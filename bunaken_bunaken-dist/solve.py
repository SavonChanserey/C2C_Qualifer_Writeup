import base64
import hashlib
import subprocess
import re
import sys
import os

def derive_aes_key(password):
    """
    Derive AES-128 key from password using SHA-256.
    Takes first 16 bytes of SHA-256 hash.
    """
    key_hash = hashlib.sha256(password.encode()).digest()
    return key_hash[:16]

def decrypt_flag(encrypted_base64, password):
    """
    Decrypt the flag using AES-128-CBC via OpenSSL.
    
    Format of encrypted data:
    - First 16 bytes: IV (initialization vector)
    - Remaining bytes: Ciphertext
    """
    print("[+] Decrypting flag...")
    
    # Base64 decode
    encrypted_data = base64.b64decode(encrypted_base64)
    print(f"[+] Encrypted data length: {len(encrypted_data)} bytes")
    
    # Extract IV and ciphertext
    iv = encrypted_data[:16]
    ciphertext = encrypted_data[16:]
    
    print(f"[+] IV: {iv.hex()}")
    print(f"[+] Ciphertext length: {len(ciphertext)} bytes")
    
    # Derive AES key
    aes_key = derive_aes_key(password)
    print(f"[+] AES key (from SHA-256): {aes_key.hex()}")
    
    # Decrypt using OpenSSL
    result = subprocess.run(
        ['openssl', 'enc', '-aes-128-cbc', '-d', '-K', aes_key.hex(), '-iv', iv.hex()],
        input=ciphertext,
        capture_output=True
    )
    
    if result.returncode != 0:
        print(f"[-] OpenSSL decryption failed: {result.stderr.decode()}")
        return None
    
    decrypted = result.stdout
    print(f"[+] Decrypted length: {len(decrypted)} bytes")
    print(f"[+] First bytes: {decrypted[:20].hex()}")
    
    # Check for zstd magic number
    if decrypted[:4] == b'\x28\xb5\x2f\xfd':
        print("[+] Data is zstd compressed")
        
        # Flag is visible in ASCII even without full decompression
        text = decrypted.decode('ascii', errors='ignore')
        match = re.search(r'C2C\{[^}]+\}', text)
        if match:
            return match.group(0)
        return None
    else:
        # Try as plaintext
        return decrypted.decode('utf-8', errors='ignore')

def main():
    print("=" * 70)
    print("Bunaken CTF Challenge Solution")
    print("=" * 70)
    
    # The encrypted flag (base64)
    encrypted_flag = "3o2Gh52pjRk80IPViTp8KUly+kDGXo7qAlPo2Ff1+IOWW1ziNAoboyBZPX6R4JvNXZ4iWwc662Nv/rMPLdwrIb3D4tTbOg/vi0NKaPfToj0="
    
    # The encryption key (found through deobfuscation)
    password = "sulawesi"
    
    print(f"\n[+] Encryption key: {password}")
    print(f"[+] Encrypted flag (base64): {encrypted_flag[:50]}...")
    print()
    
    try:
        flag = decrypt_flag(encrypted_flag, password)
        
        if flag and 'C2C{' in flag:
            print("\n" + "=" * 70)
            print("🎉 FLAG FOUND!")
            print("=" * 70)
            print(f"\n  {flag}\n")
            return 0
        else:
            print("\n[-] Could not extract flag")
            if flag:
                print(f"[i] Decrypted content: {flag}")
            return 1
            
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

