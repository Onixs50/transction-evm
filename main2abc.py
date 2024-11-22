#!/usr/bin/env python3


import json
import os
import time
import random
from web3 import Web3
from eth_account import Account
from colorama import Fore, Style, init
from web3.exceptions import ContractLogicError

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
        with open(CONFIG_FILE, 'r') as f:
            content = f.read().strip()
            if content:
                return json.loads(content)
    return None

def save_private_keys(private_keys):
    with open(PRIVATE_KEYS_FILE, 'w') as f:
        for key in private_keys:
            f.write(key + '\n')

def get_user_input():
    rpc_url = input(Fore.CYAN + "Enter the RPC URL: " + Style.RESET_ALL)
    chain_id = int(input(Fore.CYAN + "Enter the Chain ID: " + Style.RESET_ALL))
    block_explorer = input(Fore.CYAN + "Enter the Block Explorer URL: " + Style.RESET_ALL)
    return rpc_url, chain_id, block_explorer

def estimate_gas_price(w3, multiplier=1.1):
    """Estimate gas price with a safety multiplier"""
    try:
        base_fee = w3.eth.get_block('latest').baseFeePerGas
        priority_fee = w3.eth.max_priority_fee
        gas_price = int((base_fee + priority_fee) * multiplier)
    except:
        # Fallback to legacy gas price estimation
        gas_price = int(w3.eth.gas_price * multiplier)
    return gas_price

def estimate_gas_limit(w3, from_address, to_address, value):
    """Estimate gas limit with a safety margin"""
    try:
        estimated_gas = w3.eth.estimate_gas({
            'from': from_address,
            'to': to_address,
            'value': value
        })
        return int(estimated_gas * 1.2)  # Add 20% safety margin
    except:
        return 21000  # Default gas limit for basic ETH transfers

def get_gas_settings(w3, from_address, to_address, value):
    gas_price = estimate_gas_price(w3)
    gas_limit = estimate_gas_limit(w3, from_address, to_address, value)
    
    gas_price_gwei = w3.from_wei(gas_price, 'gwei')
    print(f"\n{Fore.YELLOW}Estimated gas settings:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Gas Price: {gas_price_gwei:.2f} Gwei{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Gas Limit: {gas_limit}{Style.RESET_ALL}")
    
    confirm = input(Fore.CYAN + "\nDo you want to use these gas settings? (y/n): " + Style.RESET_ALL).lower()
    if confirm != 'y':
        gas_price_gwei = float(input(Fore.CYAN + "Enter new Gas Price (in Gwei): " + Style.RESET_ALL))
        gas_price = w3.to_wei(gas_price_gwei, 'gwei')
        gas_limit = int(input(Fore.CYAN + "Enter new Gas Limit: " + Style.RESET_ALL))

    return gas_price, gas_limit

def send_transaction(w3, from_account, to_address, amount, nonce, chain_id):
    value = w3.to_wei(amount, 'ether')
    gas_price = estimate_gas_price(w3, 1.2)  # Add 20% to gas price
    gas_limit = estimate_gas_limit(w3, from_account.address, to_address, value)
    
    tx = {
        'nonce': nonce,
        'to': to_address,
        'value': value,
        'gas': gas_limit,
        'gasPrice': gas_price,
        'chainId': chain_id
    }
    
    # Add retry mechanism
    max_retries = 3
    for attempt in range(max_retries):
        try:
            signed_tx = from_account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            return tx_hash
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"{Fore.YELLOW}Retry attempt {attempt + 1} due to error: {str(e)}{Style.RESET_ALL}")
                gas_price = int(gas_price * 1.2)  # Increase gas price by 20% for retry
                tx['gasPrice'] = gas_price
                time.sleep(2)  # Wait before retry
            else:
                raise e

def send_transactions(w3, from_account, to_addresses, amount_range, chain_id, delay_range, block_explorer):
    nonce = w3.eth.get_transaction_count(from_account.address)
    for i, to_address in enumerate(to_addresses, 1):
        try:
            balance = w3.eth.get_balance(from_account.address)
            balance_eth = w3.from_wei(balance, 'ether')
            print(f"\n{Fore.YELLOW}Wallet {from_account.address} Balance: {balance_eth:.6f} ETH{Style.RESET_ALL}")

            amount = random.uniform(*amount_range)
            delay = random.uniform(*delay_range) * 60

            tx_hash = send_transaction(w3, from_account, to_address, amount, nonce, chain_id)
            print(f"{Fore.GREEN}Transaction {i} sent from wallet {from_account.address}:{Style.RESET_ALL}")
            print(f"  {Fore.CYAN}To:{Style.RESET_ALL} {to_address}")
            print(f"  {Fore.CYAN}Amount:{Style.RESET_ALL} {amount:.6f} ETH")
            print(f"  {Fore.CYAN}Transaction Hash:{Style.RESET_ALL} {tx_hash.hex()}")
            if block_explorer:
                print(f"  {Fore.CYAN}Block Explorer Link:{Style.RESET_ALL} {block_explorer}/tx/{tx_hash.hex()}")
            print(Fore.GREEN + "-" * 20 + Style.RESET_ALL)
            
            # Wait for transaction confirmation
            try:
                w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
                print(f"{Fore.GREEN}Transaction confirmed!{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}Warning: Could not confirm transaction: {str(e)}{Style.RESET_ALL}")
            
            nonce += 1
            minutes_remaining = delay / 60
            print(f"{Fore.YELLOW}Next transaction will be sent in approximately {minutes_remaining:.2f} minutes.{Style.RESET_ALL}")
            time.sleep(delay)
            
        except Exception as e:
            print(f"{Fore.RED}Transaction {i} failed:{Style.RESET_ALL}")
            print(f"  {Fore.CYAN}To:{Style.RESET_ALL} {to_address}")
            print(f"  {Fore.CYAN}Error:{Style.RESET_ALL} {str(e)}")
            print(Fore.RED + "-" * 20 + Style.RESET_ALL)
            time.sleep(5)  # Wait before continuing to next transaction

def get_config():
    config = load_config()
    if config:
        use_previous = input(Fore.CYAN + "Do you want to use the previous configuration? (y/n): " + Style.RESET_ALL).lower()
        if use_previous == 'y':
            return config['rpc_url'], config['chain_id'], config['block_explorer']
    return get_user_input()

def main():
    display_header()
    
    rpc_url, chain_id, block_explorer = get_config()
    save_config(rpc_url, chain_id, block_explorer)

    # Initialize Web3 with retry mechanism
    max_retries = 3
    for attempt in range(max_retries):
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if w3.is_connected():
                break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"{Fore.YELLOW}Retry attempt {attempt + 1} to connect to network...{Style.RESET_ALL}")
                time.sleep(2)
            else:
                print(Fore.RED + "Failed to connect to the network. Please check your RPC URL." + Style.RESET_ALL)
                return

    if not w3.is_connected():
        print(Fore.RED + "Failed to connect to the network. Please check your RPC URL." + Style.RESET_ALL)
        return

    try:
        network_chain_id = w3.eth.chain_id
        if network_chain_id != chain_id:
            print(Fore.YELLOW + f"Warning: The provided Chain ID ({chain_id}) does not match the network's Chain ID ({network_chain_id})." + Style.RESET_ALL)
            continue_anyway = input(Fore.CYAN + "Do you want to continue anyway? (y/n): " + Style.RESET_ALL).lower()
            if continue_anyway != 'y':
                return
    except Exception as e:
        print(Fore.YELLOW + f"Warning: Could not verify chain ID: {str(e)}" + Style.RESET_ALL)

    if os.path.exists(PRIVATE_KEYS_FILE):
        use_previous_keys = input(Fore.CYAN + "Previous private keys found. Do you want to use them? (y/n): " + Style.RESET_ALL).lower()
        if use_previous_keys == 'y':
            with open(PRIVATE_KEYS_FILE, 'r') as f:
                private_keys = [line.strip() for line in f.readlines()]
        else:
            num_keys = int(input(Fore.CYAN + "How many new private keys do you want to add? " + Style.RESET_ALL))
            private_keys = [input(f"{Fore.CYAN}Enter private key {i + 1}: " + Style.RESET_ALL) for i in range(num_keys)]
            save_private_keys(private_keys)
    else:
        num_keys = int(input(Fore.CYAN + "How many private keys do you want to add? " + Style.RESET_ALL))
        private_keys = [input(f"{Fore.CYAN}Enter private key {i + 1}: " + Style.RESET_ALL) for i in range(num_keys)]
        save_private_keys(private_keys)

    tx_per_key = int(input(Fore.CYAN + "How many transactions per private key? " + Style.RESET_ALL))
    num_wallets_per_key = int(input(Fore.CYAN + "How many new wallets to generate per private key? " + Style.RESET_ALL))
    min_amount = float(input(Fore.CYAN + "Enter minimum amount of ETH to send (inclusive): " + Style.RESET_ALL))
    max_amount = float(input(Fore.CYAN + "Enter maximum amount of ETH to send (inclusive): " + Style.RESET_ALL))
    amount_range = (min_amount, max_amount)
    min_delay = float(input(Fore.CYAN + "Enter minimum delay between transactions in minutes (inclusive): " + Style.RESET_ALL))
    max_delay = float(input(Fore.CYAN + "Enter maximum delay between transactions in minutes (inclusive): " + Style.RESET_ALL))
    delay_range = (min_delay, max_delay)

    display_header()

    try:
        while True:
            for private_key in private_keys:
                from_account = Account.from_key(private_key)
                to_addresses = [Account.create().address for _ in range(num_wallets_per_key)]
                for _ in range(tx_per_key):
                    send_transactions(w3, from_account, to_addresses, amount_range, chain_id, delay_range, block_explorer)
                print(f"{Fore.YELLOW}Completed transactions for wallet {from_account.address}.{Style.RESET_ALL}")
    except KeyboardInterrupt:
        print(Fore.RED + "\nProcess interrupted by user. Exiting..." + Style.RESET_ALL)

if __name__ == '__main__':
    main()
