#!/usr/bin/env python3
"""
Lucky Slots - SUPER OPTIMIZED Parallel Exploit
Checks common CTF seed patterns first, then does full search
"""

import requests
import time
import sys
from multiprocessing import Pool, cpu_count
from typing import List


class DotNetRandom:
    """Minimal .NET Random"""
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
                self._seed_array[i] = (self._seed_array[i] - 
                                      self._seed_array[1 + (i + 30) % 55]) % self.MBIG
        
        self._inext = 0
        self._inextp = 21
    
    def internal_sample(self) -> int:
        self._inext = (self._inext + 1) % 56
        if self._inext == 0:
            self._inext = 1
        self._inextp = (self._inextp + 1) % 56
        if self._inextp == 0:
            self._inextp = 1
        
        retval = (self._seed_array[self._inext] - self._seed_array[self._inextp]) % self.MBIG
        self._seed_array[self._inext] = retval
        return retval
    
    def next_int(self, min_val: int = 0, max_val: int = None) -> int:
        if max_val is None:
            max_val = self.MBIG
        range_size = max_val - min_val
        sample = self.internal_sample()
        return int(sample * (1.0 / self.MBIG) * range_size) + min_val
    
    def next_bytes(self, buffer: bytearray):
        for i in range(len(buffer)):
            buffer[i] = self.internal_sample() % 256


def generate_tick(rng: DotNetRandom) -> dict:
    """Generate one tick"""
    reels = [rng.next_int(0, 10) for _ in range(3)]
    jackpot = rng.next_int(0, 1000000)
    samples = [rng.next_int(0, 2147483647) for _ in range(16)]
    buf = bytearray(4)
    rng.next_bytes(buf)
    redeem = rng.next_int(0, 10000000)
    
    return {
        'reels': reels,
        'jackpot': jackpot,
        'samples': samples,
        'redeem': redeem
    }


def check_seed_fast(seed: int, frames: List[dict], max_offset: int = 10) -> tuple:
    """Fast single seed check"""
    try:
        rng = DotNetRandom(seed)
        
        # Warmup
        buf = bytearray(64)
        rng.next_bytes(buf)
        rng.next_int(0, 1000000)
        rng.next_int(0, 2147483647)
        
        # Try different offsets
        for offset in range(max_offset):
            test_rng = DotNetRandom(seed)
            buf2 = bytearray(64)
            test_rng.next_bytes(buf2)
            test_rng.next_int(0, 1000000)
            test_rng.next_int(0, 2147483647)
            
            for _ in range(offset):
                generate_tick(test_rng)
            
            # Check match
            gen = generate_tick(test_rng)
            
            if (gen['reels'] == frames[0]['reels'] and
                gen['jackpot'] == frames[0]['jackpotPreview']):
                
                if gen['samples'][:4] == frames[0]['sampleInts'][:4]:
                    if len(frames) > 1:
                        gen2 = generate_tick(test_rng)
                        if gen2['reels'] == frames[1]['reels']:
                            return (seed, offset)
                    else:
                        return (seed, offset)
    except:
        pass
    
    return None


def check_seed_wrapper(args):
    """Wrapper for multiprocessing"""
    seed, frames = args
    return check_seed_fast(seed, frames)


def quick_pattern_check(frames: List[dict]) -> tuple:
    """Check common CTF seed patterns first"""
    print("[*] Quick checking common CTF patterns...")
    
    # Common patterns in CTFs
    patterns = []
    
    # Small numbers
    patterns.extend(range(0, 10000))
    patterns.extend(range(-1000, 0))
    
    # Powers of 2
    patterns.extend([2**i for i in range(32)])
    patterns.extend([-(2**i) for i in range(32)])
    
    # Round numbers
    for i in range(1, 1000):
        patterns.extend([i * 1000, i * 10000, i * 100000, i * 1000000])
        patterns.extend([-(i * 1000), -(i * 10000), -(i * 100000), -(i * 1000000)])
    
    # Common "random looking" seeds
    patterns.extend([12345, 123456, 1234567, 12345678, 123456789])
    patterns.extend([42, 420, 1337, 31337, 0xDEADBEEF, 0xCAFEBABE])
    
    # Remove duplicates
    patterns = list(set(patterns))
    
    print(f"    Checking {len(patterns)} pattern seeds...")
    
    for i, seed in enumerate(patterns):
        if i % 10000 == 0 and i > 0:
            print(f"    Checked {i}/{len(patterns)}...", end='\r')
        
        result = check_seed_fast(seed, frames)
        if result:
            print(f"\n[+] FOUND in patterns! Seed={result[0]}, Offset={result[1]}")
            return result
    
    print(f"    Checked all {len(patterns)} patterns - not found")
    return None


def parallel_search_chunked(frames: List[dict], start: int, end: int, chunk_size: int = 1_000_000):
    """Search in chunks with better progress reporting"""
    num_workers = cpu_count()
    
    for chunk_start in range(start, end, chunk_size):
        chunk_end = min(chunk_start + chunk_size, end)
        
        print(f"\n[*] Chunk: {chunk_start:,} to {chunk_end:,}")
        print(f"    ({num_workers} cores, ~{(chunk_end-chunk_start)/num_workers/60000:.1f} min)")
        
        args_list = [(seed, frames) for seed in range(chunk_start, chunk_end)]
        
        with Pool(num_workers) as pool:
            for i, result in enumerate(pool.imap_unordered(check_seed_wrapper, args_list, chunksize=10000)):
                if result:
                    print(f"\n[+] FOUND! Seed={result[0]}, Offset={result[1]}")
                    pool.terminate()
                    return result
                
                if (i + 1) % 50000 == 0:
                    progress = (i + 1) / len(args_list) * 100
                    seeds_per_sec = 50000 / 0.5  # Rough estimate
                    print(f"    {i+1:,}/{len(args_list):,} ({progress:.1f}%) - ~{seeds_per_sec:,.0f} seeds/sec", end='\r')
    
    return None


def smart_fetch(url: str, timeout: int = 10):
    """Fetch with auto HTTP/HTTPS detection"""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp, url.rsplit('/', 1)[0]
    except requests.exceptions.SSLError:
        http_url = url.replace('https://', 'http://')
        resp = requests.get(http_url, timeout=timeout)
        resp.raise_for_status()
        return resp, http_url.rsplit('/', 1)[0]


def exploit(base_url: str):
    """Main exploit"""
    print("="*70)
    print(f"SUPER OPTIMIZED PARALLEL SEARCH ({cpu_count()} cores)")
    print("="*70)
    
    # Fetch data
    print("\n[1] Fetching frames...")
    resp, actual_base = smart_fetch(f"{base_url}/api/recent/15")
    frames = resp.json()
    base_url = actual_base
    
    print(f"[+] Connected: {base_url}")
    print(f"[+] Frames: {len(frames)} (ticks {frames[0]['tickId']}-{frames[-1]['tickId']})")
    print(f"[+] First frame reels: {frames[0]['reels']}, jackpot: {frames[0]['jackpotPreview']}")
    
    # Quick pattern check first
    print("\n[2] Quick pattern search...")
    result = quick_pattern_check(frames)
    
    if not result:
        # Full search with optimized ranges
        print("\n[3] Full parallel search (prioritized ranges)...")
        
        ranges = [
            (10_000_000, 100_000_000, "10M-100M"),
            (100_000_000, 500_000_000, "100M-500M"),
            (-100_000_000, -10_000_000, "-100M to -10M"),
            (500_000_000, 1_000_000_000, "500M-1B"),
            (-500_000_000, -100_000_000, "-500M to -100M"),
        ]
        
        for start, end, desc in ranges:
            print(f"\n[*] Range: {desc}")
            result = parallel_search_chunked(frames, start, end)
            if result:
                break
    
    if not result:
        print("\n[!] Seed not found in search space")
        return False
    
    seed, offset = result
    print(f"\n[+] RECOVERED SEED: {seed}")
    
    # Predict and submit
    print("\n[4] Predicting next tick...")
    resp, _ = smart_fetch(f"{base_url}/api/frame")
    current = resp.json()
    tick = current['tickId']
    
    rng = DotNetRandom(seed)
    buf = bytearray(64)
    rng.next_bytes(buf)
    rng.next_int(0, 1000000)
    rng.next_int(0, 2147483647)
    
    for _ in range(tick):
        generate_tick(rng)
    
    next_pred = generate_tick(rng)
    
    print(f"[+] Tick {tick + 1} prediction: redeem={next_pred['redeem']}")
    
    print("\n[5] Waiting and submitting...")
    time.sleep(2.5)
    
    try:
        resp = requests.post(f"{base_url}/api/redeem",
                           json={"tickId": tick + 1, "code": next_pred['redeem']},
                           timeout=10)
    except requests.exceptions.SSLError:
        resp = requests.post(f"{base_url.replace('https://', 'http://')}/api/redeem",
                           json={"tickId": tick + 1, "code": next_pred['redeem']},
                           timeout=10)
    
    result = resp.json()
    
    print("\n" + "="*70)
    if result.get('success'):
        print("🎉 SUCCESS! 🎉")
        print("="*70)
        print(f"\nFLAG: {result['flag']}\n")
    else:
        print(f"❌ FAILED: {result.get('message')}")
    
    return result.get('success', False)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python3 super_fast.py <url>")
        print(f"Example: python3 super_fast.py challenges.1pc.tf:49418")
        sys.exit(1)
    
    url = sys.argv[1].rstrip('/')
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        exploit(url)
    except KeyboardInterrupt:
        print("\n[!] Interrupted")
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()
