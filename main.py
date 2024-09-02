import json
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor
from web3 import Web3
from eth_account import Account
from colorama import Fore, Style, init

# Initialize colorama
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

def save_config(rpc_url, chain_id, block_explorer):
    config = {'rpc_url': rpc_url, 'chain_id': chain_id, 'block_explorer': block_explorer}
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(Fore.RED + "Error reading JSON file. The file may be corrupted or empty." + Style.RESET_ALL)
    return None

def save_private_keys(private_keys):
    with open(PRIVATE_KEYS_FILE, 'w') as f:
        for key in private_keys:
            f.write(key + '\n')

def get_user_input():
    rpc_url = input(Fore.CYAN + "Enter the RPC URL: " + Style.RESET_ALL)
    chain_id = int(input(Fore.CYAN + "Enter the Chain ID: " + Style.RESET_ALL))
    block_explorer = input(Fore.CYAN + "Enter the Block Explorer URL (e.g., https://etherscan.io/tx/): " + Style.RESET_ALL)
    return rpc_url, chain_id, block_explorer

def get_gas_settings(w3):
    gas_price = w3.eth.gas_price
    gas_price_gwei = w3.from_wei(gas_price, 'gwei')
    gas_limit = 21000  # Standard gas limit for ETH transfers

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
    tx = {
        'nonce': nonce,
        'to': to_address,
        'value': w3.to_wei(amount, 'ether'),
        'gas': gas_limit,
        'gasPrice': gas_price,
        'chainId': chain_id
    }
    signed_tx = from_account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash

def send_transactions(w3, from_account, to_addresses, amount_range, chain_id, delay_range, block_explorer, gas_price, gas_limit):
    nonce = w3.eth.get_transaction_count(from_account.address)
    for i, to_address in enumerate(to_addresses, 1):
        try:
            # Generate random amount and delay
            amount = random.uniform(*amount_range)
            delay = random.uniform(*delay_range) * 60  # Convert minutes to seconds
            
            tx_hash = send_transaction(w3, from_account, to_address, amount, nonce, chain_id, gas_price, gas_limit)
            print(f"{Fore.GREEN}Transaction {i} sent:{Style.RESET_ALL}")
            print(f"  {Fore.CYAN}To:{Style.RESET_ALL} {to_address}")
            print(f"  {Fore.CYAN}Amount:{Style.RESET_ALL} {amount:.6f} ETH")
            print(f"  {Fore.CYAN}Transaction Hash:{Style.RESET_ALL} {tx_hash.hex()}")
            if block_explorer:
                print(f"  {Fore.CYAN}Block Explorer Link:{Style.RESET_ALL} {block_explorer}{tx_hash.hex()}")
            print(Fore.GREEN + "-" * 20 + Style.RESET_ALL)
            nonce += 1
            time.sleep(delay)  # delay is now in seconds
        except Exception as e:
            print(f"{Fore.RED}Transaction {i} failed:{Style.RESET_ALL}")
            print(f"  {Fore.CYAN}To:{Style.RESET_ALL} {to_address}")
            print(f"  {Fore.CYAN}Error:{Style.RESET_ALL} {str(e)}")
            print(Fore.RED + "-" * 20 + Style.RESET_ALL)

def get_config():
    config = load_config()
    if config:
        use_previous = input(Fore.CYAN + "Do you want to use the previous configuration? (y/n): " + Style.RESET_ALL).lower()
        if use_previous == 'y':
            return config['rpc_url'], config['chain_id'], config['block_explorer']
        else:
            return get_user_input()
    else:
        return get_user_input()

def main():
    display_header()
    
    rpc_url, chain_id, block_explorer = get_config()

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print(Fore.RED + "Failed to connect to the network. Please check your RPC URL." + Style.RESET_ALL)
        return

    network_chain_id = w3.eth.chain_id
    if network_chain_id != chain_id:
        print(Fore.YELLOW + f"Warning: The provided Chain ID ({chain_id}) does not match the network's Chain ID ({network_chain_id})." + Style.RESET_ALL)
        continue_anyway = input(Fore.CYAN + "Do you want to continue anyway? (y/n): " + Style.RESET_ALL).lower()
        if continue_anyway != 'y':
            return

    # Ask user for number of private keys
    num_keys = int(input(Fore.CYAN + "How many private keys do you want to add? " + Style.RESET_ALL))
    private_keys = [input(f"{Fore.CYAN}Enter private key {i + 1}: " + Style.RESET_ALL) for i in range(num_keys)]

    # Save private keys to a file
    save_private_keys(private_keys)

    # Ask user for the number of transactions per private key
    tx_per_key = int(input(Fore.CYAN + "How many transactions per private key? " + Style.RESET_ALL))

    # Ask user for the number of wallets to generate per private key
    num_wallets_per_key = int(input(Fore.CYAN + "How many new wallets to generate per private key? " + Style.RESET_ALL))

    # Ask user for the amount range and delay range
    min_amount = float(input(Fore.CYAN + "Enter minimum amount of ETH to send (inclusive): " + Style.RESET_ALL))
    max_amount = float(input(Fore.CYAN + "Enter maximum amount of ETH to send (inclusive): " + Style.RESET_ALL))
    amount_range = (min_amount, max_amount)

    min_delay = float(input(Fore.CYAN + "Enter minimum delay between transactions in minutes (inclusive): " + Style.RESET_ALL))
    max_delay = float(input(Fore.CYAN + "Enter maximum delay between transactions in minutes (inclusive): " + Style.RESET_ALL))
    delay_range = (min_delay, max_delay)

    display_header()  # Clear screen and show header again before starting operations

    try:
        for private_key in private_keys:
            from_account = Account.from_key(private_key)
            gas_price, gas_limit = get_gas_settings(w3)

            for _ in range(tx_per_key):
                # Generate new wallets
                with ThreadPoolExecutor() as executor:
                    new_wallets = list(executor.map(lambda _: Account.create(), range(num_wallets_per_key)))
                
                to_addresses = [wallet.address for wallet in new_wallets]
                send_transactions(w3, from_account, to_addresses, amount_range, chain_id, delay_range, block_explorer, gas_price, gas_limit)
                print(f"\n{Fore.GREEN}Transactions for wallet {from_account.address} completed.{Style.RESET_ALL}")

            print("\nNew wallet addresses:")
            for i, wallet in enumerate(new_wallets, 1):
                print(f"Wallet {i}: {wallet.address}")

    except Exception as e:
        print(Fore.RED + f"An error occurred: {e}" + Style.RESET_ALL)

if __name__ == "__main__":
    main()
