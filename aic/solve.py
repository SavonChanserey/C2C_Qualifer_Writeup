#!/usr/bin/env python3
"""
Lucky Slots CTF Solver
======================
Challenge: http://challenges.1pc.tf:44963

Vulnerability:
  - Only 4 bytes (32 bits) of entropy per tick
  - sampleBytes (the seed) is EXPOSED in the API response
  - System.Random is seeded deterministically from those 4 bytes
  - => We can predict every future tick's reels and time our redeem perfectly

Strategy:
  1. Fetch /api/tick/history to get the last 30 ticks with their sampleBytes
  2. Reverse-engineer the RNG: sampleBytes -> sampleInts -> reels + jackpotPreview
  3. Brute-force or directly read the seed to predict future ticks
  4. Find a future tick where reels = jackpot combo (e.g. [7,7,7])
  5. Submit redeem at exactly the right tick
"""

import requests
import struct
import time
import json
import sys
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
BASE_URL = "http://challenges.1pc.tf:44963"
TICK_PERIOD = 2.0          # seconds between ticks (from appsettings.json)
JACKPOT_MAX = 1_000_000    # from appsettings.json
REDEEM_MAX  = 10_000_000   # from appsettings.json
SAMPLE_INT_COUNT = 16      # SampleIntCount from appsettings.json
SAMPLE_BYTE_LEN  = 4       # SampleByteLen  from appsettings.json

# Adjust these if you discover the actual symbol count / jackpot combo
NUM_SYMBOLS   = 8          # guess — reels show 0-7, so likely 8 symbols
JACKPOT_COMBO = [7, 7, 7]  # highest symbol on all 3 reels (adjust if needed)

HEADERS = {"Content-Type": "application/json"}
# ──────────────────────────────────────────────────────────────────────────────


# ── .NET System.Random reimplementation ───────────────────────────────────────
# .NET's System.Random (pre-.NET 6 legacy algorithm, which .NET 8 still uses
# when seeded with an int via new Random(seed)) uses a subtractive LCG.
# Reference: https://github.com/dotnet/runtime/blob/main/src/libraries/System.Private.CoreLib/src/System/Random.Net5CompatImpl.cs

class DotNetRandom:
    """
    Faithful reimplementation of .NET System.Random legacy algorithm.
    Used by .NET 8 when constructed as new Random(int seed).
    """
    MBIG = 2_147_483_647   # int.MaxValue
    MSEED = 161_803_398
    MZ = 0

    def __init__(self, seed: int):
        # Handle negative seeds like .NET does
        seed = seed & 0xFFFFFFFF
        if seed > 0x7FFFFFFF:
            seed = seed - 0x100000000  # convert to signed int32

        self._seed_array = [0] * 56
        subtraction = (abs(seed) if seed != -2_147_483_648 else 2_147_483_647)
        mj = (self.MSEED - subtraction) & 0x7FFFFFFF
        self._seed_array[55] = mj
        mk = 1
        for i in range(1, 55):
            ii = (21 * i) % 55
            self._seed_array[ii] = mk
            mk = (mj - mk) & 0x7FFFFFFF
            mj = self._seed_array[ii]

        for _ in range(4):
            for i in range(1, 56):
                n = i + 30
                if n >= 55:
                    n -= 55
                self._seed_array[i] = (self._seed_array[i] - self._seed_array[1 + n]) & 0x7FFFFFFF

        self._inext  = 0
        self._inextp = 21

    def _internal_sample(self) -> int:
        inext  = self._inext + 1
        inextp = self._inextp + 1
        if inext  >= 56: inext  = 1
        if inextp >= 56: inextp = 1
        ret_val = (self._seed_array[inext] - self._seed_array[inextp]) & 0x7FFFFFFF
        self._seed_array[inext] = ret_val
        self._inext  = inext
        self._inextp = inextp
        return ret_val

    def next_int(self) -> int:
        """Equivalent to .NET Random.Next() — returns [0, int.MaxValue)"""
        return self._internal_sample()

    def next_bounded(self, max_val: int) -> int:
        """Equivalent to .NET Random.Next(maxValue)"""
        return int(self._internal_sample() * (1.0 / self.MBIG) * max_val)

    def next_double(self) -> float:
        """Equivalent to .NET Random.NextDouble()"""
        return self._internal_sample() * (1.0 / self.MBIG)


# ── RNG derivation logic ───────────────────────────────────────────────────────

def bytes_to_seed(hex_str: str) -> int:
    """Convert 8-char hex sampleBytes to a signed int32 seed."""
    raw = int(hex_str, 16)
    # Interpret as little-endian int32 (common in .NET BitConverter)
    b = struct.pack(">I", raw)
    return struct.unpack("<i", b)[0]

def derive_sample_ints(seed: int, count: int = SAMPLE_INT_COUNT) -> list[int]:
    """Generate the sampleInts list from a seed."""
    rng = DotNetRandom(seed)
    return [rng.next_int() for _ in range(count)]

def sample_ints_to_reels(sample_ints: list[int], num_symbols: int = NUM_SYMBOLS) -> list[int]:
    """Map first 3 sampleInts to reel positions."""
    return [v % num_symbols for v in sample_ints[:3]]

def sample_ints_to_jackpot_preview(sample_ints: list[int]) -> int:
    """
    Guess: jackpotPreview is derived from remaining sampleInts.
    Common pattern: sum or product of ints[3:] mod JACKPOT_MAX.
    We'll try several and validate against observed values.
    """
    # Attempt 1: direct value of sampleInts[3] mod JACKPOT_MAX
    return sample_ints[3] % JACKPOT_MAX


# ── API helpers ────────────────────────────────────────────────────────────────

def api_get(path: str) -> dict | list | None:
    try:
        r = requests.get(f"{BASE_URL}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[!] GET {path} failed: {e}")
        return None

def api_post(path: str, payload: dict) -> dict | None:
    try:
        r = requests.post(f"{BASE_URL}{path}", json=payload, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[!] POST {path} failed: {e}")
        try:
            return r.json()
        except:
            return None


# ── Calibration: figure out exact RNG formula ─────────────────────────────────

def calibrate(history: list[dict]) -> tuple[int, str]:
    """
    Use tick history (which exposes sampleBytes + reels + jackpotPreview)
    to figure out the exact mapping.
    Returns (num_symbols, jackpot_formula_description).
    """
    print("\n[*] Calibrating RNG against tick history...")
    num_symbols_candidates = list(range(2, 32))
    passed = {n: 0 for n in num_symbols_candidates}
    total = 0

    for tick in history:
        sb = tick.get("sampleBytes") or tick.get("sampleBytes_hex") or tick.get("sample_bytes")
        reels = tick.get("reels")
        jp    = tick.get("jackpotPreview") or tick.get("jackpot_preview")
        if not sb or not reels:
            continue
        total += 1

        seed  = bytes_to_seed(sb)
        ints  = derive_sample_ints(seed)

        for n in num_symbols_candidates:
            predicted = [v % n for v in ints[:3]]
            if predicted == reels:
                passed[n] += 1

    if total == 0:
        print("[!] No usable history ticks found — check API field names")
        print("    History sample:", json.dumps(history[:1], indent=2) if history else "empty")
        return NUM_SYMBOLS, "unknown"

    best_n = max(passed, key=lambda k: passed[k])
    accuracy = passed[best_n] / total * 100
    print(f"    Best num_symbols = {best_n}  ({accuracy:.0f}% match over {total} ticks)")

    # Validate jackpot formula
    jp_formulas = {
        "ints[3] % JACKPOT_MAX": lambda i: i[3] % JACKPOT_MAX,
        "sum(ints) % JACKPOT_MAX": lambda i: sum(i) % JACKPOT_MAX,
        "ints[0] % JACKPOT_MAX": lambda i: i[0] % JACKPOT_MAX,
        "ints[15] % JACKPOT_MAX": lambda i: i[15] % JACKPOT_MAX,
        "(ints[0]+ints[1]+ints[2]) % JACKPOT_MAX": lambda i: (i[0]+i[1]+i[2]) % JACKPOT_MAX,
    }
    best_formula = None
    for tick in history:
        sb = tick.get("sampleBytes") or tick.get("sampleBytes_hex") or tick.get("sample_bytes")
        jp = tick.get("jackpotPreview") or tick.get("jackpot_preview")
        if not sb or jp is None:
            continue
        seed = bytes_to_seed(sb)
        ints = derive_sample_ints(seed)
        for name, fn in list(jp_formulas.items()):
            try:
                if fn(ints) != jp:
                    del jp_formulas[name]
            except:
                pass
        if len(jp_formulas) == 1:
            best_formula = list(jp_formulas.keys())[0]
            break
        if not jp_formulas:
            break

    if best_formula:
        print(f"    jackpotPreview formula: {best_formula}")
    else:
        print("    jackpotPreview formula: could not determine")

    return best_n, best_formula or "unknown"


# ── Main exploit ───────────────────────────────────────────────────────────────

def explore_api():
    """Try common API endpoint patterns to map the server's API."""
    print("\n[*] Probing API endpoints...")
    endpoints = [
        "/api/frame/current",
        "/api/tick/current",
        "/api/game/current",
        "/api/current",
        "/api/frame",
        "/api/tick",
        "/api/frame/history",
        "/api/tick/history",
        "/api/history",
        "/api/game/history",
    ]
    found = {}
    for ep in endpoints:
        try:
            r = requests.get(f"{BASE_URL}{ep}", timeout=5)
            if r.status_code == 200:
                print(f"  [+] {ep} -> HTTP 200")
                found[ep] = r.json()
            else:
                print(f"  [-] {ep} -> HTTP {r.status_code}")
        except Exception as e:
            print(f"  [!] {ep} -> {e}")
    return found


def find_jackpot_tick(num_symbols: int, look_ahead: int = 200) -> dict | None:
    """
    Fetch current frame, then scan future ticks by brute-forcing possible
    next sampleBytes values. Since sampleBytes is exposed, we actually just
    wait and poll — but we can also predict if we know seed generation pattern.
    
    Better approach: poll history repeatedly, find seed pattern, extrapolate.
    """
    print(f"\n[*] Scanning for jackpot tick (combo {JACKPOT_COMBO}, {look_ahead} ticks ahead)...")
    
    # Collect a window of history to find seed pattern
    seen_seeds = []
    print("    Collecting seed history (waiting ~10 ticks)...")
    for _ in range(10):
        frame = api_get("/api/frame/current") or api_get("/api/tick/current")
        if frame:
            sb = (frame.get("sampleBytes") or frame.get("sampleBytes_hex") or "")
            tid = frame.get("tickId", "?")
            if sb and sb not in [s for s,_ in seen_seeds]:
                seen_seeds.append((sb, tid))
                print(f"    tickId={tid}  sampleBytes={sb}")
        time.sleep(TICK_PERIOD + 0.1)

    if not seen_seeds:
        print("[!] Could not read sampleBytes from current frame — seed may not be exposed directly")
        return None

    # Try to find the seed generation pattern
    # Common: CSPRNG bytes (truly random each tick) vs counter/time-based
    seeds_int = [int(sb, 16) for sb, _ in seen_seeds]
    diffs = [seeds_int[i+1] - seeds_int[i] for i in range(len(seeds_int)-1)]
    print(f"    Seed diffs: {diffs[:5]}")

    # If diffs are constant -> linear counter (very predictable!)
    if len(set(diffs)) == 1:
        print(f"[!] SEEDS ARE LINEAR COUNTER! diff={diffs[0]} — fully predictable")
        last_seed, last_tid = int(seen_seeds[-1][0], 16), seen_seeds[-1][1]
        for i in range(1, look_ahead + 1):
            next_seed = (last_seed + diffs[0] * i) & 0xFFFFFFFF
            seed_hex  = f"{next_seed:08x}"
            signed    = bytes_to_seed(seed_hex)
            ints      = derive_sample_ints(signed)
            reels     = [v % num_symbols for v in ints[:3]]
            if reels == JACKPOT_COMBO:
                future_tid = last_tid + i
                print(f"\n[!!!] JACKPOT at future tickId={future_tid} (in {i} ticks = ~{i*TICK_PERIOD:.0f}s)")
                print(f"      sampleBytes={seed_hex}  reels={reels}")
                return {"tickId": future_tid, "sampleBytes": seed_hex, "reels": reels,
                        "ticks_away": i, "seconds_away": i * TICK_PERIOD}
    else:
        print("    Seeds appear random (CSPRNG) — brute-forcing 32-bit space...")
        # Since only 32 bits, brute force all possible seeds looking for jackpot
        jackpot_seeds = []
        for seed_int in range(0, 2**32, 1):
            signed = seed_int if seed_int <= 0x7FFFFFFF else seed_int - 0x100000000
            ints   = derive_sample_ints(signed)
            reels  = [v % num_symbols for v in ints[:3]]
            if reels == JACKPOT_COMBO:
                jackpot_seeds.append(f"{seed_int:08x}")
            if seed_int % 50_000_000 == 0:
                print(f"    Progress: {seed_int/2**32*100:.1f}%  found {len(jackpot_seeds)} jackpot seeds so far")
        print(f"\n[+] Found {len(jackpot_seeds)} seeds that produce jackpot reels")
        print(f"    Jackpot seeds (first 10): {jackpot_seeds[:10]}")
        print("    Now polling until one of these seeds appears...")
        return {"jackpot_seeds": jackpot_seeds, "num_symbols": num_symbols}


def wait_and_redeem(jackpot_info: dict, amount: int = REDEEM_MAX):
    """Wait for the jackpot tick and submit a redeem."""
    if "ticks_away" in jackpot_info:
        # Linear predictor path
        wait_secs = jackpot_info["seconds_away"] - TICK_PERIOD  # arrive 1 tick early
        target_tid = jackpot_info["tickId"]
        print(f"\n[*] Waiting {wait_secs:.1f}s for tickId={target_tid}...")
        if wait_secs > 0:
            time.sleep(wait_secs)

        # Poll until we hit the target tick
        print("[*] Polling for target tick...")
        for _ in range(20):
            frame = api_get("/api/frame/current") or api_get("/api/tick/current")
            if frame and frame.get("tickId") == target_tid:
                print(f"[+] Target tick reached! Submitting redeem for {amount}...")
                result = api_post("/api/redeem", {"amount": amount, "tickId": target_tid})
                print(f"[+] Redeem response: {json.dumps(result, indent=2)}")
                return result
            time.sleep(0.3)

    elif "jackpot_seeds" in jackpot_info:
        # CSPRNG path — poll until a jackpot seed appears
        jackpot_set = set(jackpot_info["jackpot_seeds"])
        ns = jackpot_info["num_symbols"]
        print(f"\n[*] Polling for a jackpot seed ({len(jackpot_set)} candidates)...")
        while True:
            frame = api_get("/api/frame/current") or api_get("/api/tick/current")
            if frame:
                sb  = frame.get("sampleBytes") or frame.get("sampleBytes_hex") or ""
                tid = frame.get("tickId")
                if sb.lower() in jackpot_set:
                    print(f"[!!!] JACKPOT SEED DETECTED! tickId={tid} sampleBytes={sb}")
                    result = api_post("/api/redeem", {"amount": amount, "tickId": tid})
                    print(f"[+] Redeem response: {json.dumps(result, indent=2)}")
                    return result
            time.sleep(TICK_PERIOD * 0.8)  # poll slightly faster than tick rate


def main():
    print("=" * 60)
    print("  Lucky Slots CTF Solver")
    print("=" * 60)

    # Step 1: Map the API
    found_endpoints = explore_api()
    if not found_endpoints:
        print("[!] Could not reach any API endpoints. Check BASE_URL.")
        sys.exit(1)

    # Step 2: Get current frame — inspect all fields
    frame = None
    for ep in ["/api/frame/current", "/api/tick/current", "/api/current"]:
        frame = api_get(ep)
        if frame:
            print(f"\n[+] Current frame from {ep}:")
            print(json.dumps(frame, indent=2))
            break

    # Step 3: Get history
    history = []
    for ep in ["/api/frame/history", "/api/tick/history", "/api/history"]:
        h = api_get(ep)
        if h:
            history = h if isinstance(h, list) else h.get("history", h.get("ticks", h.get("frames", [])))
            if history:
                print(f"\n[+] Got {len(history)} history ticks from {ep}")
                print("    Sample tick fields:", list(history[0].keys()) if history else "none")
                break

    # Step 4: Calibrate RNG
    num_symbols = NUM_SYMBOLS
    if history:
        num_symbols, formula = calibrate(history)
    else:
        print("[!] No history available — using default NUM_SYMBOLS =", NUM_SYMBOLS)

    # Step 5: Find jackpot tick and redeem
    jackpot_info = find_jackpot_tick(num_symbols)
    if jackpot_info:
        wait_and_redeem(jackpot_info)
    else:
        print("\n[!] Could not determine jackpot strategy.")
        print("    Try decompiling project.dll with: ilspycmd project.dll -o ./decompiled/")
        print("    Then update bytes_to_seed() and sample_ints_to_reels() accordingly.")


# ── Standalone RNG test ────────────────────────────────────────────────────────

def test_rng():
    """Quick sanity check: verify our DotNetRandom matches known .NET output."""
    # Known values from .NET: new Random(42).Next() sequence
    rng = DotNetRandom(42)
    got = [rng.next_int() for _ in range(5)]
    print("RNG test (seed=42):", got)
    # Expected .NET sequence for seed=42:
    # 1434747710, 302596119, 269548474, ...
    # (run a .NET snippet to get ground truth and compare)

    # Also test with the observed sampleBytes from screenshot
    # sampleBytes would be in the API response; from screenshot we see reels=[0,0,7]
    # If we knew sampleBytes we could verify here


if __name__ == "__main__":
    if "--test-rng" in sys.argv:
        test_rng()
    else:
        main()
