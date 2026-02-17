#!/bin/bash
#
# Lucky Slots - Improved Automated Solver
# More robust with better error handling and wider search
#

URL="${1:-challenges.1pc.tf:49418}"

echo "======================================================================"
echo "LUCKY SLOTS - SIMPLE AUTOMATED SOLVER"
echo "======================================================================"
echo ""
echo "Target: $URL"
echo "Cores: $(nproc)"
echo ""

# Create optimized Python solver
cat > /tmp/simple_solver.py << 'ENDPYTHON'
#!/usr/bin/env python3
import requests
import time
import sys
from multiprocessing import Pool, cpu_count

class DotNetRandom:
    MBIG = 2147483647
    def __init__(self, seed: int):
        seed = seed & 0xFFFFFFFF
        if seed >= 2**31:
            seed -= 2**32
        MSEED = 161803398
        subtraction = (MSEED - abs(seed)) % self.MBIG
        self._seed_array = [0] * 56
        self._seed_array[55] = subtraction
        mk = 1
        for i in range(1, 55):
            ii = (21 * i) % 55
            self._seed_array[ii] = mk
            mk = (subtraction - mk) % self.MBIG
            subtraction = self._seed_array[ii]
        for _ in range(4):
            for i in range(1, 56):
                self._seed_array[i] = (self._seed_array[i] - self._seed_array[1 + (i + 30) % 55]) % self.MBIG
        self._inext = 0
        self._inextp = 21
    
    def internal_sample(self):
        self._inext = (self._inext + 1) % 56
        if self._inext == 0: self._inext = 1
        self._inextp = (self._inextp + 1) % 56
        if self._inextp == 0: self._inextp = 1
        retval = (self._seed_array[self._inext] - self._seed_array[self._inextp]) % self.MBIG
        self._seed_array[self._inext] = retval
        return retval
    
    def next_int(self, min_val=0, max_val=None):
        if max_val is None: max_val = self.MBIG
        range_size = max_val - min_val
        sample = self.internal_sample()
        return int(sample * (1.0 / self.MBIG) * range_size) + min_val
    
    def next_bytes(self, buffer):
        for i in range(len(buffer)):
            buffer[i] = self.internal_sample() % 256

def gen_tick(rng):
    reels = [rng.next_int(0, 10) for _ in range(3)]
    jackpot = rng.next_int(0, 1000000)
    samples = [rng.next_int(0, 2147483647) for _ in range(16)]
    buf = bytearray(4)
    rng.next_bytes(buf)
    redeem = rng.next_int(0, 10000000)
    return {'reels': reels, 'jackpot': jackpot, 'samples': samples, 'redeem': redeem}

def check(args):
    seed, frames = args
    try:
        rng = DotNetRandom(seed)
        buf = bytearray(64)
        rng.next_bytes(buf)
        rng.next_int(0, 1000000)
        rng.next_int(0, 2147483647)
        for offset in range(min(8, len(frames) + 3)):
            test = DotNetRandom(seed)
            b = bytearray(64)
            test.next_bytes(b)
            test.next_int(0, 1000000)
            test.next_int(0, 2147483647)
            for _ in range(offset): gen_tick(test)
            g = gen_tick(test)
            if g['reels'] == frames[0]['reels'] and g['jackpot'] == frames[0]['jackpotPreview']:
                if g['samples'][:4] == frames[0]['sampleInts'][:4]:
                    if len(frames) > 1:
                        g2 = gen_tick(test)
                        if g2['reels'] == frames[1]['reels']:
                            return (seed, offset)
                    else:
                        return (seed, offset)
    except: pass
    return None

def fetch(url, base_url):
    try:
        return requests.get(url, timeout=10), base_url
    except requests.exceptions.SSLError:
        http_url = url.replace('https://', 'http://')
        return requests.get(http_url, timeout=10), base_url.replace('https://', 'http://')

def search(base_url, start, end):
    print(f"Fetching frames from {base_url}...")
    resp, base_url = fetch(f"{base_url}/api/recent/10", base_url)
    frames = resp.json()
    print(f"Got {len(frames)} frames")
    print(f"Searching {start:,} to {end:,} with {cpu_count()} cores...")
    
    args = [(s, frames) for s in range(start, end)]
    with Pool(cpu_count()) as pool:
        for i, res in enumerate(pool.imap_unordered(check, args, chunksize=5000)):
            if res:
                print(f"\nFOUND! Seed={res[0]}, Offset={res[1]}")
                pool.terminate()
                return res, base_url, frames
            if (i+1) % 50000 == 0:
                print(f"  {i+1:,}/{len(args):,} ({(i+1)/len(args)*100:.1f}%)", flush=True)
    return None, base_url, frames

def exploit(base_url, seed, offset):
    print(f"\nPredicting with seed {seed}...")
    resp, base_url = fetch(f"{base_url}/api/frame", base_url)
    cur = resp.json()
    tick = cur['tickId']
    print(f"Current tick: {tick}")
    
    rng = DotNetRandom(seed)
    buf = bytearray(64)
    rng.next_bytes(buf)
    rng.next_int(0, 1000000)
    rng.next_int(0, 2147483647)
    
    for _ in range(tick): gen_tick(rng)
    next_t = gen_tick(rng)
    
    print(f"Next tick {tick+1} redeem: {next_t['redeem']}")
    print("Waiting for tick...")
    time.sleep(2.5)
    
    print("Submitting...")
    try:
        resp = requests.post(f"{base_url}/api/redeem", 
                           json={"tickId": tick+1, "code": next_t['redeem']}, timeout=10)
    except requests.exceptions.SSLError:
        base_url = base_url.replace('https://', 'http://')
        resp = requests.post(f"{base_url}/api/redeem",
                           json={"tickId": tick+1, "code": next_t['redeem']}, timeout=10)
    
    result = resp.json()
    print("\n" + "="*70)
    if result.get('success'):
        print("🎉 SUCCESS! 🎉")
        print("="*70)
        print(f"\nFLAG: {result['flag']}\n")
        return True
    else:
        print(f"FAILED: {result.get('message')}")
        return False

if __name__ == "__main__":
    base_url = sys.argv[1]
    start = int(sys.argv[2])
    end = int(sys.argv[3])
    
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'https://' + base_url
    
    result, base_url, frames = search(base_url, start, end)
    
    if result:
        seed, offset = result
        exploit(base_url, seed, offset)
    else:
        print(f"\nNot found in range {start:,} to {end:,}")
        sys.exit(1)
ENDPYTHON

chmod +x /tmp/simple_solver.py

# Try different ranges sequentially
RANGES=(
    "0 50000000"              # 0-50M
    "50000000 150000000"      # 50M-150M
    "-50000000 0"             # -50M to 0
    "150000000 500000000"     # 150M-500M
    "-150000000 -50000000"    # -150M to -50M
    "500000000 1000000000"    # 500M-1B
    "-500000000 -150000000"   # -500M to -150M
    "1000000000 2147483647"   # 1B to max
    "-2147483648 -500000000"  # min to -500M
)

echo "Will search the following ranges in order:"
for i in "${!RANGES[@]}"; do
    echo "  $((i+1)). ${RANGES[$i]}"
done
echo ""

for RANGE in "${RANGES[@]}"; do
    START=$(echo $RANGE | cut -d' ' -f1)
    END=$(echo $RANGE | cut -d' ' -f2)
    
    echo "======================================================================"
    echo "Searching range: $START to $END"
    echo "======================================================================"
    
    python3 /tmp/simple_solver.py "$URL" "$START" "$END"
    
    if [ $? -eq 0 ]; then
        # Success!
        exit 0
    fi
    
    echo ""
    echo "Range completed. Moving to next range..."
    echo ""
done

echo ""
echo "All ranges searched without finding seed."
echo "The seed might be in an unusual range or there may be an issue."
