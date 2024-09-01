import json
import os
import time
import random
from web3 import Web3
from eth_account import Account
from colorama import Fore, Style, init

init(autoreset=True)

CONFIG_FILE = 'config.json'
PRIVATE_KEYS_FILE = 'private_keys.txt'

HEADER = f"""
{Fore.GREEN}Coded By Onixia{Style.RESET_ALL}
"""

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_header():
    clear_screen()
    print(HEADER)
    print(Fore.GREEN + "=" * 70 + Style.RESET_ALL + "\n")

def ensure_file_exists(filename, content=''):
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            f.write(content)

def save_config(rpc_url, chain_id, block_explorer):
    config = {'rpc_url': rpc_url, 'chain_id': chain_id, 'block_explorer': block_explorer}
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None

def save_private_keys(private_keys):
    with open(PRIVATE_KEYS_FILE, 'w') as f:
        for key in private_keys:
            f.write(key + '\n')

def load_private_keys():
    if os.path.exists(PRIVATE_KEYS_FILE):
        with open(PRIVATE_KEYS_FILE, 'r') as f:
            return [line.strip() for line in f.readlines()]
    return []

def get_user_input():
    rpc_url = input(Fore.CYAN + "Enter the RPC URL: " + Style.RESET_ALL)
    chain_id = int(input(Fore.CYAN + "Enter the Chain ID: " + Style.RESET_ALL))
    block_explorer = input(Fore.CYAN + "Enter the Block Explorer URL (e.g., https://etherscan.io/tx/): " + Style.RESET_ALL)
    return rpc_url, chain_id, block_explorer

def get_gas_settings(w3):
    gas_price = w3.eth.gas_price
    gas_price_gwei = w3.from_wei(gas_price, 'gwei')
    gas_limit = 21000

    print(f"\n{Fore.YELLOW}Current gas settings:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Gas Price: {gas_price_gwei:.2f} Gwei{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Gas Limit: {gas_limit}{Style.RESET_ALL}")
    confirm = input(Fore.CYAN + "\nDo you want to use these gas settings? (y/n): " + Style.RESET_ALL).lower()
    if confirm != 'y':
        gas_price_gwei = float(input(Fore.CYAN + "Enter new Gas Price (in Gwei): " + Style.RESET_ALL))
        gas_price = w3.to_wei(gas_price_gwei, 'gwei')
        gas_limit = int(input(Fore.CYAN + "Enter new Gas Limit: " + Style.RESET_ALL))

    return gas_price, gas_limit

def send_transaction(w3, from_account, to_address, amount, nonce, chain_id, gas_price, gas_limit):
    transaction = {
        'nonce': nonce,
        'to': to_address,
        'value': w3.to_wei(amount, 'ether'),
        'gas': gas_limit,
        'gasPrice': gas_price,
        'chainId': chain_id,
    }
    
    signed_txn = w3.eth.account.sign_transaction(transaction, from_account.key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return tx_hash

def process_transactions(w3, from_account, num_transactions, amount_range, chain_id, delay_range, block_explorer, gas_price, gas_limit):
    nonce = w3.eth.get_transaction_count(from_account.address)
    
    initial_balance = w3.eth.get_balance(from_account.address)
    print(f"\n{Fore.YELLOW}Initial account balance: {w3.from_wei(initial_balance, 'ether')} ETH{Style.RESET_ALL}")
    
    for i in range(1, num_transactions + 1):
        try:
            current_balance = w3.eth.get_balance(from_account.address)
            print(f"\n{Fore.YELLOW}Current account balance before transaction {i}: {w3.from_wei(current_balance, 'ether')} ETH{Style.RESET_ALL}")
            
            new_wallet = Account.create()
            to_address = new_wallet.address
            
            amount = random.uniform(*amount_range)
            delay = random.uniform(*delay_range) * 60
            
            tx_hash = send_transaction(w3, from_account, to_address, amount, nonce, chain_id, gas_price, gas_limit)
            print(f"{Fore.GREEN}Transaction {i} sent:{Style.RESET_ALL}")
            print(f"  {Fore.CYAN}To:{Style.RESET_ALL} {to_address}")
            print(f"  {Fore.CYAN}Amount:{Style.RESET_ALL} {amount:.6f} ETH")
            print(f"  {Fore.CYAN}Transaction Hash:{Style.RESET_ALL} {tx_hash.hex()}")
            if block_explorer:
                print(f"  {Fore.CYAN}Block Explorer Link:{Style.RESET_ALL} {block_explorer}{tx_hash.hex()}")
            print(Fore.GREEN + "-" * 50 + Style.RESET_ALL)
            nonce += 1
            time.sleep(delay)
        except Exception as e:
            print(f"{Fore.RED}Transaction {i} failed:{Style.RESET_ALL}")
            print(f"  {Fore.CYAN}To:{Style.RESET_ALL} {to_address}")
            print(f"  {Fore.CYAN}Error:{Style.RESET_ALL} {str(e)}")
            print(Fore.RED + "-" * 50 + Style.RESET_ALL)

def get_config():
    config = load_config()
    if config:
        use_previous = input(Fore.CYAN + "Do you want to use the previous configuration? (y/n): " + Style.RESET_ALL).lower()
        if use_previous == 'y':
            return config['rpc_url'], config['chain_id'], config['block_explorer']
    
    return get_user_input()

def main():
    display_header()
    
    ensure_file_exists(CONFIG_FILE)
    ensure_file_exists(PRIVATE_KEYS_FILE)
    
    rpc_url, chain_id, block_explorer = get_config()
    save_config(rpc_url, chain_id, block_explorer)

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print(Fore.RED + "Failed to connect to the network. Please check your RPC URL." + Style.RESET_ALL)
        return

    print(f"{Fore.GREEN}Connected to network: {w3.is_connected()}{Style.RESET_ALL}")

    network_chain_id = w3.eth.chain_id
    if network_chain_id != chain_id:
        print(Fore.YELLOW + f"Warning: The provided Chain ID ({chain_id}) does not match the network's Chain ID ({network_chain_id})." + Style.RESET_ALL)
        continue_anyway = input(Fore.CYAN + "Do you want to continue anyway? (y/n): " + Style.RESET_ALL).lower()
        if continue_anyway != 'y':
            return

    private_keys = load_private_keys()

    tx_per_key = int(input(Fore.CYAN + "How many transactions per private key? " + Style.RESET_ALL))

    min_amount = float(input(Fore.CYAN + "Enter minimum amount of ETH to send (inclusive): " + Style.RESET_ALL))
    max_amount = float(input(Fore.CYAN + "Enter maximum amount of ETH to send (inclusive): " + Style.RESET_ALL))
    amount_range = (min_amount, max_amount)

    min_delay = float(input(Fore.CYAN + "Enter minimum delay between transactions in minutes (inclusive): " + Style.RESET_ALL))
    max_delay = float(input(Fore.CYAN + "Enter maximum delay between transactions in minutes (inclusive): " + Style.RESET_ALL))
    delay_range = (min_delay, max_delay)

    display_header()

    try:
        for private_key in private_keys:
            from_account = Account.from_key(private_key)
            gas_price, gas_limit = get_gas_settings(w3)

            print(f"\n{Fore.YELLOW}Processing transactions for wallet: {from_account.address}{Style.RESET_ALL}")
            
            process_transactions(w3, from_account, tx_per_key, amount_range, chain_id, delay_range, block_explorer, gas_price, gas_limit)
            
            print(f"\n{Fore.GREEN}Transactions for wallet {from_account.address} completed.{Style.RESET_ALL}")
            print(Fore.GREEN + "=" * 70 + Style.RESET_ALL)

    except Exception as e:
        print(Fore.RED + f"An error occurred: {e}" + Style.RESET_ALL)

if __name__ == "__main__":
    main()
