#!/usr/bin/env python3
# ============================================
# FLOREIXA BOT – SECURE VERSION
# Owner: SKY FLOREX 🪐
# ============================================

import os
import sys
import re
import time
import json
import math
import random
import sqlite3
import queue
import requests
from datetime import datetime
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from telebot import TeleBot, types
from telebot.apihelper import ApiException

# ========== SECURE CONFIGURATION ==========
# Token environment variable se lo (Bothost.me mein set karna)
BOT_TOKEN = os.environ.get("8603082164:AAGL_p23Mg0TEuW7p-q5S8QbPcbp3rsd82A")
if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN environment variable not set!")
    print("Please set it in Bothost.me dashboard → Environment Variables")
    sys.exit(1)

# Owner ID bhi environment variable se lo (optional)
try:
    OWNER_ID = int(os.environ.get("OWNER_ID", "7808744534"))
except:
    OWNER_ID = 7808744534

RECHARGE_CONTACT = os.environ.get("RECHARGE_CONTACT", "@LazyMikey")
OWNER_NAME = os.environ.get("OWNER_NAME", "SKY FLOREX 🪐")
SUPPORT_CONTACT = os.environ.get("SUPPORT_CONTACT", "@LazyMikey")
STORE_NAME = os.environ.get("STORE_NAME", "FLOREIXA 🍡")
REFERRAL_BONUS = int(os.environ.get("REFERRAL_BONUS", "1"))
CHANNEL_LINK = os.environ.get("CHANNEL_LINK", "https://t.me/TEAM_FLOREX")
# ===========================================

bot = TeleBot(BOT_TOKEN)

# ========== RATE LIMITING ==========
RATE_LIMIT = 30  # 30 requests per minute
rate_limit_dict = {}
rate_limit_lock = Lock()

def check_rate_limit(user_id):
    with rate_limit_lock:
        now = time.time()
        if user_id in rate_limit_dict:
            # Clean old entries (older than 60 seconds)
            rate_limit_dict[user_id] = [t for t in rate_limit_dict[user_id] if now - t < 60]
            if len(rate_limit_dict[user_id]) >= RATE_LIMIT:
                return False
            rate_limit_dict[user_id].append(now)
        else:
            rate_limit_dict[user_id] = [now]
    return True

# ========== SECURE DATABASE ==========
class SecureDatabasePool:
    def __init__(self, db_path, max_connections=5):
        self.db_path = db_path
        self.max_connections = max_connections
        self._pool = queue.Queue(max_connections)
        self._lock = Lock()
        
        for _ in range(max_connections):
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            self._pool.put(conn)
    
    def get_connection(self):
        return self._pool.get()
    
    def return_connection(self, conn):
        self._pool.put(conn)

# Database initialize
db_path = 'floreixa.db'  # Aapka existing database file
pool = SecureDatabasePool(db_path)

def get_cursor():
    conn = pool.get_connection()
    return conn.cursor(), conn

def close_cursor(cursor, conn):
    cursor.close()
    pool.return_connection(conn)

# ========== INPUT VALIDATION ==========
def sanitize_input(text, max_length=1000):
    """User input ko safe banayein"""
    if not text or not isinstance(text, str):
        return ""
    # Control characters hatao
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    return cleaned[:max_length]

def validate_amount(amount):
    try:
        return int(amount) > 0
    except:
        return False

# ========== EXISTING FUNCTIONS (Aapke original se) ==========
# Yahan par aap apne original functions copy kar sakte ho
# Jaise: add_user, get_balance, update_balance, etc.
# Main function names wahi rahenge, bas andar database access secure ho

def get_balance(user_id):
    c, conn = get_cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    close_cursor(c, conn)
    return res[0] if res else 0

def is_admin(user_id):
    if user_id == OWNER_ID:
        return True
    c, conn = get_cursor()
    c.execute("SELECT is_admin FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    close_cursor(c, conn)
    return res and res[0] == 1

def is_blocked(user_id):
    c, conn = get_cursor()
    c.execute("SELECT is_blocked FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    close_cursor(c, conn)
    return res and res[0] == 1

# ... aap apne saare original functions yahan add karo ...

# ========== SAFE MESSAGE SENDING ==========
def safe_send_message(chat_id, text, parse_mode='Markdown', **kwargs):
    try:
        return bot.send_message(chat_id, text, parse_mode=parse_mode, **kwargs)
    except ApiException as e:
        # Try without markdown
        try:
            return bot.send_message(chat_id, text, parse_mode=None, **kwargs)
        except:
            return None
    except Exception as e:
        print(f"Message error: {e}")
        return None

def escape_markdown(text):
    if not text:
        return ""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

# ========== START COMMAND ==========
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    
    # Rate limit check
    if not check_rate_limit(user_id):
        safe_send_message(user_id, "⚠️ Too many requests. Please slow down.")
        return
    
    # Aapka existing start logic yahan copy karo
    # Example:
    text = f"🌟 Welcome {message.from_user.first_name}!\nUse /menu to continue."
    safe_send_message(user_id, text)

# ========== CALLBACK HANDLER ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if not check_rate_limit(user_id):
        bot.answer_callback_query(call.id, "⚠️ Slow down!", show_alert=True)
        return
    
    if is_blocked(user_id):
        bot.answer_callback_query(call.id, "⛔ You are blocked.", show_alert=True)
        return
    
    # Aapke saare callback handlers yahan copy karo
    # ...

# ========== ADMIN COMMANDS ==========
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        safe_send_message(user_id, "⛔ Access denied.")
        return
    
    # Admin menu yahan banao
    markup = types.InlineKeyboardMarkup()
    # ... buttons ...
    safe_send_message(user_id, "Admin Panel", reply_markup=markup)

# ========== RUN BOT ==========
if __name__ == "__main__":
    print("🤖 FLOREIXA Secure Bot Starting...")
    print(f"👑 Owner: {OWNER_ID}")
    print("✅ Security: Rate Limiting, Input Validation, Env Variables")
    
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Bot crashed: {e}. Restarting in 5s...")
            time.sleep(5)