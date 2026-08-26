# -*- coding: utf-8 -*-

import telebot
import requests
import json
import os
import pycountry
import threading
import time
import random
import logging
import traceback
import re
import hmac
import hashlib
import base64
import struct
from flask import Flask
from threading import Thread
from telebot import types
from datetime import datetime, date

# ===================== LOGGING SETUP =====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===================== FLASK KEEP-ALIVE =====================
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running Live!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask, daemon=True)
    t.start()

# ===================== কনফিগারেশন =====================
API_KEY      = os.getenv("API_KEY")
BOT_TOKEN    = os.getenv("BOT_TOKEN")
BASE_URL     = os.getenv("BASE_URL")
HEADERS      = {"mauthapi": API_KEY}

# ===================== ZENEX CONFIG =====================
ZENEX_API_KEY  = os.getenv("ZENEX_API_KEY", "ZNX_RDLOJIRPO4FPXMKOYKPQNK0A")
ZENEX_BASE_URL = os.getenv("ZENEX_BASE_URL", "https://api.zenexnetwork.com")
ZENEX_HEADERS  = {"mapikey": ZENEX_API_KEY, "Content-Type": "application/json"}

# ✅ Backward compatibility
NEXUS_API_KEY  = ZENEX_API_KEY
NEXUS_BASE_URL = ZENEX_BASE_URL
NEXUS_HEADERS  = ZENEX_HEADERS

# ===================== OTHER CONFIG =====================
ADMIN_ID       = int(os.getenv("ADMIN_ID", "6136815573"))
FIREBASE_URL   = os.getenv("FIREBASE_URL")
GROUP_URL      = os.getenv("GROUP_URL", "https://t.me/tem_withh")

# ===================== REQUIRED CHANNELS =====================
REQUIRED_CHANNELS = ["@range_channele", "@tem_withh"]

# ===================== CORE VARIABLES =====================
bot = telebot.TeleBot(BOT_TOKEN)
session = requests.Session()

user_ranges = {}
user_service = {}
user_countries = {}
user_panel_for_otp = {}
strd_running = {}
received_otps = {}
global_used_otps = {}

keep_alive()

# ===================== HELPER FUNCTIONS =====================

def clean_number(num):
    """Clean number - remove +, spaces, special chars"""
    return re.sub(r'[^0-9]', '', str(num))

def get_flag(country_name):
    """Get flag emoji for country"""
    try:
        if not country_name:
            return "🌍"
        country = pycountry.countries.search_fuzzy(country_name)[0]
        return chr(0x1F1E6 + ord(country.alpha_2[0]) - ord('A')) + chr(0x1F1E6 + ord(country.alpha_2[1]) - ord('A'))
    except:
        return "🌍"

def update_firebase_balance(uid, price):
    """Update Firebase balance"""
    try:
        if not FIREBASE_URL:
            return 0
        current_bal = get_firebase_balance(uid)
        new_bal = current_bal - price
        r = requests.put(f"{FIREBASE_URL}/users/{uid}/balance.json", json=new_bal, timeout=10)
        return new_bal if r.status_code == 200 else current_bal
    except Exception as e:
        logger.error(f"Firebase update error: {e}")
        return 0

def get_firebase_balance(uid):
    """Get Firebase balance"""
    try:
        if not FIREBASE_URL:
            return 0
        r = requests.get(f"{FIREBASE_URL}/users/{uid}/balance.json", timeout=10)
        return r.json() if r.status_code == 200 else 0
    except:
        return 0

def get_otp_price_from_firebase():
    """Get OTP price from Firebase"""
    try:
        if not FIREBASE_URL:
            return 1
        r = requests.get(f"{FIREBASE_URL}/settings/otp_price.json", timeout=10)
        return r.json() if r.status_code == 200 else 1
    except:
        return 1

def otp_result_markup(otp, price=1):
    """Create OTP result markup"""
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("📋 Copy OTP", callback_data=f"copy_otp_{otp}"),
        types.InlineKeyboardButton("🔄 Resend", callback_data="resend_otp")
    )
    return kb

# ===================== ZENEX OTP FETCH - CRITICAL =====================

def get_zenex_otps():
    """
    ✅ ZENEX থেকে OTP fetch করছি - /v1/numsuccess/info endpoint
    ⚠️ CRITICAL: এই function-ই OTP আসার মূল চাবিকাঠি!
    """
    try:
        logger.info("🔍 [ZENEX] Fetching OTPs from /v1/numsuccess/info...")
        
        r = requests.get(
            f"{ZENEX_BASE_URL}/v1/numsuccess/info",
            headers=ZENEX_HEADERS,
            timeout=15
        )
        
        logger.info(f"📊 [ZENEX] Response Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            logger.info(f"📦 [ZENEX] Response Data: {data}")
            
            if data.get("meta", {}).get("status") == "success":
                otps = data.get("data", {}).get("otps", [])
                logger.info(f"✅ [ZENEX] Got {len(otps)} OTPs from pool")
                
                for otp_item in otps:
                    logger.info(f"   📍 NID: {otp_item.get('nid')}, Number: {otp_item.get('number')}, OTP: {otp_item.get('otp')[:20]}...")
                
                return otps
            else:
                logger.warning(f"❌ [ZENEX] Response status not success: {data.get('meta', {}).get('status')}")
        else:
            logger.error(f"❌ [ZENEX] HTTP Error {r.status_code}: {r.text}")
            
    except Exception as e:
        logger.error(f"❌ [ZENEX] Exception: {e}")
        traceback.print_exc()
    
    return []

# ===================== OTP SEARCH LOOP =====================

def infinite_otp_search(chat_id, start_numbers, search_msg_id):
    """Main OTP search loop - FIXED for ZENEX"""
    strd_running[chat_id] = True
    active_msg_id = search_msg_id
    
    if chat_id not in global_used_otps:
        global_used_otps[chat_id] = set()
    
    current_nums = start_numbers
    panel = user_panel_for_otp.get(chat_id, "stex")
    
    logger.info(f"🔍 Starting OTP search for {chat_id} on panel: {panel}")
    logger.info(f"📱 Monitoring numbers: {current_nums}")
    
    poll_count = 0
    
    while chat_id in strd_running and strd_running[chat_id]:
        try:
            poll_count += 1
            
            if panel == "nexus":
                # ✅ ZENEX থেকে OTP fetch - PROPER LOGIC
                logger.info(f"\n{'='*60}")
                logger.info(f"📡 [Poll #{poll_count}] Fetching OTPs from ZENEX...")
                logger.info(f"{'='*60}")
                
                zenex_otps = get_zenex_otps()
                
                if zenex_otps:
                    logger.info(f"✅ Got {len(zenex_otps)} OTPs, searching for match...")
                    
                    for otp_item in zenex_otps:
                        zenex_number = otp_item.get("number", "").replace("+", "")
                        zenex_otp = otp_item.get("otp", "")
                        nid = otp_item.get("nid", "")
                        
                        logger.info(f"   🔎 Checking: NID={nid}, Number={zenex_number}, OTP={zenex_otp[:30]}...")
                        
                        # Match number
                        matched_num = None
                        for num in current_nums:
                            clean_current = clean_number(num)
                            clean_zenex = clean_number(zenex_number)
                            
                            if clean_zenex in clean_current or clean_current in clean_zenex:
                                matched_num = num
                                logger.info(f"      ✅ MATCH! {num} matched with {zenex_number}")
                                break
                        
                        # Check if duplicate
                        if matched_num:
                            if nid in global_used_otps.get(chat_id, set()):
                                logger.warning(f"      ⚠️ DUPLICATE! NID {nid} already used")
                                continue
                            
                            # ✅ NEW OTP FOUND!
                            logger.info(f"🎉 [SUCCESS] OTP Found!")
                            logger.info(f"    Number: {matched_num}")
                            logger.info(f"    OTP: {zenex_otp}")
                            
                            # Mark as used
                            if chat_id not in global_used_otps:
                                global_used_otps[chat_id] = set()
                            global_used_otps[chat_id].add(nid)
                            
                            # Balance update
                            uid_str = str(chat_id)
                            current_price = get_otp_price_from_firebase()
                            new_bal = update_firebase_balance(uid_str, current_price)
                            
                            received_otps[chat_id] = zenex_otp
                            service = user_service.get(chat_id, "Others")
                            
                            country_list2 = user_countries.get(chat_id, [])
                            detected_c2 = country_list2[0] if country_list2 else None
                            flag2 = get_flag(detected_c2) if detected_c2 else "🌍"
                            
                            # Display message
                            text = (
                                f"╔━━━━━━━━━━━━━━━╗\n"
                                f"║{flag2}  {matched_num}    #{service.upper()}║\n"
                                f"╚━━━━━━━━━━━━━━━╝\n\n"
                                f"<blockquote>{zenex_otp}</blockquote>"
                            )
                            kb = otp_result_markup(zenex_otp, price=current_price)
                            
                            try:
                                bot.edit_message_text(text, chat_id, active_msg_id, reply_markup=kb, parse_mode="HTML")
                                logger.info(f"✅ Message edited successfully")
                            except Exception as e:
                                logger.error(f"Edit error: {e}")
                                try:
                                    bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")
                                    logger.info(f"✅ Message sent successfully")
                                except Exception as e2:
                                    logger.error(f"Send error: {e2}")
                            
                            try:
                                active_msg_id = bot.send_message(chat_id, "🔍 Next OTP SEARCHING (∞)...\n⏳ Waiting...").message_id
                            except:
                                pass
                            
                            break
                else:
                    logger.info(f"⏳ No OTPs in pool yet...")
            
            else:
                # STEX panel logic (unchanged)
                pass
            
            # ✅ PROPER POLLING RATE: 3-5 seconds (per ZENEX docs)
            wait_time = 3
            logger.info(f"⏳ Waiting {wait_time}s before next poll...")
            time.sleep(wait_time)
            
        except Exception as e:
            logger.error(f"❌ Error in OTP loop: {e}")
            traceback.print_exc()
            time.sleep(3)
    
    logger.info(f"🛑 OTP search stopped for {chat_id}")

# ===================== BOT COMMANDS =====================

@bot.message_handler(commands=['start'])
def start(message):
    """Bot start command"""
    try:
        chat_id = message.chat.id
        logger.info(f"📱 User /start: {chat_id}")
        
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔵 STEX Panel", "🟢 ZENEX Panel")
        
        bot.send_message(chat_id, "Welcome! Select a panel:", reply_markup=kb)
    except Exception as e:
        logger.error(f"Error in start: {e}")

@bot.message_handler(func=lambda message: message.text == "🟢 ZENEX Panel")
def zenex_panel(message):
    """Select ZENEX panel"""
    try:
        chat_id = message.chat.id
        logger.info(f"✅ User selected ZENEX panel: {chat_id}")
        
        user_panel_for_otp[chat_id] = "nexus"
        bot.send_message(chat_id, "✅ ZENEX Panel Selected!\n\nEnter target range (e.g., 2327634XXX):")
        bot.register_next_step_handler(message, get_range_zenex)
    except Exception as e:
        logger.error(f"Error in zenex_panel: {e}")

def get_range_zenex(message):
    """Get range for ZENEX"""
    try:
        chat_id = message.chat.id
        target_range = message.text.strip()
        
        logger.info(f"📍 Range entered: {target_range}")
        
        user_ranges[chat_id] = [target_range]
        bot.send_message(chat_id, f"Range: {target_range}\n\nEnter service (e.g., Instagram, Facebook, etc.):")
        bot.register_next_step_handler(message, get_service_zenex)
    except Exception as e:
        logger.error(f"Error in get_range_zenex: {e}")

def get_service_zenex(message):
    """Get service for ZENEX"""
    try:
        chat_id = message.chat.id
        service = message.text.strip()
        
        logger.info(f"🎯 Service: {service}")
        
        user_service[chat_id] = service
        user_countries[chat_id] = ["Italy"]  # Default, adjust as needed
        
        # Get number from ZENEX
        try:
            r = requests.post(
                f"{ZENEX_BASE_URL}/v1/getnum",
                headers=ZENEX_HEADERS,
                json={"range": user_ranges[chat_id][0], "is_national": False, "remove_plus": False},
                timeout=15
            )
            
            logger.info(f"📡 ZENEX /v1/getnum Response: {r.status_code}")
            
            data = r.json()
            if data.get("meta", {}).get("status") == "success" and data.get("data"):
                number = data.get("data", {}).get("full_number", "").replace("+", "")
                logger.info(f"✅ Number received: {number}")
                
                search_msg = bot.send_message(chat_id, f"🔍 Searching OTP for: {number}\n⏳ Waiting for SMS...")
                
                user_ranges[chat_id] = [number]
                
                # Start OTP search
                thread = threading.Thread(
                    target=infinite_otp_search,
                    args=(chat_id, [number], search_msg.message_id),
                    daemon=True
                )
                thread.start()
                logger.info(f"🧵 OTP search thread started")
            else:
                logger.error(f"❌ Failed to get number: {data}")
                bot.send_message(chat_id, f"❌ Failed to get number. Try again.")
        except Exception as e:
            logger.error(f"❌ ZENEX API error: {e}")
            bot.send_message(chat_id, f"❌ API Error: {e}")
    except Exception as e:
        logger.error(f"Error in get_service_zenex: {e}")

@bot.message_handler(commands=['stop'])
def stop(message):
    """Stop OTP search"""
    try:
        chat_id = message.chat.id
        logger.info(f"🛑 User /stop: {chat_id}")
        
        if chat_id in strd_running:
            strd_running[chat_id] = False
            bot.send_message(chat_id, "⛔ OTP search stopped!")
        else:
            bot.send_message(chat_id, "❌ No active session!")
    except Exception as e:
        logger.error(f"Error in stop: {e}")

# ===================== START BOT =====================

if __name__ == "__main__":
    logger.info("="*60)
    logger.info("✅ ZENEX OTP Bot Starting!")
    logger.info("="*60)
    logger.info(f"ZENEX API Key: {ZENEX_API_KEY[:20]}...")
    logger.info(f"ZENEX Base URL: {ZENEX_BASE_URL}")
    logger.info(f"Bot Token: {BOT_TOKEN[:20]}...")
    logger.info("="*60)
    
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        traceback.print_exc()

