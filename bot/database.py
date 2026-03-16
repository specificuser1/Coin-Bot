import json
import os
from datetime import datetime, timedelta
from config import COINS_FILE, KEYS_DIR

class Database:
    def __init__(self):
        self.coins_file = COINS_FILE
        self.ensure_files()
    
    def ensure_files(self):
        os.makedirs(os.path.dirname(self.coins_file), exist_ok=True)
        os.makedirs(KEYS_DIR, exist_ok=True)
        
        if not os.path.exists(self.coins_file):
            with open(self.coins_file, 'w') as f:
                json.dump({}, f)
        
        keys_file = os.path.join(KEYS_DIR, 'unused_keys.txt')
        if not os.path.exists(keys_file):
            with open(keys_file, 'w') as f:
                f.write('')
        
        redeemed_file = os.path.join(KEYS_DIR, 'redeemed_keys.txt')
        if not os.path.exists(redeemed_file):
            with open(redeemed_file, 'w') as f:
                f.write('')
    
    def get_user_coins(self, user_id):
        with open(self.coins_file, 'r') as f:
            data = json.load(f)
        return data.get(str(user_id), {'coins': 0, 'last_claim': None, 'daily_keys': 0})
    
    def update_user_coins(self, user_id, coins, last_claim=None, daily_keys=None):
        with open(self.coins_file, 'r') as f:
            data = json.load(f)
        
        if str(user_id) not in data:
            data[str(user_id)] = {'coins': 0, 'last_claim': None, 'daily_keys': 0}
        
        data[str(user_id)]['coins'] = coins
        if last_claim:
            data[str(user_id)]['last_claim'] = last_claim
        if daily_keys is not None:
            data[str(user_id)]['daily_keys'] = daily_keys
        
        with open(self.coins_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def add_coins(self, user_id, amount):
        user_data = self.get_user_coins(user_id)
        new_coins = user_data['coins'] + amount
        self.update_user_coins(user_id, new_coins)
        return new_coins
    
    def remove_coins(self, user_id, amount):
        user_data = self.get_user_coins(user_id)
        if user_data['coins'] >= amount:
            new_coins = user_data['coins'] - amount
            self.update_user_coins(user_id, new_coins)
            return True
        return False
    
    def get_all_users(self):
        with open(self.coins_file, 'r') as f:
            return json.load(f)
    
    def add_key(self, key):
        keys_file = os.path.join(KEYS_DIR, 'unused_keys.txt')
        with open(keys_file, 'a') as f:
            f.write(key + '\n')
    
    def get_key(self):
        keys_file = os.path.join(KEYS_DIR, 'unused_keys.txt')
        with open(keys_file, 'r') as f:
            keys = f.read().splitlines()
        
        if keys:
            key = keys[0]
            # Remove from unused
            with open(keys_file, 'w') as f:
                f.write('\n'.join(keys[1:]))
            
            # Add to redeemed
            redeemed_file = os.path.join(KEYS_DIR, 'redeemed_keys.txt')
            with open(redeemed_file, 'a') as f:
                f.write(f"{key}|{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            return key
        return None
    
    def check_key_exists(self, key):
        keys_file = os.path.join(KEYS_DIR, 'unused_keys.txt')
        with open(keys_file, 'r') as f:
            keys = f.read().splitlines()
        return key in keys
    
    def get_redeemed_keys(self):
        redeemed_file = os.path.join(KEYS_DIR, 'redeemed_keys.txt')
        if os.path.exists(redeemed_file):
            with open(redeemed_file, 'r') as f:
                lines = f.read().splitlines()
            return [line.split('|') for line in lines if line]
        return []
    
    def reset_daily_keys(self):
        with open(self.coins_file, 'r') as f:
            data = json.load(f)
        
        for user_id in data:
            data[user_id]['daily_keys'] = 0
        
        with open(self.coins_file, 'w') as f:
            json.dump(data, f, indent=4)
