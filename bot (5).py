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
# ✅ সব sensitive তথ্য (টোকেন, key, url) এখন কোডে নেই — Render-এর
# Environment Variables থেকে পড়া হচ্ছে, তাই GitHub-এ ফাইল আপলোড করলেও চুরি হবে না।
API_KEY      = os.getenv("API_KEY")
BOT_TOKEN    = os.getenv("BOT_TOKEN")
BASE_URL     = os.getenv("BASE_URL")
HEADERS      = {"mauthapi": API_KEY}

# ===================== ZENEX CONFIG =====================
ZENEX_API_KEY  = os.getenv("ZENEX_API_KEY", "ZNX_RDLOJIRPO4FPXMKOYKPQNK0A")
ZENEX_BASE_URL = os.getenv("ZENEX_BASE_URL", "https://api.zenexnetwork.com")
ZENEX_HEADERS  = {"mapikey": ZENEX_API_KEY, "Content-Type": "application/json"}

# ✅ Backward compatibility - NEXUS variables পুরনো কোডের জন্য
NEXUS_API_KEY  = ZENEX_API_KEY
NEXUS_BASE_URL = ZENEX_BASE_URL
NEXUS_HEADERS  = ZENEX_HEADERS

ADMIN_ID     = os.getenv("ADMIN_ID")
GROUP_URL    = os.getenv("GROUP_URL", "https://t.me/tem_withh")
FIREBASE_URL = os.getenv("FIREBASE_URL")

# ✅ Render-এ Environment Variables সেট করা না থাকলে পরিষ্কার এরর দেখাবে
_required_env = {
    "BOT_TOKEN": BOT_TOKEN, "API_KEY": API_KEY, "BASE_URL": BASE_URL,
    "ZENEX_API_KEY": ZENEX_API_KEY, "ADMIN_ID": ADMIN_ID, "FIREBASE_URL": FIREBASE_URL,
}
_missing = [k for k, v in _required_env.items() if not v]
if _missing:
    raise SystemExit(
        f"❌ Missing environment variables: {', '.join(_missing)}\n"
        f"Render Dashboard → your service → Environment → এই ভ্যারিয়েবলগুলো যোগ করুন।"
    )

REQUIRED_CHANNELS = ["@range_channele", "@tem_withh"]

FIXED_SERVICES = ["Facebook", "Instagram", "WhatsApp", "Imo", "Telegram", "TikTok"]

# ✅ Fancy (𝖒𝖆𝖙𝖍 𝖘𝖆𝖓𝖘-𝖘𝖊𝖗𝖎𝖋) কীবোর্ড লেবেল
BTN_GET_NUMBER    = "📱 𝗚𝗘𝗧 𝗡𝗨𝗠𝗕𝗘𝗥"
BTN_LIVE_TRAFFIC  = "📡 𝗟𝗜𝗩𝗘 𝗧𝗥𝗔𝗙𝗙𝗜𝗖"
BTN_2FA           = "🔐 𝟮𝗙𝗔 𝗖𝗢𝗗𝗘"
BTN_ADMIN_SUPPORT = "☎️ 𝗔𝗗𝗠𝗜𝗡 𝗦𝗨𝗣𝗣𝗢𝗥𝗧"
BTN_BALANCE       = "💰 𝗕𝗔𝗟𝗔𝗡𝗖𝗘"
BTN_PROFILE       = "👤 𝗣𝗥𝗢𝗙𝗜𝗟𝗘"
BTN_ADMIN_PANEL   = "🛠️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟"
SELECT_SERVICE_TEXT = "📱 𝗦𝗲𝗹𝗲𝗰𝘁 𝗮 𝗦𝗲𝗿𝘃𝗶𝗰𝗲"

SERVICE_LABELS = {
    "Facebook":  "𝖥𝖺𝖼𝖾𝖻𝗈𝗈𝗄",
    "Instagram": "𝖨𝗇𝗌𝗍𝖺𝗀𝗋𝖺𝗆",
    "WhatsApp":  "𝖶𝗁𝖺𝗍𝗌𝖠𝗉𝗉",
    "Imo":       "𝖨𝗆𝗈",
    "Telegram":  "𝖳𝖾𝗅𝖾𝗀𝗋𝖺𝗆",
    "TikTok":    "𝖳𝗂𝗄𝖳𝗈𝗄",
}

SERVICE_ICONS = {
    "Facebook":  "F",
    "WhatsApp":  "💬",
    "Telegram":  "✈️",
    "Instagram": "📸",
    "Imo":       "🟢",
    "TikTok":    "🎵",
}

SERVICE_TAGS = {
    "facebook":  "#FB",
    "whatsapp":  "#WA",
    "telegram":  "#TG",
    "instagram": "#IG",
    "imo":       "#IM",
    "tiktok":    "#TIKTOK",
}

def get_service_tag(service_name):
    return SERVICE_TAGS.get(str(service_name).strip().lower(), f"#{str(service_name)[:2].upper()}")

def make_box(lines):
    """একাধিক লাইনকে ছোট, কমপ্যাক্ট বক্স আকারে সাজায় (বর্ডার ডান পাশ থেকে সামান্য ছোট, কিন্তু লেখা কাটবে না)"""
    content_width = max(len(l) for l in lines) if lines else 0
    border_width  = max(0, content_width - 8)
    top    = "╔" + "━" * border_width + "╗"
    bottom = "╚" + "━" * border_width + "╝"
    body   = "\n".join(f"║{l}║" for l in lines)
    return f"{top}\n{body}\n{bottom}"

OTP_PRICE = 0.40

# ===================== SESSION & BOT =====================
session = requests.Session()
session.headers.update(HEADERS)

logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")
bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=20)

# ===================== IN-MEMORY STATE =====================
users           = {}
user_ranges     = {}
user_service    = {}
user_numbers    = {}       # chat_id → [num1, num2]  (list of up to 2)
user_countries  = {}
user_api_ids    = {}      # chat_id → [nexus_id1, nexus_id2]  (OTP চেক করার জন্য /numbers/{id})
user_panel_for_otp = {}  # Panel track করছি OTP এর জন্য       # chat_id → [country1, country2]
received_otps   = {}
used_otps       = {}
otp_running     = {}
otp_generation  = {}   # ✅ chat_id → generation number, Change Number চাপলেই পুরনো থ্রেড সাথে সাথে বন্ধ হবে
strd_running    = {}
withdraw_data   = {}
withdraw_status = {}       # uid_str → {status, amount, method, number, msg_id}
user_names      = {}
admin_state     = {}

# Today stats per user
today_earn      = {}       # uid_str → float
today_otp_count = {}       # uid_str → int
today_date      = {}       # uid_str → date string

global_used_otps = {}

service_countries = {s: [] for s in FIXED_SERVICES}

# ===================== COLORED BUTTON HELPER =====================
def make_button(text, callback_data=None, url=None, style="primary", copy_text_val=None):
    d = {"text": text, "style": style}
    if callback_data:
        d["callback_data"] = callback_data
    if url:
        d["url"] = url
    if copy_text_val:
        d["copy_text"] = {"text": copy_text_val}
    return d

def build_inline_keyboard(rows):
    kb = types.InlineKeyboardMarkup()
    kb.keyboard = []
    for row in rows:
        kb_row = []
        for d in row:
            if "url" in d:
                b = types.InlineKeyboardButton(text=d["text"], url=d["url"])
            elif "copy_text" in d:
                b = types.InlineKeyboardButton(
                    text=d["text"],
                    copy_text=types.CopyTextButton(text=d["copy_text"]["text"])
                )
            else:
                b = types.InlineKeyboardButton(
                    text=d["text"],
                    callback_data=d.get("callback_data", "noop")
                )
            if "style" in d:
                b.__dict__["style"] = d["style"]
            kb_row.append(b)
        kb.keyboard.append(kb_row)
    return kb

# ===================== FIREBASE =====================
def _fb_get(path):
    try:
        r = session.get(f"{FIREBASE_URL}{path}.json", timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def _fb_put(path, data):
    try:
        session.put(
            f"{FIREBASE_URL}{path}.json",
            data=json.dumps(data, ensure_ascii=False),
            timeout=10
        )
    except Exception:
        pass

def _fb_delete(path):
    try:
        session.delete(f"{FIREBASE_URL}{path}.json", timeout=10)
    except Exception:
        pass

# ✅ OTP Price Firebase functions
def get_otp_price_from_firebase():
    val = _fb_get("/admin/otp_price")
    try:
        if val is not None:
            return float(val)
    except Exception:
        pass
    return OTP_PRICE

def set_otp_price_to_firebase(price):
    price = round(float(price), 2)
    _fb_put("/admin/otp_price", price)
    return price

def get_firebase_balance(uid):
    val = _fb_get(f"/users/{uid}/balance")
    try:
        return float(val) if val is not None else 0.0
    except Exception:
        return 0.0

def update_firebase_balance(uid, amount):
    uid = str(uid)
    current = get_firebase_balance(uid)
    new_bal = round(current + amount, 2)
    _fb_put(f"/users/{uid}/balance", new_bal)
    # today stats
    today_str = str(date.today())
    if today_date.get(uid) != today_str:
        today_date[uid]      = today_str
        today_earn[uid]      = 0.0
        today_otp_count[uid] = 0
    today_earn[uid]      = round(today_earn.get(uid, 0.0) + amount, 2)
    today_otp_count[uid] = today_otp_count.get(uid, 0) + 1
    return new_bal

def set_firebase_balance(uid, val):
    uid     = str(uid)
    new_bal = round(float(val), 2)
    _fb_put(f"/users/{uid}/balance", new_bal)
    return new_bal

def clear_all_balances():
    data = _fb_get("/users")
    if isinstance(data, dict):
        for uid in data:
            _fb_put(f"/users/{uid}/balance", 0)

def register_user(uid, name="User"):
    uid = str(uid)
    if uid not in users:
        users[uid] = {"balance": 0}
    if not _fb_get(f"/users/{uid}/registered"):
        _fb_put(f"/users/{uid}/registered", True)
    _fb_put(f"/users/{uid}/name", name)

def load_all_users_from_firebase():
    data = _fb_get("/users")
    if isinstance(data, dict):
        for uid, val in data.items():
            if uid not in users:
                users[uid] = {"balance": 0}
            # name একই data থেকে নাও — আলাদা request না
            if isinstance(val, dict) and val.get("name"):
                user_names[uid] = val["name"]

def load_countries_from_firebase():
    for sname in FIXED_SERVICES:
        data = _fb_get(f"/service_data/{sname}")
        if isinstance(data, list):
            service_countries[sname] = [c for c in data if isinstance(c, dict) and "name" in c and "rid" in c]
        elif isinstance(data, dict):
            service_countries[sname] = [v for v in data.values() if isinstance(v, dict) and "name" in v and "rid" in v]
        else:
            service_countries[sname] = []

def save_countries_to_firebase(service_name):
    _fb_put(f"/service_data/{service_name}", service_countries[service_name])

# ===================== STARTUP =====================
load_all_users_from_firebase()
load_countries_from_firebase()

# ===================== TOTP (2FA) =====================
def _totp_generate(secret_b32: str, digits: int = 6, period: int = 30) -> str:
    try:
        secret_b32    = secret_b32.upper().strip().replace(" ", "")
        pad           = (8 - len(secret_b32) % 8) % 8
        secret_bytes  = base64.b32decode(secret_b32 + "=" * pad)
        counter       = int(time.time()) // period
        counter_bytes = struct.pack(">Q", counter)
        h             = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()
        offset        = h[-1] & 0x0F
        code_int      = struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF
        return str(code_int % (10 ** digits)).zfill(digits)
    except Exception:
        return None

# ===================== OTP EXTRACTION =====================
def extract_otp(message_text, phone_number=None):
    if not message_text:
        return None
    phone_digits = clean_number(phone_number) if phone_number else ""

    # নোট: re.ASCII ব্যবহার করা হচ্ছে কারণ Python-এ ডিফল্টভাবে \b (word boundary)
    # Unicode-aware — জাপানি/চাইনিজ/কোরিয়ান অক্ষরকেও "word character" ধরে নেয়।
    # ফলে "09977がFacebook..." এর মতো মেসেজে (OTP-এর ঠিক পরেই কোনো স্পেস ছাড়া
    # CJK অক্ষর থাকলে) boundary ধরতে ব্যর্থ হতো, আর ভুল OTP বের হতো।
    # re.ASCII দিলে শুধু ASCII অক্ষরকেই word character ধরবে, তাই boundary
    # সঠিকভাবে কাজ করবে।

    # STEP 1: "975-802" বা "975 802" এর মতো dash/space দেওয়া OTP ধরো
    dashed_matches = re.findall(r'\b(\d{3,5}[-\s]\d{3,5})\b', message_text, re.ASCII)
    for match in dashed_matches:
        joined = re.sub(r'[-\s]', '', match)
        if not joined.isdigit():
            continue
        if phone_digits and (joined in phone_digits or phone_digits in joined):
            continue
        if 4 <= len(joined) <= 10:
            return joined

    # STEP 2: "138 740" এর মতো spaced OTP ধরো
    spaced_matches = re.findall(r'\b(\d[\d ]{2,12}\d)\b', message_text, re.ASCII)
    for match in spaced_matches:
        joined = match.replace(" ", "")
        if not joined.isdigit():
            continue
        if phone_digits and (joined in phone_digits or phone_digits in joined):
            continue
        if 4 <= len(joined) <= 10:
            return joined

    # STEP 3: keyword দিয়ে OTP খোঁজো
    keyword_patterns = [
        r'(?:code|otp|OTP|Code|verification|verify|passcode|password|কোড)[^\d]*(\d{4,8})',
        r'(\d{4,8})[^\d]*(?:is your|as your|কোড)',
    ]
    for pattern in keyword_patterns:
        match = re.search(pattern, message_text, re.IGNORECASE | re.ASCII)
        if match:
            candidate = match.group(1)
            if phone_digits and candidate in phone_digits:
                continue
            return candidate

    # STEP 4: সাধারণ ৪-১০ digit
    candidates = re.findall(r'\b(\d{4,10})\b', message_text, re.ASCII)
    for candidate in candidates:
        if phone_digits:
            if candidate in phone_digits:
                continue
            if phone_digits in candidate:
                continue
            if phone_digits[-10:] in candidate:
                continue
        if len(candidate) == 4 and candidate.startswith(('19', '20')):
            continue
        if 4 <= len(candidate) <= 10:
            return candidate

    # STEP 5: fallback
    all_digits = re.sub(r'\D', '', message_text)
    if phone_digits:
        all_digits = all_digits.replace(phone_digits, "")
        if len(phone_digits) >= 10:
            all_digits = all_digits.replace(phone_digits[-10:], "")
    if len(all_digits) >= 4:
        return all_digits[-6:] if len(all_digits) >= 6 else all_digits
    return None

def extract_country_from_otp_message(msg_text):
    """OTP মেসেজ থেকে flag emoji এবং country detect করা"""
    if not msg_text:
        return None, None
    
    # Flag emoji খুঁজা
    for i in range(len(msg_text) - 1):
        char1 = msg_text[i]
        char2 = msg_text[i + 1]
        code1 = ord(char1)
        code2 = ord(char2)
        
        if 0x1F1E6 <= code1 <= 0x1F1FF and 0x1F1E6 <= code2 <= 0x1F1FF:
            # Flag পাওয়া গেছে
            flag_emoji = char1 + char2
            
            # Country code বের করা
            c1 = code1 - 0x1F1E6
            c2 = code2 - 0x1F1E6
            country_code = chr(c1 + ord('A')) + chr(c2 + ord('A'))
            
            # Country name পাওয়া
            try:
                c = pycountry.countries.get(alpha_2=country_code)
                country_name = c.name if c else country_code
            except:
                country_name = country_code
            
            return flag_emoji, country_name
    
    return None, None

# ===================== HELPERS =====================
def safe_execute(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            logging.error(traceback.format_exc())
    return wrapper

def mask_number(number_str):
    """255𝘚𝘩𝘶𝘷𝘰538 — দেশ কোড + 𝘚𝘩𝘶𝘷𝘰 + শেষ ৩ ডিজিট"""
    digits = re.sub(r'\D', '', str(number_str))
    if len(digits) <= 3:
        return digits + '𝘚𝘩𝘶𝘷𝘰'
    prefix = digits[:3]
    suffix = digits[-3:]
    return f"{prefix}𝘚𝘩𝘶𝘷𝘰{suffix}"

def clean_number(num):
    return "".join(filter(str.isdigit, str(num)))

COUNTRY_NAME_MAP = {
    "ivory coast": "CI", "ivory coast 2": "CI", "côte d'ivoire": "CI",
    "cote d'ivoire": "CI", "cote divoire": "CI", "guinea bissau": "GW",
    "guinea-bissau": "GW", "south korea": "KR", "north korea": "KP",
    "russia": "RU", "tanzania": "TZ", "syria": "SY", "iran": "IR",
    "vietnam": "VN", "laos": "LA", "moldova": "MD", "congo": "CG",
    "dr congo": "CD", "democratic republic of congress": "CD",
    "palestine": "PS", "kosovo": "XK", "taiwan": "TW", "cape verde": "CV",
    "east timor": "TL", "myanmar": "MM", "swaziland": "SZ", "eswatini": "SZ",
    "macau": "MO", "saint kitts": "KN", "saint lucia": "LC",
    "saint vincent": "VC", "micronesia": "FM", "curacao": "CW",
}

def get_flag(country_name):
    if not country_name:
        return ""
    name_lower = country_name.lower().strip()
    if name_lower in COUNTRY_NAME_MAP:
        alpha2 = COUNTRY_NAME_MAP[name_lower]
        return "".join(chr(ord(x) + 127397) for x in alpha2.upper())
    try:
        c = pycountry.countries.lookup(country_name)
        return "".join(chr(ord(x) + 127397) for x in c.alpha_2.upper())
    except Exception:
        pass
    try:
        results = pycountry.countries.search_fuzzy(country_name)
        if results:
            return "".join(chr(ord(x) + 127397) for x in results[0].alpha_2.upper())
    except Exception:
        pass
    return ""

def is_joined(user_id):
    try:
        for ch in REQUIRED_CHANNELS:
            m = bot.get_chat_member(ch, user_id)
            if m.status not in ["member", "administrator", "creator"]:
                return False
        return True
    except Exception:
        return False

def is_admin(uid):
    return str(uid) == ADMIN_ID

# ===================== MARKUPS =====================

def join_markup():
    return build_inline_keyboard([
        [make_button("📢 Join Channel 1", url="https://t.me/range_channele", style="primary")],
        [make_button("📢 Join Channel 2", url="https://t.me/tem_withh",     style="primary")],
        [make_button("✅ VERIFIED",        callback_data="verify_join",      style="success")],
    ])


# ===================== LIVE TRAFFIC DATA =====================
live_traffic = {
    "Facebook": {},
    "WhatsApp": {},
    "Instagram": {},
    "Telegram": {},
    "Others": {}
}
traffic_last_reset = time.time()

def get_country_name_from_api(country_code):
    """Country code থেকে country name পাওয়া"""
    try:
        c = pycountry.countries.get(alpha_2=country_code.upper())
        return c.name if c else country_code
    except:
        return country_code

def update_traffic(service_name, country, flag):
    """OTP আসলে traffic update করা - সঠিক implementation"""
    global traffic_last_reset, live_traffic
    
    # ১৫ মিনিট পর reset
    current_time = time.time()
    if current_time - traffic_last_reset > 900:
        # Reset করা
        for service in live_traffic:
            live_traffic[service] = {}
        traffic_last_reset = current_time
    
    # Service name validation
    if service_name not in live_traffic:
        service_name = "Others"
    
    # Country key তৈরি করা
    key = f"{flag} {country}"
    
    # Count বাড়ানো
    if key in live_traffic[service_name]:
        live_traffic[service_name][key] += 1
    else:
        live_traffic[service_name][key] = 1

def get_traffic_display():
    """LIVE TRAFFIC ডিসপ্লে তৈরি করা"""
    display = "📊 LIVE TRAFFIC\n\n"
    
    for service in ["Facebook", "WhatsApp", "Instagram", "Telegram", "Others"]:
        display += f"{service}\n"
        
        if not live_traffic[service]:
            display += "  (কোনো OTP নেই)\n"
        else:
            # Count অনুযায়ী sorting
            sorted_countries = sorted(
                live_traffic[service].items(),
                key=lambda x: x[1],
                reverse=True
            )
            for country_key, count in sorted_countries[:5]:  # শীর্ষ ৫টি
                display += f"  {country_key} [{count}]\n"
        
        display += "\n"
    
    return display

def traffic_menu_markup():
    """LIVE TRAFFIC মেসেজের জন্য buttons"""
    return build_inline_keyboard([
        [
            make_button("GET NUMBER", callback_data="get_number_menu", style="primary"),
            make_button("REFRESH", callback_data="refresh_traffic", style="success")
        ]
    ])

def main_markup(uid=None):
    """মেইন কীবোর্ড — সব নীল, লেআউট নতুন"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    def pb(text):
        b = types.KeyboardButton(text)
        b.__dict__["style"] = "primary"
        return b

    # GET NUMBER — একা উপরে
    markup.row(pb(BTN_GET_NUMBER))
    # LIVE TRAFFIC + 2FA CODE
    markup.row(pb(BTN_LIVE_TRAFFIC), pb(BTN_2FA))
    # ADMIN SUPPORT + BALANCE
    markup.row(pb(BTN_ADMIN_SUPPORT), pb(BTN_BALANCE))
    # PROFILE — একা নিচে
    markup.row(pb(BTN_PROFILE))
    # ADMIN PANEL — সবার নিচে একা (শুধু admin)
    if uid and is_admin(uid):
        b = types.KeyboardButton(BTN_ADMIN_PANEL)
        b.__dict__["style"] = "primary"
        markup.row(b)

    return markup

def service_menu_markup():
    """সার্ভিস মেনু - পাশাপাশি ২টা করে, ফ্যান্সি টেক্সট"""
    rows = []
    row = []
    for name in FIXED_SERVICES:
        label = SERVICE_LABELS.get(name, name)
        row.append(make_button(label, callback_data=f"sv_{name}", style="primary"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return build_inline_keyboard(rows)

def country_menu_markup(service_name):
    rows      = []
    countries = service_countries.get(service_name, [])
    if not countries:
        rows.append([make_button("⚠️ কোনো দেশ এড হয়নি", callback_data="noop", style="danger")])
    else:
        row = []
        for idx, c in enumerate(countries):
            flag  = get_flag(c["name"])
            label = f"{flag}   {c['name']}   " if flag else f"{c['name']}   "
            row.append(make_button(label, callback_data=f"ct_{service_name}__{idx}", style="success"))
            if len(row) == 2:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
    rows.append([make_button("🔙 Back", callback_data="back_to_services", style="danger")])
    return build_inline_keyboard(rows)

def number_assigned_markup(nums, countries, back_cb):
    """
    ✅ ২টা নাম্বার — প্রতিটা আলাদা বাটনে, flag+number সহ
    nums: list of up to 2 phone numbers
    countries: list of corresponding country names
    """
    rows = []
    for i, num in enumerate(nums):
        country = countries[i] if i < len(countries) else ""
        flag    = get_flag(country)
        label   = f"{flag}  +{num}"
        rows.append([make_button(label, style="primary", copy_text_val=f"+{num}")])
    rows.append([
        make_button("🔄 Change Number", callback_data="change_num", style="primary"),
        make_button("🔐 OTP GROUP",     url=GROUP_URL,              style="primary"),
    ])
    rows.append([make_button("🔙 BACK", callback_data=back_cb, style="danger")])
    return build_inline_keyboard(rows)

def service_info_markup(service_name, country, back_cb):
    """Country + Service — আলাদা নীল বাটন"""
    flag = get_flag(country)
    return build_inline_keyboard([
        [make_button(f"{flag} {country}", callback_data="noop", style="success")],
        [make_button(f"📲 {service_name.upper()}", callback_data="noop", style="success")],
        [make_button("🔙 BACK", callback_data=back_cb, style="danger")],
    ])

def otp_result_markup(otp, price=None, full_msg=None):
    rows = []
    # ১ম সারি: OTP বাটন (সবুজ)
    rows.append([make_button(otp, style="success", copy_text_val=otp)])
    # ২য় সারি: Add Tk বাটন (নীল)
    if price is not None:
        rows.append([make_button(f"Add {price:.2f} Tk", callback_data="noop", style="primary")])
    return build_inline_keyboard(rows)

def profile_markup():
    return build_inline_keyboard([
        [make_button("📩 OTP PRICE", callback_data="otp_price", style="success")],
        [make_button("❌ Cancel",    callback_data="back_to_main", style="danger")],
    ])

def balance_markup(balance):
    return build_inline_keyboard([
        [make_button(f"💶 WITHDRAW", callback_data="withdraw", style="danger")],
        [make_button("❌ Cancel",    callback_data="back_to_main", style="primary")],
    ])

def cancel_2fa_markup():
    return build_inline_keyboard([
        [make_button("❌ Cancel", callback_data="cancel_2fa", style="danger")],
    ])

def withdraw_select_method_markup(balance):
    return build_inline_keyboard([
        [
            make_button("💳 BKASH",  callback_data="bkash",  style="success"),
            make_button("💳 ROCKET", callback_data="rocket", style="primary"),
        ],
        [make_button("🔙 BACK", callback_data="back_balance", style="danger")],
    ])

def withdraw_cancel_markup():
    return build_inline_keyboard([
        [make_button("❌ Cancel", callback_data="cancel_withdraw", style="danger")],
    ])

def withdraw_confirm_markup():
    return build_inline_keyboard([
        [
            make_button("✅ Confirm", callback_data="confirm_withdraw", style="success"),
            make_button("❌ Cancel",  callback_data="cancel_withdraw",  style="danger"),
        ],
    ])

def withdraw_check_markup():
    return build_inline_keyboard([
        [make_button("📋 WITHDRAW CHECK", callback_data="withdraw_status", style="primary")],
    ])

def withdraw_refresh_markup():
    return build_inline_keyboard([
        [make_button("🔄 Refresh", callback_data="withdraw_refresh", style="primary")],
    ])

def admin_approve_markup(uid):
    return build_inline_keyboard([
        [
            make_button("✅ APPROVE", callback_data=f"approve_{uid}", style="success"),
            make_button("❌ REJECT",  callback_data=f"reject_{uid}",  style="danger"),
        ],
    ])

def try_again_markup():
    return build_inline_keyboard([
        [make_button("🔄 আবার চেষ্টা করুন", callback_data="change_num", style="danger")],
    ])

def otp_price_markup():
    return build_inline_keyboard([
        [make_button("🔙 BACK", callback_data="back_profile", style="primary")],
    ])

def admin_support_markup():
    return build_inline_keyboard([
        [make_button("ᯓᡣ𐭩 Admin Shuvo ᯓᡣ𐭩", url=f"tg://user?id={ADMIN_ID}", style="primary")],
    ])

# ========== ADMIN PANEL MARKUP ==========
def admin_panel_markup():
    return build_inline_keyboard([
        [
            make_button("🌍 Add Country",    callback_data="adm_add_country",  style="success"),
            make_button("🗑️ Del Country",    callback_data="adm_del_country",  style="danger"),
        ],
        [
            make_button("📨 User Message",   callback_data="adm_user_message", style="primary"),
            make_button("💰 Add Money",      callback_data="adm_add_money",    style="success"),
        ],
        [
            make_button("🗑️ Money Clear",    callback_data="adm_money_clear",  style="danger"),
            make_button("💰 Change Price",   callback_data="admin_change_price", style="success"),
        ],
        [
            make_button("👥 User Count",     callback_data="adm_user_count",   style="primary"),
            make_button("📊 All User Money", callback_data="adm_all_money",    style="primary"),
        ],
        [
            make_button("❌ Close",          callback_data="adm_close",        style="danger"),
        ],
    ])

def admin_del_country_service_markup():
    """Delete Country — সার্ভিস সিলেক্ট"""
    rows = []
    row  = []
    for name in FIXED_SERVICES:
        icon = SERVICE_ICONS.get(name, "📲")
        row.append(make_button(f"{icon} {name}", callback_data=f"adm_delcountry_{name}", style="primary"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([make_button("❌ Cancel", callback_data="adm_cancel", style="danger")])
    return build_inline_keyboard(rows)

def admin_del_country_list_markup(service_name):
    """ডিলিট করার জন্য দেশের লিস্ট"""
    rows      = []
    countries = service_countries.get(service_name, [])
    if not countries:
        rows.append([make_button("⚠️ কোনো দেশ নেই", callback_data="noop", style="danger")])
    else:
        row = []
        for idx, c in enumerate(countries):
            flag  = get_flag(c["name"])
            label = f"{flag}   {c['name']}   " if flag else f"{c['name']}   "
            row.append(make_button(label, callback_data=f"adm_delcountry_do_{service_name}__{idx}", style="danger"))
            if len(row) == 2:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
    rows.append([make_button("🔙 Back", callback_data="adm_del_country", style="primary")])
    return build_inline_keyboard(rows)

def admin_service_select_markup(action):
    rows = []
    row  = []
    for name in FIXED_SERVICES:
        icon = SERVICE_ICONS.get(name, "📲")
        row.append(make_button(f"{icon} {name}", callback_data=f"adm_svc_{action}_{name}", style="primary"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([make_button("❌ Cancel", callback_data="adm_cancel", style="danger")])
    return build_inline_keyboard(rows)

def admin_cancel_markup():
    return build_inline_keyboard([
        [make_button("❌ Cancel", callback_data="adm_cancel", style="danger")],
    ])

def admin_confirm_send_markup():
    return build_inline_keyboard([
        [
            make_button("📨 SEND",    callback_data="adm_confirm_send", style="success"),
            make_button("❌ Cancel",  callback_data="adm_cancel",       style="danger"),
        ],
    ])

# ===================== OTP GROUP MESSAGE HANDLER =====================
OTP_GROUP_ID = -1002670575248  # OTP Group চ্যানেল ID

@bot.message_handler(func=lambda m: m.chat.id == OTP_GROUP_ID, content_types=['text'])
def handle_otp_group_message(message):
    """OTP Group থেকে সরাসরি message পড়া এবং LIVE TRAFFIC update করা"""
    try:
        msg_text = message.text or ""
        
        # Flag emoji এবং country detect করা
        flag_emoji, detected_country = extract_country_from_otp_message(msg_text)
        
        if not flag_emoji or not detected_country:
            return  # Country detect না হলে ignore
        
        # Service detect করা (Facebook, WhatsApp, Instagram, Telegram)
        service_name = "Others"
        msg_lower = msg_text.lower()
        
        for svc in ["facebook", "whatsapp", "instagram", "telegram"]:
            if svc in msg_lower:
                service_name = svc.capitalize()
                break
        
        # ✅ LIVE TRAFFIC update করা
        update_traffic(service_name, detected_country, flag_emoji)
        
    except Exception as e:
        logging.error(f"OTP Group Handler Error: {str(e)}")

# ===================== /start =====================
@safe_execute
@bot.message_handler(commands=['start'])
def start(message):
    uid       = str(message.from_user.id)
    user_name = message.from_user.username or f"{message.from_user.first_name or 'User'} {message.from_user.last_name or ''}".strip()
    register_user(uid, user_name)
    user_names[uid] = user_name
    if not is_joined(message.from_user.id):
        join_msg = (
            "🔗 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 𝐕𝐞𝐫𝐢𝐟𝐢𝐜𝐚𝐭𝐢𝐨𝐧 𝐑𝐞𝐪𝐮𝐢𝐫𝐞𝐝\n\n"
            "📢 আপনাকে আমাদের চ্যানেলে Join করতে হবে:\n\n"
            "✨ এই বট ব্যবহার করতে নিচের দুইটি চ্যানেলে Join করুন।\n\n"
            "✅ Join করার পর VERIFIED বাটনে চাপুন।"
        )
        bot.send_message(
            message.chat.id,
            join_msg,
            reply_markup=join_markup()
        )
        return
    welcome_text = (
        "👋𓆩𓆩WELCOME TO OTP SERViCE𓆪𓆪\n"
        " ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅\n\n"
        "🤖 WELCOME TO TEAM WITH 3.0 \n\n"
        " ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅\n\n"
        "♾️ POWERED BY Shuvoᯓᡣ𐭩"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_markup(uid))

# ===================== ADMIN COMMANDS =====================
@bot.message_handler(commands=['add'])
def add_service(message):
    if not is_admin(message.from_user.id):
        return
    raw   = message.text.replace("/add", "", 1).strip()
    parts = None
    if raw.count("|") >= 2:
        parts = [p.strip() for p in raw.split("|", 2)]
    elif raw.count("|") == 1 and ":" in raw.split("|", 1)[1]:
        left, right  = raw.split("|", 1)
        country, rid = right.split(":", 1)
        parts        = [left.strip(), country.strip(), rid.strip()]
    elif raw.count(":") >= 2:
        parts = [p.strip() for p in raw.split(":", 2)]
    else:
        bot.reply_to(message, "⚠️ সঠিক ফরম্যাট:\n/add Facebook|Guinea|2246545"); return
    if len(parts) < 3 or not all(parts):
        bot.reply_to(message, "⚠️ সঠিক ফরম্যাট:\n/add Facebook|Guinea|2246545"); return
    service_name, country_name, rid = parts[0], parts[1], parts[2]
    if service_name not in FIXED_SERVICES:
        bot.reply_to(message, f"❌ '{service_name}' সার্ভিস নেই।"); return
    countries = service_countries[service_name]
    found = False
    for c in countries:
        if c["name"].lower() == country_name.lower():
            c["rid"] = rid; found = True; break
    if not found:
        countries.append({"name": country_name, "rid": rid})
    save_countries_to_firebase(service_name)
    bot.reply_to(message, f"✅ Added!\n🌍 {service_name} → {country_name}\n🔢 {rid}")

@bot.message_handler(commands=['del'])
def del_service(message):
    if not is_admin(message.from_user.id):
        return
    text = message.text.replace("/del", "", 1).strip()
    if "|" in text:
        service_name, country_query = [p.strip() for p in text.split("|", 1)]
        if service_name not in FIXED_SERVICES:
            bot.reply_to(message, "❌ সার্ভিসটি পাওয়া যায়নি।"); return
        matched = [c for c in service_countries[service_name]
                   if country_query.lower() in c["name"].lower() or c["name"].lower() in country_query.lower()]
        if matched:
            service_countries[service_name] = [c for c in service_countries[service_name] if c not in matched]
            save_countries_to_firebase(service_name)
            bot.reply_to(message, f"✅ {service_name} → {', '.join(c['name'] for c in matched)} ডিলিট হয়েছে।")
        else:
            bot.reply_to(message, "❌ দেশটি পাওয়া যায়নি।")
    else:
        service_name = text
        if service_name in FIXED_SERVICES:
            service_countries[service_name] = []
            save_countries_to_firebase(service_name)
            bot.reply_to(message, f"✅ {service_name}-এর সব দেশ ডিলিট হয়েছে।")
        else:
            bot.reply_to(message, "❌ সার্ভিসটি পাওয়া যায়নি।")

@bot.message_handler(commands=['price'])
def price_command(message):
    current_price = get_otp_price_from_firebase()
    bot.send_message(
        message.chat.id,
        f"💰 𝐓𝐨𝐝𝐚𝐲 𝐎𝐓𝐏 𝐏𝐫𝐢𝐜𝐞\n\n📌 𝟏 𝐎𝐓𝐏 = {current_price:.2f} 𝐓𝐊",
        reply_markup=otp_price_markup()
    )

@bot.message_handler(commands=['addmoney'])
def addmoney_command(message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 3:
        bot.reply_to(message, "⚠️ /addmoney [user_id] [amount]"); return
    uid, amount = parts[1], float(parts[2])
    new_bal = update_firebase_balance(uid, amount)
    bot.reply_to(message, f"✅ ব্যালেন্স আপডেট!\n👤 ID: {uid}\n💰 নতুন: {new_bal} TK")

@bot.message_handler(commands=['delbalance'])
def del_balance_cmd(message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) == 1:
        bot.reply_to(message, "⚠️ /delbalance [user_id] [amount]\n/delbalance [user_id]\n/delbalance all"); return
    if parts[1].lower() == "all":
        clear_all_balances()
        bot.reply_to(message, "✅ সব ব্যালেন্স 0 করা হয়েছে।"); return
    uid = parts[1]
    if len(parts) == 2:
        set_firebase_balance(uid, 0)
        bot.reply_to(message, f"✅ {uid} এর ব্যালেন্স 0।")
    elif len(parts) == 3:
        try:
            amount  = float(parts[2])
            current = get_firebase_balance(uid)
            new_bal = set_firebase_balance(uid, max(0, current - amount))
            bot.reply_to(message, f"✅ কাটা: {amount} TK\n💰 বাকি: {new_bal} TK")
        except Exception:
            bot.reply_to(message, "❌ সংখ্যা দিন।")

@bot.message_handler(commands=['setprice'])
def setprice_command(message):
    """OTP প্রাইস সেট করা"""
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 2:
        current_price = get_otp_price_from_firebase()
        bot.reply_to(
            message,
            f"💰 নতুন OTP মূল্য কত হবে?\n\n"
            f"📝 উদাহরণ: /setprice 0.50\n\n"
            f"বর্তমান মূল্য: {current_price:.2f} টাকা"
        )
        return
    try:
        new_price = float(parts[1])
        if new_price < 0:
            bot.reply_to(message, "❌ মূল্য negative হতে পারে না।")
            return
        set_otp_price_to_firebase(new_price)
        bot.reply_to(
            message,
            f"✅ OTP মূল্য সেট করা হয়েছে!\n\n"
            f"💰 নতুন মূল্য: {new_price:.2f} টাকা\n"
            f"📝 প্রতিটি OTP-তে ইউজার এই পরিমাণ পাবে।"
        )
    except ValueError:
        bot.reply_to(message, "❌ ভুল সংখ্যা। যেমন: /setprice 0.50")

@bot.message_handler(commands=['setprice'])
def setprice_command(message):
    """OTP প্রাইস সেট করা"""
    global admin_otp_price
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(
            message,
            f"💰 নতুন OTP মূল্য কত হবে?\n\n"
            f"📝 উদাহরণ: 0.50 অথবা 1.25\n\n"
            f"বর্তমান মূল্য: {admin_otp_price:.2f} টাকা"
        )
        return
    try:
        new_price = float(parts[1])
        if new_price < 0:
            bot.reply_to(message, "❌ মূল্য negative হতে পারে না।")
            return
        admin_otp_price = new_price
        _fb_put("/admin/otp_price", new_price)
        bot.reply_to(
            message,
            f"✅ OTP মূল্য সেট করা হয়েছে!\n\n"
            f"💰 নতুন মূল্য: {new_price:.2f} টাকা\n"
            f"📝 প্রতিটি OTP-তে ইউজার এই পরিমাণ পাবে।"
        )
    except ValueError:
        bot.reply_to(message, "❌ ভুল সংখ্যা। যেমন: /setprice 0.50")

@bot.message_handler(commands=['user'])
def count_users(message):
    if is_admin(message.from_user.id):
        load_all_users_from_firebase()
        bot.reply_to(message, f"👥 মোট ইউজার: {len(users)}")

@bot.message_handler(commands=['user_info'])
def user_info_cmd(message):
    if not is_admin(message.from_user.id):
        return
    load_all_users_from_firebase()
    if not users:
        bot.reply_to(message, "❌ কোনো ইউজার নেই!"); return
    info_text = "╔════════════════════╗\n👥 সকল ইউজার\n╚════════════════════╝\n\n"
    for idx, uid in enumerate(sorted(users.keys()), 1):
        balance = get_firebase_balance(uid)
        uname   = user_names.get(uid, "Unknown")
        info_text += f"#{idx} | 🆔 {uid} | 👤 {uname} | 💰 {balance:.2f} TK\n"
    for i in range(0, len(info_text), 4000):
        bot.send_message(message.chat.id, info_text[i:i+4000])

@bot.message_handler(commands=['send'])
def broadcast(message):
    if not is_admin(message.from_user.id):
        return
    text = message.text.replace("/send", "", 1).strip()
    if not text:
        bot.reply_to(message, "⚠️ /send [message]"); return
    load_all_users_from_firebase()
    count = failed = 0
    for uid in list(users.keys()):
        try:
            bot.send_message(int(str(uid)), text); count += 1; time.sleep(0.05)
        except Exception:
            failed += 1
    bot.reply_to(message, f"✅ {count} জনকে পাঠানো হয়েছে।\n❌ {failed} জন ব্যর্থ।")

def flag_to_country_code(flag):
    """Flag emoji থেকে country code বের করা"""
    if not flag or len(flag) < 2:
        return None
    try:
        # Flag emoji = 2 regional indicator symbols
        chars = list(flag)
        if len(chars) >= 2:
            code1 = ord(chars[0]) - 0x1F1E6
            code2 = ord(chars[1]) - 0x1F1E6
            if 0 <= code1 <= 25 and 0 <= code2 <= 25:
                return chr(code1 + ord('A')) + chr(code2 + ord('A'))
    except:
        pass
    return None

def get_country_name_from_code(code):
    """Country code থেকে full country name বের করা"""
    if not code or len(code) != 2:
        return code
    try:
        c = pycountry.countries.get(alpha_2=code.upper())
        return c.name if c else code
    except:
        return code

# ===================== LIVE TRAFFIC DISPLAY =====================
@bot.message_handler(commands=['strd'])
def strd_command(message):
    uid = str(message.from_user.id)
    if not is_admin(uid):
        return
    welcome_text = (
        "👋𓆩𓆩WELCOME TO OTP SERViCE𓆪𓆪\n"
        " ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅\n\n"
        "🤖 WELCOME TO TEAM WITH 3.0 \n\n"
        " ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅\n\n"
        "♾️ POWERED BY Shuvoᯓᡣ𐭩"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_markup(uid))
    return
    chat_id  = message.chat.id
    nums     = user_numbers.get(chat_id, [])
    if not nums:
        bot.reply_to(message, "❌ আগে একটি নাম্বার নিন!"); return
    if strd_running.get(chat_id):
        bot.reply_to(message, "⏳ ইতিমধ্যে OTP খোঁজা চলছে!"); return
    search_msg = bot.send_message(chat_id, "🔍 OTP SEARCHING (∞)...\n⏳ Number change না হওয়া পর্যন্ত চালু...")
    threading.Thread(target=infinite_otp_search, args=(chat_id, list(nums), search_msg.message_id), daemon=True).start()

# ===================== ZENEX OTP FETCH =====================
def get_zenex_otps():
    """ZENEX থেকে OTP fetch করছি /v1/numsuccess/info endpoint থেকে"""
    try:
        r = requests.get(
            f"{ZENEX_BASE_URL}/v1/numsuccess/info",
            headers=ZENEX_HEADERS,
            timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("meta", {}).get("status") == "success" and data.get("data", {}).get("otps"):
                return data.get("data", {}).get("otps", [])
    except Exception as e:
        logging.error(f"ZENEX OTP fetch error: {e}")
    return []

def get_nexus_otp(api_id):
    """Backward compatibility - ZENEX এ convert হয়েছে"""
    try:
        otps = get_zenex_otps()
        if otps and len(otps) > 0:
            return otps[0].get("otp", "")
    except:
        pass
    return None

def infinite_otp_search(chat_id, start_numbers, search_msg_id):
    strd_running[chat_id] = True
    active_msg_id = search_msg_id
    # ✅ init used sets
    if chat_id not in used_otps:
        used_otps[chat_id] = []
    if chat_id not in global_used_otps:
        global_used_otps[chat_id] = set()
    try:
        while strd_running.get(chat_id):
            current_nums = user_numbers.get(chat_id, [])
            if not isinstance(current_nums, list):
                current_nums = [current_nums] if current_nums else []
            # ✅ নাম্বার বদলে গেলে নতুন নাম্বারে continue — বন্ধ না
            if current_nums and set(current_nums) != set(start_numbers):
                start_numbers = list(current_nums)
                # used_otps রিসেট করো নতুন নাম্বারের জন্য
                used_otps[chat_id] = []
                try:
                    nums_str = " | ".join(f"+{n}" for n in start_numbers)
                    active_msg_id = bot.send_message(chat_id, f"🔄 নতুন নাম্বারে OTP খোঁজা শুরু: {nums_str}").message_id
                except Exception:
                    pass
            if not current_nums:
                time.sleep(2); continue
            try:
                panel = user_panel_for_otp.get(chat_id, "stex")
                
                if panel == "nexus":
                    # NEXUS থেকে OTP নিচ্ছি - /api/v1/numbers/{id} endpoint থেকে
                    api_ids = user_ranges.get(chat_id, [])
                    if api_ids and isinstance(api_ids, list):
                        for api_id in api_ids:
                            otp = get_nexus_otp(api_id)
                            if otp:
                                uid_str = str(chat_id)
                                current_price = get_otp_price_from_firebase()
                                new_bal = update_firebase_balance(uid_str, current_price)
                                
                                received_otps[chat_id] = otp
                                service = user_service.get(chat_id, "Others")
                                matched_num = current_nums[0] if current_nums else "?"
                                
                                country_list2  = user_countries.get(chat_id, [])
                                detected_c2    = country_list2[0] if country_list2 else None
                                flag2          = get_flag(detected_c2) if detected_c2 else "🌍"
                                full_msg_nexus = item.get("message", otp)
                                text = (
                                    f"╔━━━━━━━━━━━━━━━╗\n"
                                    f"║{flag2}  {matched_num}    #{service.upper()}║\n"
                                    f"╚━━━━━━━━━━━━━━━╝\n\n"
                                    f"<blockquote>{full_msg_nexus}</blockquote>"
                                )
                                kb = otp_result_markup(otp, price=current_price)
                                try:
                                    bot.edit_message_text(text, chat_id, active_msg_id, reply_markup=kb, parse_mode="HTML")
                                except Exception:
                                    try:
                                        bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")
                                    except Exception:
                                        pass
                                try:
                                    active_msg_id = bot.send_message(chat_id, "🔍 Next OTP SEARCHING (∞)...\n⏳ Waiting...").message_id
                                except Exception:
                                    pass
                                break
                else:
                    # STEX থেকে OTP নিচ্ছি
                    r = session.get(f"{BASE_URL}/success-otp", timeout=10)
                    data = r.json()
                    if data.get("meta", {}).get("code") == 200:
                        for item in data.get("data", {}).get("otps", []):
                            msg_id  = item.get("otp_id") or item.get("id")
                            api_num = clean_number(item.get("number", ""))
                        if msg_id in global_used_otps.get(chat_id, set()):
                            continue
                        # check against all current numbers
                        matched_num = None
                        matched_idx = None
                        for idx, num in enumerate(current_nums):
                            cur = clean_number(num)
                            if api_num in cur or cur in api_num:
                                matched_num = num; matched_idx = idx; break
                        if not matched_num:
                            continue
                        if msg_id in used_otps.get(chat_id, []):
                            continue
                        if chat_id not in used_otps:
                            used_otps[chat_id] = []
                        if chat_id not in global_used_otps:
                            global_used_otps[chat_id] = set()
                        used_otps[chat_id].append(msg_id)
                        global_used_otps[chat_id].add(msg_id)
                        otp = extract_otp(item.get("message", ""), matched_num)
                        if otp is None:
                            continue
                        
                            continue
                        
                        uid_str = str(chat_id)
                        # ✅ Firebase থেকে dynamic price পড়ুন
                        current_price = get_otp_price_from_firebase()
                        new_bal = update_firebase_balance(uid_str, current_price)
                        
                        # ✅ নাম্বার কেনার সময়ই যে country সেভ করা হয়েছিল সেটা থেকে flag বের করা
                        # (SMS টেক্সটে flag emoji খোঁজা ভুল ছিল, কারণ SMS-এ কখনো flag emoji থাকে না)
                        country_list = user_countries.get(chat_id, [])
                        detected_country = country_list[matched_idx] if (matched_idx is not None and matched_idx < len(country_list)) else None
                        flag_emoji = get_flag(detected_country) if detected_country else None
                        
                        # ✅ LIVE TRAFFIC আপডেট করা
                        service = user_service.get(chat_id, "Others")
                        if flag_emoji and detected_country:
                            update_traffic(service, detected_country, flag_emoji)
                        
                        received_otps[chat_id] = otp
                        # Display এ use করার জন্য
                        display_flag = flag_emoji if flag_emoji else "🌍"
                        display_country = detected_country if detected_country else "Unknown"
                        full_msg = item.get("message", "")
                        text = (
                            f"╔━━━━━━━━━━━━━━━╗\n"
                            f"║{display_flag}  {matched_num}    #{service.upper()}║\n"
                            f"╚━━━━━━━━━━━━━━━╝\n\n"
                            f"<blockquote>{full_msg}</blockquote>"
                        )
                        kb = otp_result_markup(otp, price=current_price)
                        try:
                            bot.edit_message_text(text, chat_id, active_msg_id, reply_markup=kb, parse_mode="HTML")
                        except Exception:
                            try:
                                bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")
                            except Exception:
                                pass
                        try:
                            active_msg_id = bot.send_message(chat_id, "🔍 Next OTP SEARCHING (∞)...\n⏳ Waiting...").message_id
                        except Exception:
                            pass
            except Exception:
                pass
            time.sleep(2)
    finally:
        strd_running[chat_id] = False

# ===================== AUTO OTP — ২ নাম্বারে খোঁজে =====================
def auto_check_otp(chat_id, phone_numbers, number_msg_id=None, search_msg_id=None, gen=None):
    """phone_numbers: list of up to 2 numbers"""
    if otp_running.get(chat_id):
        return
    otp_running[chat_id] = True
    first_otp_found = False
    if chat_id not in used_otps:
        used_otps[chat_id] = []
    if chat_id not in global_used_otps:
        global_used_otps[chat_id] = set()
    consecutive_errors = 0
    start_time = time.time()

    while True:
        try:
            # ✅ Change Number চাপার সাথে সাথেই এই থ্রেডের generation পুরনো হয়ে গেলে
            # সাথে সাথে বন্ধ হয়ে যাবে — পুরনো নাম্বারের OTP আর কখনো পাঠাবে না
            if gen is not None and otp_generation.get(chat_id) != gen:
                otp_running[chat_id] = False
                return
            # ✅ ৫ মিনিট পরে — number message ডিলিট করে Time Expired দেখাও
            if time.time() - start_time > 1800:
                otp_running[chat_id] = False
                try:
                    kb = build_inline_keyboard([[
                        make_button("📱 GET NUMBER", callback_data="get_number_menu", style="primary")
                    ]])
                    # number message ডিলিট করো
                    if number_msg_id:
                        try:
                            bot.delete_message(chat_id, number_msg_id)
                        except Exception:
                            pass
                    # Time Expired message পাঠাও
                    bot.send_message(chat_id, "⏰ Time Expired!", reply_markup=kb)
                except Exception:
                    pass
                return
            # নাম্বার বদলে গেলে বন্ধ
            current_nums = user_numbers.get(chat_id, [])
            if not current_nums:
                otp_running[chat_id] = False; return
            # যদি কোনো নাম্বারই phone_numbers এ না থাকে
            if not any(n in current_nums for n in phone_numbers):
                otp_running[chat_id] = False; return

            panel = user_panel_for_otp.get(chat_id, "stex")

            if panel == "nexus":
                # ✅ NEXUS নাম্বারের OTP /api/v1/numbers/{id} থেকে চেক করা হচ্ছে
                api_ids = user_api_ids.get(chat_id, [])
                try:
                    for idx, api_id in enumerate(api_ids):
                        if not api_id:
                            continue
                        otp_raw = get_nexus_otp(api_id)
                        if not otp_raw:
                            continue

                        matched_num = phone_numbers[idx] if idx < len(phone_numbers) else (current_nums[0] if current_nums else "?")
                        otp = extract_otp(otp_raw, matched_num)
                        if otp is None:
                            continue

                        # ✅ শুধু এই নির্দিষ্ট OTP-টা আগে পাঠানো হয়েছে কিনা চেক করছি
                        # (api_id ব্লক করছি না, তাই একই নাম্বারে নতুন/দ্বিতীয় OTP আসলেও সেটা পাঠানো হবে)
                        sent_key = f"{api_id}:{otp}"
                        if sent_key in used_otps.get(chat_id, []):
                            continue
                        used_otps[chat_id].append(sent_key)
                        global_used_otps[chat_id].add(sent_key)

                        uid_str = str(chat_id)
                        current_price = get_otp_price_from_firebase()
                        new_bal = update_firebase_balance(uid_str, current_price)

                        country_list     = user_countries.get(chat_id, [])
                        detected_country = country_list[idx] if idx < len(country_list) else None
                        flag_emoji       = get_flag(detected_country) if detected_country else None
                        service          = user_service.get(chat_id, "Others")
                        if flag_emoji and detected_country:
                            update_traffic(service, detected_country, flag_emoji)

                        received_otps[chat_id] = otp
                        display_flag    = flag_emoji if flag_emoji else "🌍"
                        display_country = detected_country if detected_country else "Unknown"
                        tag             = get_service_tag(service)
                        full_msg        = item.get("message", "")
                        text = (
                            make_box([f"{display_flag} {matched_num} {tag}"]) +
                            f"\n\n<blockquote>{full_msg}</blockquote>"
                        )
                        kb = otp_result_markup(otp, price=current_price)
                        if not first_otp_found and search_msg_id:
                            try:
                                bot.edit_message_text(text, chat_id, search_msg_id, reply_markup=kb, parse_mode="HTML")
                                first_otp_found = True
                            except Exception:
                                try:
                                    bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")
                                    first_otp_found = True
                                except Exception:
                                    pass
                        else:
                            try:
                                bot.send_message(chat_id, text, reply_markup=kb)
                            except Exception:
                                pass
                    consecutive_errors = 0
                except Exception:
                    consecutive_errors += 1
                time.sleep(3 if consecutive_errors >= 5 else 1)
                continue

            try:
                r = session.get(f"{BASE_URL}/success-otp", timeout=15)
                r.raise_for_status()
                data = r.json()
                consecutive_errors = 0
                if data.get("meta", {}).get("code") == 200:
                    for item in data.get("data", {}).get("otps", []):
                        api_num = clean_number(item.get("number", ""))
                        # ২ নাম্বারের যেকোনো একটায় match করলেই চলবে
                        matched_num = None
                        matched_idx = None
                        for idx, num in enumerate(phone_numbers):
                            my_num = clean_number(num)
                            if api_num and my_num and (api_num in my_num or my_num in api_num):
                                matched_num = num; matched_idx = idx; break
                        if not matched_num:
                            continue
                        msg_id = item.get("otp_id") or item.get("id")
                        if not msg_id:
                            continue
                        if msg_id in global_used_otps[chat_id]:
                            continue
                        if msg_id in used_otps[chat_id]:
                            continue
                        used_otps[chat_id].append(msg_id)
                        global_used_otps[chat_id].add(msg_id)
                        otp = extract_otp(item.get("message", ""), matched_num)
                        if otp is None:
                            continue
                        
                            continue
                        
                        uid_str = str(chat_id)
                        # ✅ Firebase থেকে dynamic price পড়ুন
                        current_price = get_otp_price_from_firebase()
                        new_bal = update_firebase_balance(uid_str, current_price)
                        
                        # ✅ নাম্বার কেনার সময়ই যে country সেভ করা হয়েছিল সেটা থেকে flag বের করা
                        # (SMS টেক্সটে flag emoji খোঁজা ভুল ছিল, কারণ SMS-এ কখনো flag emoji থাকে না)
                        country_list = user_countries.get(chat_id, [])
                        detected_country = country_list[matched_idx] if (matched_idx is not None and matched_idx < len(country_list)) else None
                        flag_emoji = get_flag(detected_country) if detected_country else None
                        
                        # ✅ LIVE TRAFFIC আপডেট করা
                        service = user_service.get(chat_id, "Others")
                        if flag_emoji and detected_country:
                            update_traffic(service, detected_country, flag_emoji)
                        
                        received_otps[chat_id] = otp
                        display_flag    = flag_emoji if flag_emoji else "🌍"
                        display_country = detected_country if detected_country else "Unknown"
                        tag             = get_service_tag(service)
                        full_msg2       = item.get("message", "")
                        text = (
                            make_box([f"{display_flag} {matched_num} {tag}"]) +
                            f"\n\n<blockquote>{full_msg2}</blockquote>"
                        )
                        kb = otp_result_markup(otp, price=current_price)
                        if not first_otp_found and search_msg_id:
                            try:
                                bot.edit_message_text(text, chat_id, search_msg_id, reply_markup=kb, parse_mode="HTML")
                                first_otp_found = True
                            except Exception:
                                try:
                                    bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")
                                    first_otp_found = True
                                except Exception:
                                    pass
                        else:
                            try:
                                bot.send_message(chat_id, text, reply_markup=kb)
                            except Exception:
                                pass
            except requests.exceptions.Timeout:
                consecutive_errors += 1
            except requests.exceptions.RequestException:
                consecutive_errors += 1
            except Exception:
                consecutive_errors += 1
            time.sleep(3 if consecutive_errors >= 5 else 1)
        except Exception:
            time.sleep(2)

# ===================== NUMBER PROCESSING — ২টা নাম্বার =====================
# ===================== NEXUS SERVICE MAPPING =====================
def get_nexus_sid(service_name):
    mapping = {"facebook": "fb", "whatsapp": "wa", "telegram": "tg", "instagram": "ig", "imo": "imo", "tiktok": "tiktok"}
    return mapping.get(service_name.lower(), service_name.lower())

def process_number(message, edit_msg=None, service_name="Unknown", rid=None):
    chat_id = message.chat.id
    if rid is None:
        rid = user_ranges.get(chat_id) or message.text

    # ✅ নতুন generation — এর ফলে আগের auto_check_otp থ্রেড (যদি এখনো চলে) সাথে সাথে থেমে যাবে
    otp_generation[chat_id] = otp_generation.get(chat_id, 0) + 1
    my_generation = otp_generation[chat_id]

    loading_text = "🔄 FETCHING NEW NUMBER...\n⏳ PLEASE WAIT..."
    empty_kb = types.InlineKeyboardMarkup()
    if edit_msg:
        try:
            bot.edit_message_text(loading_text, chat_id, edit_msg.message_id, reply_markup=empty_kb)
            status_id = edit_msg.message_id
        except Exception:
            status_id = bot.send_message(chat_id, loading_text).message_id
    else:
        status_id = bot.send_message(chat_id, loading_text).message_id

    # Panel check করছি first
    panel = "stex"  # default
    if service_name in service_countries:
        for c in service_countries[service_name]:
            if c.get("rid") == rid:
                panel = c.get("panel", "stex")
                break

    # ✅ আগে যদি NEXUS-এর পুরনো নাম্বার (id) থাকে, সেগুলো রিলিজ/ক্যান্সেল করে দাও
    # (এটা ছাড়া Change Number চাপলে একই রেঞ্জ থেকে নতুন নাম্বার নাও আসতে পারে,
    # কারণ পুরনো নাম্বারটা তখনও "active" থেকে যায়)
    old_api_ids = user_api_ids.get(chat_id, [])
    if old_api_ids:
        for old_id in old_api_ids:
            if not old_id:
                continue
            try:
                requests.delete(f"{NEXUS_BASE_URL}/numbers/{old_id}", headers=NEXUS_HEADERS, timeout=10)
            except Exception:
                pass
        # ✅ রিলিজ হওয়ার পর নেক্সাস সার্ভারকে একটু সময় দিচ্ছি, নাহলে সাথে সাথে নতুন
        # নাম্বার চাইলে মাঝে মাঝে "already active" ধরনের এরর দিয়ে ব্যর্থ হচ্ছিল
        time.sleep(1.5)

    # Panel save করছি OTP এর জন্য
    user_panel_for_otp[chat_id] = panel

    nums = []
    countries = []
    api_ids = []

    if panel == "nexus":
        # ZENEX থেকে (NEXUS এর জায়গায় এখন ZENEX)
        for attempt in range(8):
            try:
                r = requests.post(
                    f"{ZENEX_BASE_URL}/v1/getnum",
                    headers=ZENEX_HEADERS,
                    json={"range": rid, "is_national": False, "remove_plus": False},
                    timeout=15
                )
                data = r.json()
                if data.get("meta", {}).get("status") == "success" and data.get("data"):
                    num = str(data.get("data", {}).get("full_number", "")).replace("+", "")
                    country = data.get("data", {}).get("country", "Unknown")
                    api_id = data.get("data", {}).get("nid", num)  # ZENEX uses NID
                    if num not in nums:
                        nums.append(num)
                        countries.append(country)
                        api_ids.append(api_id)
                    if len(nums) >= 2:
                        break
                else:
                    # ✅ ডিবাগ লগ — কেন ZENEX নাম্বার দিচ্ছে না সেটা Render Logs-এ দেখা যাবে
                    logging.error(f"ZENEX number fetch failed (attempt {attempt}): {data}")
                    time.sleep(0.3)
            except Exception:
                logging.error(traceback.format_exc())
                time.sleep(0.3)
    else:
        # STEX থেকে
        for attempt in range(5):
            try:
                r = session.post(f"{BASE_URL}/getnum", json={"rid": rid}, timeout=15)
                data = r.json()
                if data.get("meta", {}).get("code") == 200:
                    full_num = str(data["data"]["full_number"]).replace("+", "")
                    country = data["data"].get("country", "Unknown")
                    if full_num not in nums:
                        nums.append(full_num)
                        countries.append(country)
                    if len(nums) >= 2:
                        break
                else:
                    time.sleep(0.3)
            except Exception:
                time.sleep(0.3)

    if not nums:
        try:
            bot.edit_message_text("⚠️ Number out of stock.\n🔄 Try again later.", chat_id, status_id, reply_markup=try_again_markup())
        except Exception:
            pass
        return

    # State সেট করো
    otp_running[chat_id]    = False
    strd_running[chat_id]   = False
    user_numbers[chat_id]   = nums
    user_countries[chat_id] = countries
    user_ranges[chat_id]    = rid
    user_service[chat_id]   = service_name
    user_api_ids[chat_id]   = api_ids if panel == "nexus" else []
    received_otps[chat_id]  = None
    # ✅ used_otps ইচ্ছাকৃতভাবে রিসেট করা হচ্ছে না — Change Number করলেও আগে
    # পাঠানো OTP-গুলোর memory থেকে যাবে, তাই পুরনো/লেগে থাকা thread থাকলেও
    # সেটা পুরনো OTP আবার পাঠাতে বা টাকা যোগ করতে পারবে না।

    back_cb      = f"back_to_country_{service_name}" if service_name in FIXED_SERVICES else "back_to_services"
    country_show = countries[0] if countries else "Unknown"
    flag         = get_flag(country_show)

    # ✅ শুধু "WAITING FOR OTP..." — এখানে বক্স লাগবে না (বক্স শুধু OTP আসার সময় দেখাবে)
    msg_text = "⏳ WAITING FOR OTP..."
    kb = build_inline_keyboard(
        # নাম্বার বাটনগুলো
        [[make_button(f"{get_flag(countries[i] if i < len(countries) else '')}  +{num}", style="primary", copy_text_val=f"+{num}")] for i, num in enumerate(nums)]
        +
        # country আর service আলাদা বাটন
        [[make_button(f"{flag} {country_show}", callback_data="noop", style="success"),
          make_button(f"📲 {service_name.upper()}", callback_data="noop", style="success")]]
        +
        [
            [
                make_button("🔄 Change Number", callback_data="change_num", style="primary"),
                make_button("🔐 OTP GROUP",     url=GROUP_URL,              style="primary"),
            ],
            [make_button("🔙 BACK", callback_data=back_cb, style="danger")],
        ]
    )

    try:
        bot.edit_message_text(msg_text, chat_id, status_id, reply_markup=kb)
    except Exception:
        bot.send_message(chat_id, msg_text, reply_markup=kb)

    threading.Thread(target=auto_check_otp, args=(chat_id, list(nums), status_id, None, my_generation), daemon=True).start()

# ===================== TEXT HANDLER =====================
@safe_execute
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    uid       = str(message.from_user.id)
    user_name = message.from_user.username or f"{message.from_user.first_name or 'User'} {message.from_user.last_name or ''}".strip()
    register_user(uid, user_name)
    user_names[uid] = user_name

    if not is_joined(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ দয়া করে চ্যানেলে জয়েন করুন।", reply_markup=join_markup())
        return

    txt = message.text

    if uid in admin_state and admin_state[uid].get("step"):
        handle_admin_state(message, uid, txt)
        return

    if txt == "⚙️ ADMIN PANEL":
        if not is_admin(uid):
            return
        bot.send_message(
            message.chat.id,
            "╔════════════════════╗\n      ⚙️ ADMIN PANEL\n╚════════════════════╝",
            reply_markup=admin_panel_markup()
        )
        return

    if txt == BTN_GET_NUMBER:
        bot.send_message(message.chat.id, SELECT_SERVICE_TEXT, reply_markup=service_menu_markup())

    elif txt == BTN_2FA:
        msg = bot.send_message(
            message.chat.id,
            "🔐 Enter your 2FA code.\n"
            "🔑 Example: JBSWY3DPEHPK3PXP",
            reply_markup=cancel_2fa_markup()
        )
        bot.register_next_step_handler(msg, process_2fa)

    elif txt == BTN_PROFILE:
        balance   = get_firebase_balance(uid)
        today_str = str(date.today())
        if today_date.get(uid) != today_str:
            t_earn  = 0.0
            t_count = 0
        else:
            t_earn  = today_earn.get(uid, 0.0)
            t_count = today_otp_count.get(uid, 0)
        msg_text = (
            " 👤  𝐘𝐎𝐔𝐑 𝐏𝐑𝐎𝐅𝐈𝐋𝐄\n\n"
            f"💸 𝐓𝐨𝐝𝐚𝐲 𝐄𝐚𝐫𝐧 : {t_earn:.2f} 𝐓𝐊\n"
            f"📩 𝐓𝐨𝐝𝐚𝐲 𝐎𝐓𝐏 : {t_count}\n\n"
            f"🆔 𝐈𝐃 : {uid}\n"
            f"💰 𝐁𝐚𝐥𝐚𝐧𝐜𝐞 : {balance:.2f} 𝐓𝐊\n"
            "✅ 𝐒𝐭𝐚𝐭𝐮𝐬 : 𝐀𝐂𝐓𝐈𝐕𝐄"
        )
        bot.send_message(message.chat.id, msg_text, reply_markup=profile_markup())

    elif txt == BTN_BALANCE:
        balance  = get_firebase_balance(uid)
        msg_text = (
            "💳 𝐘𝐎𝐔𝐑 𝐁𝐀𝐋𝐀𝐍𝐂𝐄\n\n"
            f"💰 𝐁𝐀𝐋𝐀𝐍𝐂𝐄 {balance:.2f} 𝐓𝐊\n\n"
            "✨ 𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞 𝐁𝐚𝐥𝐚𝐧𝐜𝐞"
        )
        bot.send_message(message.chat.id, msg_text, reply_markup=balance_markup(balance))

    elif txt == BTN_LIVE_TRAFFIC:
        traffic_intro = "📡 𝐋𝐢𝐯𝐞 𝐓𝐫𝐚𝐟𝐟𝐢𝐂 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 👇"
        traffic_kb = build_inline_keyboard([
            [make_button("📊 LIVE TRAFFIC", url="https://t.me/tem_withh", style="primary")],
            [make_button("🔵 GET NUMBER", callback_data="get_number_menu", style="success")],
            [make_button("❌ CANCEL", callback_data="back_to_main", style="danger")],
        ])
        bot.send_message(message.chat.id, traffic_intro, reply_markup=traffic_kb)

    elif txt == BTN_ADMIN_SUPPORT:
        bot.send_message(
            message.chat.id,
            "🛠️ Admin Support\n\n"
            "❓Having any problem?\n"
            "💬 Contact Admin Support for instant help.",
            reply_markup=admin_support_markup()
        )

    elif txt == BTN_ADMIN_PANEL:
        # ✅ শুধুমাত্র Admin দেখতে পারবে
        if is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "🏠 ADMIN PANEL", reply_markup=admin_panel_markup())
        else:
            bot.send_message(message.chat.id, "❌ আপনি Admin নন!")

# ===================== ADMIN PANEL MULTI-STEP =====================
def handle_admin_state(message, uid, txt):
    uid = str(uid)  # uid কে string এ convert করছি
    state = admin_state.get(uid, {})
    step  = state.get("step")
    cid   = message.chat.id

    if step == "add_country_name":
        if uid not in admin_state:
            admin_state[uid] = {}
        admin_state[uid]["country"] = txt
        admin_state[uid]["step"]    = "add_country_rid"
        msg = bot.send_message(cid, f"✅ দেশের নাম: {txt}\n\nএখন রেন্জ (RID) দিন:", reply_markup=admin_cancel_markup())

    elif step == "add_country_rid":
        service_name = state.get("service")
        country_name = state.get("country")
        panel = state.get("panel", "stex")
        rid = txt
        
        # Validate data
        if not service_name or not country_name:
            bot.send_message(cid, "❌ ডেটা হারিয়ে গেছে। আবার চেষ্টা করুন।", reply_markup=admin_panel_markup())
            admin_state.pop(uid, None)
            return
        
        countries = service_countries.get(service_name, [])
        found = False
        for c in countries:
            if c["name"].lower() == country_name.lower():
                c["rid"] = rid
                c["panel"] = panel
                found = True
                break
        if not found:
            countries.append({"name": country_name, "rid": rid, "panel": panel})
        save_countries_to_firebase(service_name)
        admin_state.pop(uid, None)
        bot.send_message(
            cid,
            f"✅ সফলভাবে এড হয়েছে!\n🔵 Panel   : {panel.upper()}\n🌍 Service : {service_name}\n🌏 Country : {country_name}\n🔢 Range   : {rid}",
            reply_markup=admin_panel_markup()
        )

    elif step == "user_message_uid":
        admin_state[uid]["target_uid"] = txt
        admin_state[uid]["step"]       = "user_message_text"
        msg = bot.send_message(cid, f"👤 ইউজার ID: {txt}\n\nএখন মেসেজ লিখুন:")

    elif step == "user_message_text":
        admin_state[uid]["msg_text"] = txt
        admin_state[uid]["step"]     = "user_message_confirm"
        bot.send_message(cid, f"📨 পাঠাবেন এই মেসেজটি:\n\n{txt}\n\nনিশ্চিত করুন:", reply_markup=admin_confirm_send_markup())

    elif step == "user_message_confirm":
        # ✅ User message confirm - সব ইউজারকে পাঠাবেন
        msg_text = state.get("msg_text")
        
        if txt.lower() in ["yes", "হ্যাঁ"]:
            # সব user কে broadcast
            load_all_users_from_firebase()
            count = failed = 0
            for u in list(users.keys()):
                try:
                    bot.send_message(int(str(u)), f"📨 এডমিন থেকে:\n\n{msg_text}")
                    count += 1
                    time.sleep(0.05)
                except Exception:
                    failed += 1
            bot.send_message(cid, f"✅ {count} জনকে পাঠানো হয়েছে!\n❌ {failed} জন ব্যর্থ।", reply_markup=admin_panel_markup())
            admin_state.pop(uid, None)
        else:
            bot.send_message(cid, "❌ বাতিল করা হয়েছে", reply_markup=admin_panel_markup())
            admin_state.pop(uid, None)

    elif step == "add_money_uid":
        admin_state[uid]["target_uid"] = txt
        admin_state[uid]["step"]       = "add_money_amount"
        msg = bot.send_message(cid, f"👤 UID: {txt}\n\nকত টাকা দিতে চান?", reply_markup=admin_cancel_markup())

    elif step == "add_money_amount":
        try:
            amount     = float(txt)
            target_uid = state.get("target_uid")
            new_bal    = update_firebase_balance(target_uid, amount)
            admin_state.pop(uid, None)
            bot.send_message(cid, f"✅ টাকা এড হয়েছে!\n👤 ID: {target_uid}\n💰 যোগ: {amount} TK\n🏦 মোট: {new_bal:.2f} TK", reply_markup=admin_panel_markup())
            try:
                bot.send_message(target_uid, f"💰 আপনার একাউন্টে {amount} TK যোগ হয়েছে!\n🏦 মোট ব্যালেন্স: {new_bal:.2f} TK")
            except Exception:
                pass
        except Exception:
            bot.send_message(cid, "❌ সংখ্যা দিন।", reply_markup=admin_cancel_markup())

    elif step == "money_clear_uid":
        admin_state[uid]["target_uid"] = txt
        admin_state[uid]["step"]       = "money_clear_amount"
        msg = bot.send_message(cid, f"👤 UID: {txt}\n\nকত টাকা কাটবেন? (all লিখলে সব 0 হবে)", reply_markup=admin_cancel_markup())

    elif step == "money_clear_amount":
        target_uid = state.get("target_uid")
        try:
            if txt.lower() == "all":
                set_firebase_balance(target_uid, 0)
                msg_out = f"✅ {target_uid} এর সব ব্যালেন্স 0 করা হয়েছে।"
            else:
                amount  = float(txt)
                current = get_firebase_balance(target_uid)
                new_bal = set_firebase_balance(target_uid, max(0, current - amount))
                msg_out = f"✅ কাটা: {amount} TK\n👤 ID: {target_uid}\n💰 বাকি: {new_bal:.2f} TK"
            admin_state.pop(uid, None)
            bot.send_message(cid, msg_out, reply_markup=admin_panel_markup())
        except Exception:
            bot.send_message(cid, "❌ সংখ্যা বা 'all' দিন।", reply_markup=admin_cancel_markup())

    # ✅ Change OTP Price
    elif step == "change_price":
        try:
            new_price = float(txt)
            if new_price <= 0:
                bot.send_message(cid, "❌ দাম ০ এর বেশি হতে হবে!", reply_markup=admin_cancel_markup())
                return
            set_otp_price_to_firebase(new_price)
            admin_state.pop(uid, None)
            bot.send_message(
                cid,
                f"✅ OTP মূল্য আপডেট হয়েছে!\n\n"
                f"💰 নতুন মূল্য: {new_price:.2f} টাকা\n\n"
                f"এখন থেকে প্রতিটি OTP-তে ব্যবহারকারী {new_price:.2f} টাকা পাবেন।",
                reply_markup=admin_panel_markup()
            )
        except ValueError:
            bot.send_message(cid, "❌ দয়া করে সঠিক সংখ্যা দিন! (যেমন: 0.50)", reply_markup=admin_cancel_markup())

    elif step == "withdraw_number":
        # ✅ uid যেকোনো type হোক — int key দিয়ে withdraw_data access
        int_uid = int(uid) if str(uid).isdigit() else uid
        if int_uid not in withdraw_data:
            withdraw_data[int_uid] = {}
        withdraw_data[int_uid]["number"] = txt
        admin_state[uid]["step"] = "withdraw_amount"
        msg = bot.send_message(cid, "💰 কত টাকা প্রত্যাহার করতে চান?", reply_markup=withdraw_cancel_markup())

    elif step == "withdraw_amount":
        try:
            amount  = int(txt)
            if amount < 50:
                bot.send_message(cid, "❌ Minimum 50 TK!", reply_markup=withdraw_cancel_markup()); return
            int_uid = int(uid) if str(uid).isdigit() else uid
            if int_uid not in withdraw_data:
                withdraw_data[int_uid] = {}
            withdraw_data[int_uid]["amount"] = amount
            method = withdraw_data[int_uid].get("method", "")
            number = withdraw_data[int_uid].get("number", "")
            admin_state.pop(uid, None)
            confirm_txt = (
                "ভালো করে দেখুন\n"
                "আপনার নাম্বার ঠিক আছে কি না\n"
                "ভুল হলে এডমিন দায়ী নয়\n"
                "সব কিছু ঠিক হবে confirm করুন\n\n"
                f"📱 {method.upper()} : {number}\n"
                f"💰 Amount : {amount} TK"
            )
            bot.send_message(cid, confirm_txt, reply_markup=withdraw_confirm_markup())
        except Exception:
            bot.send_message(cid, "❌ সংখ্যা দিন।", reply_markup=withdraw_cancel_markup())

    else:
        admin_state.pop(uid, None)

# 2FA secret key store — per user
user_2fa_keys = {}

def process_2fa(message):
    secret_key = message.text.strip().replace(" ", "")
    user_2fa_keys[message.chat.id] = secret_key
    code = _totp_generate(secret_key)
    if code:
        remaining = 30 - (int(time.time()) % 30)
        bot.send_message(
            message.chat.id,
            f"⚡ YOUR 2FA CODE\n\n🔑 {code}\n⏳ Remaining : {remaining} Seconds",
            reply_markup=build_inline_keyboard([
                [make_button(code, style="success", copy_text_val=code)],
                [make_button("🔄 Change", callback_data="refresh_2fa", style="primary")],
            ])
        )
    else:
        bot.send_message(message.chat.id, "❌ Invalid Secret Key!\n\n✅ সঠিক Base32 Key দিন।\nExample: JBSWY3DPEHPK3PXP")

# ===================== CALLBACK HANDLER =====================
@safe_execute
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    cid       = call.message.chat.id
    uid       = call.from_user.id
    uid_str   = str(uid)
    user_name = call.from_user.username or f"{call.from_user.first_name or 'User'} {call.from_user.last_name or ''}".strip()
    register_user(uid, user_name)
    user_names[uid_str] = user_name

    # ========== ADMIN PANEL ==========
    if call.data == "adm_close":
        if not is_admin(uid): return
        admin_state.pop(uid_str, None)
        try:
            bot.edit_message_text("✅ Admin Panel বন্ধ।", cid, call.message.message_id)
        except Exception:
            pass

    elif call.data == "adm_cancel":
        admin_state.pop(uid_str, None)
        withdraw_data.pop(uid, None)
        try:
            bot.edit_message_text("❌ বাতিল করা হয়েছে।", cid, call.message.message_id)
        except Exception:
            pass
        bot.send_message(cid, "⚙️ ADMIN PANEL", reply_markup=admin_panel_markup())

    elif call.data == "adm_add_country":
        if not is_admin(uid): return
        try:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔵 STEX", callback_data="adm_panel_stex"), types.InlineKeyboardButton("🟢 ZENEX", callback_data="adm_panel_nexus"))
            bot.edit_message_text("📱 কোন পেনেলে রেঞ্জ এড করবেন?", cid, call.message.message_id, reply_markup=kb)
        except Exception:
            pass
    
    elif call.data in ["adm_panel_stex", "adm_panel_nexus"]:
        if not is_admin(uid): return
        panel = "stex" if "stex" in call.data else "nexus"
        admin_state[uid_str] = {"panel": panel}
        try:
            bot.edit_message_text(f"🌍 {panel.upper()} — কোন সার্ভিসে দেশ এড করবেন?", cid, call.message.message_id, reply_markup=admin_service_select_markup("addcountry"))
        except Exception:
            pass

    elif call.data.startswith("adm_svc_addcountry_"):
        if not is_admin(uid): return
        service_name = call.data.replace("adm_svc_addcountry_", "")
        state = admin_state.get(uid_str, {})
        panel = state.get("panel", "stex")
        admin_state[uid_str] = {"step": "add_country_name", "service": service_name, "panel": panel}
        try:
            bot.edit_message_text(f"✅ সার্ভিস: {service_name}\n\n📝 দেশের নাম লিখুন:", cid, call.message.message_id, reply_markup=admin_cancel_markup())
            msg = call.message
        except Exception:
            msg = bot.send_message(cid, f"✅ সার্ভিস: {service_name}\n\n📝 দেশের নাম লিখুন:", reply_markup=admin_cancel_markup())

    elif call.data == "adm_user_message":
        if not is_admin(uid): return
        admin_state[uid_str] = {"step": "user_message_text"}
        msg = bot.send_message(cid, "📝 সব ইউজারদের কি মেসেজ পাঠাতে চান?")

    elif call.data == "adm_confirm_send":
        if not is_admin(uid): return
        state = admin_state.get(uid_str, {})
        msg_text = state.get("msg_text", "")
        target_uid = state.get("target_uid")
        
        # ✅ Check করা - individual user নাকি broadcast?
        if target_uid:
            # Individual user কে পাঠাচ্ছি
            try:
                bot.send_message(target_uid, f"📨 এডমিন থেকে মেসেজ:\n\n{msg_text}")
                bot.send_message(cid, f"✅ মেসেজ পাঠানো হয়েছে!\n👤 UID: {target_uid}", reply_markup=admin_panel_markup())
            except Exception as e:
                bot.send_message(cid, f"❌ ব্যর্থ: {str(e)}", reply_markup=admin_panel_markup())
        else:
            # সব user কে broadcast (পুরনো সিস্টেম)
            admin_state.pop(uid_str, None)
            load_all_users_from_firebase()
            count = failed = 0
            for u in list(users.keys()):
                try:
                    bot.send_message(int(str(u)), msg_text)
                    count += 1
                    time.sleep(0.05)
                except Exception:
                    failed += 1
            try:
                bot.edit_message_text(f"✅ {count} জনকে পাঠানো হয়েছে।\n❌ {failed} জন ব্যর্থ।", cid, call.message.message_id)
            except Exception:
                pass
            bot.send_message(cid, "⚙️ ADMIN PANEL", reply_markup=admin_panel_markup())
        
        admin_state.pop(uid_str, None)

    elif call.data == "adm_add_money":
        if not is_admin(uid): return
        admin_state[uid_str] = {"step": "add_money_uid"}
        try:
            bot.edit_message_text("👤 ইউজার UID দিন:", cid, call.message.message_id, reply_markup=admin_cancel_markup())
        except Exception:
            pass
        msg = bot.send_message(cid, "🆔 UID লিখুন:")

    elif call.data == "adm_money_clear":
        if not is_admin(uid): return
        admin_state[uid_str] = {"step": "money_clear_uid"}
        try:
            bot.edit_message_text("👤 কোন ইউজারের টাকা কাটবেন? UID দিন:", cid, call.message.message_id, reply_markup=admin_cancel_markup())
        except Exception:
            pass
        msg = bot.send_message(cid, "🆔 UID লিখুন:")

    # ✅ Change OTP Price
    elif call.data == "admin_change_price":
        if not is_admin(uid): 
            bot.answer_callback_query(call.id, "❌ Admin only!")
            return
        admin_state[uid_str] = {"step": "change_price"}
        msg = bot.send_message(
            cid,
            "💰 নতুন OTP মূল্য কত হবে?\n\n"
            "📝 উদাহরণ: 0.50 অথবা 1.25\n\n"
            "(এটি প্রতিটি OTP-তে ইউজারকে দেওয়া হবে)"
        )

    elif call.data == "adm_user_count":
        if not is_admin(uid): return
        load_all_users_from_firebase()
        try:
            bot.edit_message_text(
                f"👥 মোট ইউজার: {len(users)}", cid, call.message.message_id,
                reply_markup=build_inline_keyboard([[make_button("🔙 Back", callback_data="adm_back", style="primary")]])
            )
        except Exception:
            pass

    elif call.data == "adm_all_money":
        if not is_admin(uid): return
        load_all_users_from_firebase()
        info  = "╔════════════════════╗\n📊 ALL USER MONEY\n╚════════════════════╝\n\n"
        total = 0.0
        for u in sorted(users.keys()):
            bal   = get_firebase_balance(u)
            uname = user_names.get(u, "Unknown")
            info += f"🆔 {u} | 👤 {uname} | 💰 {bal:.2f} TK\n"
            total += bal
        info += f"\n💰 মোট: {total:.2f} TK"
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass
        for i in range(0, len(info), 4000):
            bot.send_message(cid, info[i:i+4000])
        bot.send_message(cid, "⚙️ ADMIN PANEL", reply_markup=admin_panel_markup())

    elif call.data == "adm_back":
        if not is_admin(uid): return
        try:
            bot.edit_message_text("⚙️ ADMIN PANEL", cid, call.message.message_id, reply_markup=admin_panel_markup())
        except Exception:
            pass

    elif call.data == "adm_del_country":
        if not is_admin(uid): return
        try:
            bot.edit_message_text(
                "🗑️ কোন সার্ভিস থেকে দেশ ডিলিট করবেন?",
                cid, call.message.message_id,
                reply_markup=admin_del_country_service_markup()
            )
        except Exception:
            pass

    elif call.data.startswith("adm_delcountry_") and not call.data.startswith("adm_delcountry_do_"):
        if not is_admin(uid): return
        service_name = call.data.replace("adm_delcountry_", "")
        if service_name not in FIXED_SERVICES: return
        try:
            bot.edit_message_text(
                f"🗑️ {service_name} — কোন দেশ ডিলিট করবেন?",
                cid, call.message.message_id,
                reply_markup=admin_del_country_list_markup(service_name)
            )
        except Exception:
            pass

    elif call.data.startswith("adm_delcountry_do_"):
        if not is_admin(uid): return
        inner        = call.data.replace("adm_delcountry_do_", "")
        sep          = inner.rfind("__")
        if sep == -1: return
        service_name = inner[:sep]
        idx          = int(inner[sep + 2:])
        countries    = service_countries.get(service_name, [])
        if idx >= len(countries): return
        deleted      = countries[idx]["name"]
        service_countries[service_name].pop(idx)
        save_countries_to_firebase(service_name)
        try:
            bot.edit_message_text(
                f"✅ {service_name} → {deleted} ডিলিট হয়েছে!\n\n🗑️ কোন দেশ ডিলিট করবেন?",
                cid, call.message.message_id,
                reply_markup=admin_del_country_list_markup(service_name)
            )
        except Exception:
            pass

    # ========== NORMAL CALLBACKS ==========
    elif call.data == "noop":
        bot.answer_callback_query(call.id)

    elif call.data == "get_number_menu":
        try:
            bot.edit_message_text(
                SELECT_SERVICE_TEXT,
                cid, call.message.message_id,
                reply_markup=service_menu_markup()
            )
        except Exception:
            bot.send_message(
                cid,
                "📱 যে সার্ভিসের নাম্বার প্রয়োজন তা\nসিলেক্ট করুন:",
                reply_markup=service_menu_markup()
            )

    elif call.data == "refresh_2fa":
        # ✅ একই key দিয়ে নতুন OTP দেবে
        secret_key = user_2fa_keys.get(cid)
        if not secret_key:
            bot.answer_callback_query(call.id, "❌ আগে 2FA Key দিন!")
            return
        code = _totp_generate(secret_key)
        if code:
            remaining = 30 - (int(time.time()) % 30)
            try:
                bot.edit_message_text(
                    f"⚡ YOUR 2FA CODE\n\n🔑 {code}\n⏳ Remaining : {remaining} Seconds",
                    cid, call.message.message_id,
                    reply_markup=build_inline_keyboard([
                        [make_button(code, style="success", copy_text_val=code)],
                        [make_button("🔄 Change", callback_data="refresh_2fa", style="primary")],
                    ])
                )
            except Exception:
                pass
        bot.answer_callback_query(call.id, "✅ Refreshed!")

    elif call.data == "verify_join":
        if is_joined(uid):
            # ✅ Verified - popup alert দেখাবে
            bot.answer_callback_query(call.id, "✅ Verified Success!", show_alert=True)
            welcome_text = (
                "👋𓆩𓆩WELCOME TO OTP SERViCE𓆪𓆪\n"
                " ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅\n\n"
                "🤖 WELCOME TO TEAM WITH 3.0 NUMBER BOT\n\n"
                " ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅\n\n"
                "♾️ POWERED BY Shuvoᯓᡣ𐭩"
            )
            # ✅ Join message delete করো
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            # ✅ নতুন welcome message পাঠাও
            bot.send_message(cid, welcome_text, reply_markup=main_markup())
        else:
            # ❌ Not joined - শুধু popup alert দেখাবে, কোনো message আসবে না
            bot.answer_callback_query(
                call.id, 
                "❌ চ্যানেলে Join করুন তারপর Verified করুন!",
                show_alert=True
            )

    elif call.data == "refresh_traffic":
        # ✅ LIVE TRAFFIC রিফ্রেশ - পুরানো মেসেজ edit করা
        try:
            traffic_display = get_traffic_display()
            bot.edit_message_text(
                text=traffic_display, 
                chat_id=cid, 
                message_id=call.message.message_id, 
                reply_markup=traffic_menu_markup()
            )
            bot.answer_callback_query(call.id, "✅ আপডেট হয়েছে!")
        except Exception as e:
            try:
                # Edit fail হলে নতুন মেসেজ পাঠাও
                traffic_display = get_traffic_display()
                bot.send_message(cid, traffic_display, reply_markup=traffic_menu_markup())
                bot.answer_callback_query(call.id, "✅ রিফ্রেশ হয়েছে")
            except:
                bot.answer_callback_query(call.id, "❌ রিফ্রেশ ব্যর্থ")

    elif call.data == "back_to_main":
        try:
            bot.delete_message(cid, call.message.message_id)
        except Exception:
            pass

    elif call.data == "cancel_2fa":
        # ✅ 2FA কোড তৈরি করা বন্ধ করা এবং মেসেজ ডিলিট করে Cancel দেখানো
        try:
            bot.clear_step_handler_by_chat_id(cid)
        except Exception:
            pass
        try:
            bot.delete_message(cid, call.message.message_id)
        except Exception:
            pass
        bot.send_message(cid, "❌ Cancel")

    elif call.data == "back_profile":
        balance   = get_firebase_balance(uid_str)
        today_str = str(date.today())
        if today_date.get(uid_str) != today_str:
            t_earn = 0.0; t_count = 0
        else:
            t_earn  = today_earn.get(uid_str, 0.0)
            t_count = today_otp_count.get(uid_str, 0)
        msg_text = (
            " 👤  𝐘𝐎𝐔𝐑 𝐏𝐑𝐎𝐅𝐈𝐋𝐄\n\n"
            f"💸 𝐓𝐨𝐝𝐚𝐲 𝐄𝐚𝐫𝐧 : {t_earn:.2f} 𝐓𝐊\n"
            f"📩 𝐓𝐨𝐝𝐚𝐲 𝐎𝐓𝐏 : {t_count}\n\n"
            f"🆔 𝐈𝐃 : {uid_str}\n"
            f"💰 𝐁𝐚𝐥𝐚𝐧𝐜𝐞 : {balance:.2f} 𝐓𝐊\n"
            "✅ 𝐒𝐭𝐚𝐭𝐮𝐬 : 𝐀𝐂𝐓𝐈𝐕𝐄"
        )
        try:
            bot.edit_message_text(msg_text, cid, call.message.message_id, reply_markup=profile_markup())
        except Exception:
            bot.send_message(cid, msg_text, reply_markup=profile_markup())

    elif call.data == "back_balance":
        balance  = get_firebase_balance(uid_str)
        msg_text = (
            "💳 𝐘𝐎𝐔𝐑 𝐁𝐀𝐋𝐀𝐍𝐂𝐄\n\n"
            f"💰 𝐁𝐀𝐋𝐀𝐍𝐂𝐄 {balance:.2f} 𝐓𝐊\n\n"
            "✨ 𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞 𝐁𝐚𝐥𝐚𝐧𝐜𝐞"
        )
        try:
            bot.edit_message_text(msg_text, cid, call.message.message_id, reply_markup=balance_markup(balance))
        except Exception:
            bot.send_message(cid, msg_text, reply_markup=balance_markup(balance))

    elif call.data == "back_to_services":
        try:
            bot.edit_message_text("📱 যে সার্ভিসের নাম্বার প্রয়োজন তা\nসিলেক্ট করুন:", cid, call.message.message_id, reply_markup=service_menu_markup())
        except Exception:
            bot.send_message(cid, "📱 যে সার্ভিসের নাম্বার প্রয়োজন তা\nসিলেক্ট করুন:", reply_markup=service_menu_markup())

    elif call.data.startswith("back_to_country_"):
        service_name = call.data.replace("back_to_country_", "")
        if service_name not in FIXED_SERVICES:
            service_name = user_service.get(cid, "")
        icon = SERVICE_ICONS.get(service_name, "📱")
        try:
            bot.edit_message_text(f"{icon} {service_name.upper()}", cid, call.message.message_id, reply_markup=country_menu_markup(service_name))
        except Exception:
            bot.send_message(cid, f"{icon} {service_name.upper()}", reply_markup=country_menu_markup(service_name))

    elif call.data.startswith("sv_"):
        service_name = call.data[3:]
        if service_name not in FIXED_SERVICES:
            bot.answer_callback_query(call.id, "❌ সার্ভিস পাওয়া যায়নি।"); return
        icon = SERVICE_ICONS.get(service_name, "📱")
        try:
            bot.edit_message_text(f"{icon} {service_name.upper()}", cid, call.message.message_id, reply_markup=country_menu_markup(service_name))
        except Exception:
            bot.send_message(cid, f"{icon} {service_name.upper()}", reply_markup=country_menu_markup(service_name))

    elif call.data.startswith("ct_"):
        inner = call.data[3:]
        sep   = inner.rfind("__")
        if sep == -1: return
        service_name = inner[:sep]
        idx          = int(inner[sep + 2:])
        if service_name not in FIXED_SERVICES:
            bot.answer_callback_query(call.id, "❌ সার্ভিস পাওয়া যায়নি।"); return
        countries = service_countries.get(service_name, [])
        if idx >= len(countries):
            bot.answer_callback_query(call.id, "❌ দেশ পাওয়া যায়নি।"); return
        rid = countries[idx]["rid"]
        user_ranges[cid]  = rid
        user_service[cid] = service_name
        fake_msg = type("obj", (object,), {"chat": call.message.chat, "text": rid})()
        process_number(fake_msg, edit_msg=call.message, service_name=service_name, rid=rid)

    elif call.data == "change_num":
        rid          = user_ranges.get(cid)
        service_name = user_service.get(cid, "Unknown")
        if not rid: return
        fake_msg = type("obj", (object,), {"chat": call.message.chat, "text": rid})()
        process_number(fake_msg, edit_msg=call.message, service_name=service_name, rid=rid)

    elif call.data == "otp_search":
        if otp_running.get(cid):
            bot.answer_callback_query(call.id, "⏳ OTP Search Already Running!"); return
        if received_otps.get(cid):
            bot.send_message(cid, "╔════════════════════╗\n      ✦ OTP RCV ✦\n╚════════════════════╝\n\n➤ OTP ➤ Already Received ✅")
        else:
            nums       = user_numbers.get(cid, [])
            search_msg = bot.send_message(cid, "🔍 OTP SEARCHING...\n⏳ Please Wait...")
            threading.Thread(target=auto_check_otp, args=(cid, list(nums), search_msg.message_id, None, otp_generation.get(cid)), daemon=True).start()

    elif call.data == "otp_price":
        current_price = get_otp_price_from_firebase()
        price_text = f"💰 𝐓𝐨𝐝𝐚𝐲 𝐎𝐓𝐏 𝐏𝐫𝐢𝐜𝐞\n\n📌 𝟏 𝐎𝐓𝐏 = {current_price:.2f} 𝐓𝐊"
        try:
            bot.edit_message_text(
                price_text,
                cid, call.message.message_id,
                reply_markup=otp_price_markup()
            )
        except Exception:
            bot.send_message(cid, price_text, reply_markup=otp_price_markup())

    elif call.data == "withdraw":
        balance = get_firebase_balance(uid)
        if balance < 50:
            insufficient_msg = (
                "❌ 𝐈𝐧𝐬𝐮𝐟𝐟𝐢𝐜𝐢𝐞𝐧𝐭 𝐁𝐚𝐥𝐚𝐧𝐜𝐞\n\n"
                f"💰 আপনার বর্তমান ব্যালেন্স: {balance:.2f} TK\n\n"
                "⚠️ Minimum 50 TK প্রয়োজন\n\n"
                "📌 আরও OTP সংগ্রহ করুন এবং পুনরায় চেষ্টা করুন।"
            )
            kb = build_inline_keyboard([
                [make_button("🔵 GET NUMBER", callback_data="get_number_menu", style="success")],
                [make_button("🔙 BACK", callback_data="back_balance", style="danger")],
            ])
            try:
                bot.edit_message_text(
                    insufficient_msg,
                    cid, call.message.message_id,
                    reply_markup=kb
                )
            except Exception:
                bot.send_message(cid, insufficient_msg, reply_markup=kb)
            return
        try:
            bot.edit_message_text(
                f"🏦 Select method\n\n💰 আপনার ব্যালেন্স: {balance:.2f} TK",
                cid, call.message.message_id,
                reply_markup=withdraw_select_method_markup(balance)
            )
        except Exception:
            bot.send_message(cid, f"🏦 Select method\n\n💰 আপনার ব্যালেন্স: {balance:.2f} TK", reply_markup=withdraw_select_method_markup(balance))

    elif call.data in ["bkash", "rocket"]:
        method_name = call.data.capitalize()
        withdraw_data[uid] = {"method": method_name}
        admin_state[uid_str] = {"step": "withdraw_number"}
        # ✅ শুধু একটি message পাঠাও
        msg = bot.send_message(cid, f"📱 আপনার {method_name} নম্বর লিখুন:", reply_markup=withdraw_cancel_markup())

    elif call.data == "confirm_withdraw":
        # ✅ uid int দিয়ে খোঁজো
        w_data = withdraw_data.get(uid) or withdraw_data.get(uid_str) or {}
        method = w_data.get("method", "")
        number = w_data.get("number", "")
        amount = w_data.get("amount", 0)
        uname  = user_names.get(uid_str, "Unknown")
        # ✅ admin_state clear করো
        admin_state.pop(uid_str, None)
        withdraw_status[uid_str] = {
            "status": "pending", "amount": amount,
            "method": method, "number": number, "msg_id": None
        }
        # User কে pending message
        pending_text = (
            f"⏳ 𝐘𝐨𝐮𝐫 𝐰𝐢𝐭𝐡𝐝𝐫𝐚𝐰𝐚𝐥 𝐢𝐬 𝐩𝐞𝐧𝐝𝐢𝐧𝐠.\n\n"
            f"📱 𝐍𝐮𝐦𝐛𝐞𝐫: {number}\n"
            f"💰 𝐀𝐦𝐨𝐮𝐧𝐭: {amount} TK\n\n"
            "👨‍💼 𝐏𝐥𝐞𝐚𝐬𝐞 𝐰𝐚𝐢𝐭 𝐟𝐨𝐫 𝐚𝐧 𝐚𝐝𝐦𝐢𝐧 𝐭𝐨 𝐫𝐞𝐯𝐢𝐞𝐰 𝐢𝐭.\n\n"
            "📋 𝐂𝐡𝐞𝐜𝐤 𝐲𝐨𝐮𝐫 𝐬𝐭𝐚𝐭𝐮𝐬."
        )
        try:
            sent = bot.edit_message_text(pending_text, cid, call.message.message_id, reply_markup=withdraw_check_markup())
            withdraw_status[uid_str]["msg_id"] = sent.message_id if sent else None
        except Exception:
            sent = bot.send_message(cid, pending_text, reply_markup=withdraw_check_markup())
            withdraw_status[uid_str]["msg_id"] = sent.message_id if sent else None

        # Admin কে পাঠাও
        admin_text = (
            "【💸 𝐍𝐄𝐖 𝐏𝐀𝐘𝐌𝐄𝐍𝐓】\n\n"
            f"➤ 𝐔𝐬𝐞𝐫 : @{uname}\n"
            f"➤ 𝐈𝐃 : {uid_str}\n"
            f"➤ 𝐀𝐦𝐨𝐮𝐧𝐭 : {amount} TK\n"
            f"➤ {method} : {number}"
        )
        bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_approve_markup(uid))

    elif call.data == "cancel_withdraw":
        # ✅ admin_state পরিষ্কার করো যাতে অন্য বাটন কাজ করে
        admin_state.pop(uid_str, None)
        withdraw_data.pop(uid, None)
        bot.answer_callback_query(call.id, "❌ Withdraw বাতিল।")
        try:
            bot.edit_message_text("❌ Withdraw বাতিল করা হয়েছে।", cid, call.message.message_id)
        except Exception:
            pass

    elif call.data == "withdraw_status":
        info = withdraw_status.get(uid_str)
        if not info:
            bot.answer_callback_query(call.id, "❌ কোনো request নেই।"); return
        st     = info.get("status", "pending")
        amount = info.get("amount", 0)
        number = info.get("number", "")
        if st == "pending":
            status_text = (
                f"⏳ 𝐘𝐨𝐮𝐫 𝐰𝐢𝐭𝐡𝐝𝐫𝐚𝐰𝐚𝐥 𝐢𝐬 𝐩𝐞𝐧𝐝𝐢𝐧𝐠.\n\n"
                f"📱 𝐍𝐮𝐦𝐛𝐞𝐫: {number}\n"
                f"💰 𝐀𝐦𝐨𝐮𝐧𝐭: {amount} TK\n\n"
                "👨‍💼 𝐀𝐝𝐦𝐢𝐧 𝐌𝐞𝐬𝐬𝐚𝐠𝐞:\n"
                "⏳ অপেক্ষা করুন, আপনার টাকা পাবেন।\n\n"
                "⏳ 𝐒𝐭𝐚𝐭𝐮𝐬: 𝐏𝐞𝐧𝐝𝐢𝐧𝐠"
            )
        elif st == "approved":
            status_text = (
                f"✅ 𝐘𝐨𝐮𝐫 𝐰𝐢𝐭𝐡𝐝𝐫𝐚𝐰𝐚𝐥 𝐢𝐬 𝐜𝐨𝐦𝐩𝐥𝐞𝐭𝐞𝐝!\n\n"
                f"📱 𝐍𝐮𝐦𝐛𝐞𝐫: {number}\n"
                f"💰 𝐀𝐦𝐨𝐮𝐧𝐭: {amount} TK\n\n"
                "👨‍💼 𝐀𝐝𝐦𝐢𝐧 𝐌𝐞𝐬𝐬𝐚𝐠𝐞:\n"
                "🎉 𝐆𝐨𝐨𝐝! 𝐍𝐢𝐜𝐞 𝐰𝐨𝐫𝐤. 𝐊𝐞𝐞𝐩 𝐢𝐭 𝐮𝐩! 💖\n\n"
                "✅ 𝐒𝐭𝐚𝐭𝐮𝐬: 𝐂𝐨𝐦𝐩𝐥𝐞𝐭𝐞"
            )
        else:
            status_text = (
                f"❌ 𝐘𝐨𝐮𝐫 𝐰𝐢𝐭𝐡𝐝𝐫𝐚𝐰𝐚𝐥 𝐰𝐚𝐬 𝐫𝐞𝐣𝐞𝐜𝐭𝐞𝐝.\n\n"
                f"📱 𝐍𝐮𝐦𝐛𝐞𝐫: {number}\n"
                f"💰 𝐀𝐦𝐨𝐮𝐧𝐭: {amount} TK\n\n"
                "❌ 𝐒𝐭𝐚𝐭𝐮𝐬: 𝐑𝐞𝐣𝐞𝐜𝐭𝐞𝐝"
            )
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text(status_text, cid, call.message.message_id, reply_markup=withdraw_refresh_markup())
        except Exception:
            bot.send_message(cid, status_text, reply_markup=withdraw_refresh_markup())

    elif call.data == "withdraw_refresh":
        # status চেক করে message edit করে
        info = withdraw_status.get(uid_str)
        if not info:
            bot.answer_callback_query(call.id, "❌ কোনো request নেই।"); return
        st     = info.get("status", "pending")
        amount = info.get("amount", 0)
        number = info.get("number", "")
        if st == "pending":
            status_text = (
                f"⏳ 𝐘𝐨𝐮𝐫 𝐰𝐢𝐭𝐡𝐝𝐫𝐚𝐰𝐚𝐥 𝐢𝐬 𝐩𝐞𝐧𝐝𝐢𝐧𝐠.\n\n"
                f"📱 𝐍𝐮𝐦𝐛𝐞𝐫: {number}\n"
                f"💰 𝐀𝐦𝐨𝐮𝐧𝐭: {amount} TK\n\n"
                "👨‍💼 𝐀𝐝𝐦𝐢𝐧 𝐌𝐞𝐬𝐬𝐚𝐠𝐞:\n"
                "⏳ অপেক্ষা করুন, আপনার টাকা পাবেন।\n\n"
                "⏳ 𝐒𝐭𝐚𝐭𝐮𝐬: 𝐏𝐞𝐧𝐝𝐢𝐧𝐠"
            )
        elif st == "approved":
            status_text = (
                f"✅ 𝐘𝐨𝐮𝐫 𝐰𝐢𝐭𝐡𝐝𝐫𝐚𝐰𝐚𝐥 𝐢𝐬 𝐜𝐨𝐦𝐩𝐥𝐞𝐭𝐞𝐝!\n\n"
                f"📱 𝐍𝐮𝐦𝐛𝐞𝐫: {number}\n"
                f"💰 𝐀𝐦𝐨𝐮𝐧𝐭: {amount} TK\n\n"
                "👨‍💼 𝐀𝐝𝐦𝐢𝐧 𝐌𝐞𝐬𝐬𝐚𝐠𝐞:\n"
                "🎉 𝐆𝐨𝐨𝐝! 𝐍𝐢𝐜𝐞 𝐰𝐨𝐫𝐤. 𝐊𝐞𝐞𝐩 𝐢𝐭 𝐮𝐩! 💖\n\n"
                "✅ 𝐒𝐭𝐚𝐭𝐮𝐬: 𝐂𝐨𝐦𝐩𝐥𝐞𝐭𝐞"
            )
        else:
            status_text = (
                f"❌ 𝐘𝐨𝐮𝐫 𝐰𝐢𝐭𝐡𝐝𝐫𝐚𝐰𝐚𝐥 𝐰𝐚𝐬 𝐫𝐞𝐣𝐞𝐜𝐭𝐞𝐝.\n\n"
                f"📱 𝐍𝐮𝐦𝐛𝐞𝐫: {number}\n"
                f"💰 𝐀𝐦𝐨𝐮𝐧𝐭: {amount} TK\n\n"
                "❌ 𝐒𝐭𝐚𝐭𝐮𝐬: 𝐑𝐞𝐣𝐞𝐜𝐭𝐞𝐝"
            )
        try:
            bot.edit_message_text(status_text, cid, call.message.message_id, reply_markup=withdraw_refresh_markup())
            bot.answer_callback_query(call.id, "🔄 Refreshed!")
        except Exception:
            bot.answer_callback_query(call.id)

    elif call.data.startswith("approve_"):
        if not is_admin(uid):
            bot.answer_callback_query(call.id, "❌ Admin only!"); return
        target_uid = call.data.split("_")[1]
        w          = withdraw_data.get(int(target_uid), {})
        amount     = w.get("amount", 0)
        method     = w.get("method", "")
        number     = w.get("number", "")
        update_firebase_balance(target_uid, -amount)
        withdraw_status[target_uid] = {
            "status": "approved", "amount": amount,
            "method": method, "number": number
        }
        # ইউজারের status message edit করো
        info   = withdraw_status.get(target_uid, {})
        msg_id = info.get("msg_id")
        approved_text = (
            f"✅ 𝐘𝐨𝐮𝐫 𝐰𝐢𝐭𝐡𝐝𝐫𝐚𝐰𝐚𝐥 𝐢𝐬 𝐜𝐨𝐦𝐩𝐥𝐞𝐭𝐞𝐝!\n\n"
            f"📱 𝐍𝐮𝐦𝐛𝐞𝐫: {number}\n"
            f"💰 𝐀𝐦𝐨𝐮𝐧𝐭: {amount} TK\n\n"
            "👨‍💼 𝐀𝐝𝐦𝐢𝐧 𝐌𝐞𝐬𝐬𝐚𝐠𝐞:\n"
            "🎉 𝐆𝐨𝐨𝐝! 𝐍𝐢𝐜𝐞 𝐰𝐨𝐫𝐤. 𝐊𝐞𝐞𝐩 𝐢𝐭 𝐮𝐩! 💖\n\n"
            "✅ 𝐒𝐭𝐚𝐭𝐮𝐬: 𝐂𝐨𝐦𝐩𝐥𝐞𝐭𝐞"
        )
        try:
            if msg_id:
                bot.edit_message_text(approved_text, int(target_uid), msg_id)
            else:
                bot.send_message(target_uid, approved_text)
        except Exception:
            try:
                bot.send_message(target_uid, approved_text)
            except Exception:
                pass
        bot.edit_message_text("✅ Approved", cid, call.message.message_id)

    elif call.data.startswith("reject_"):
        if not is_admin(uid):
            bot.answer_callback_query(call.id, "❌ Admin only!"); return
        target_uid = call.data.split("_")[1]
        w          = withdraw_data.get(int(target_uid), {})
        amount     = w.get("amount", 0)
        method     = w.get("method", "")
        number     = w.get("number", "")
        withdraw_status[target_uid] = {
            "status": "rejected", "amount": amount,
            "method": method, "number": number
        }
        info   = withdraw_status.get(target_uid, {})
        msg_id = info.get("msg_id")
        rejected_text = (
            f"❌ 𝐘𝐨𝐮𝐫 𝐰𝐢𝐭𝐡𝐝𝐫𝐚𝐰𝐚𝐥 𝐰𝐚𝐬 𝐫𝐞𝐣𝐞𝐜𝐭𝐞𝐝.\n\n"
            f"📱 𝐍𝐮𝐦𝐛𝐞𝐫: {number}\n"
            f"💰 𝐀𝐦𝐨𝐮𝐧𝐭: {amount} TK\n\n"
            "❌ 𝐒𝐭𝐚𝐭𝐮𝐬: 𝐑𝐞𝐣𝐞𝐜𝐭𝐞𝐝"
        )
        try:
            if msg_id:
                bot.edit_message_text(rejected_text, int(target_uid), msg_id)
            else:
                bot.send_message(target_uid, rejected_text)
        except Exception:
            try:
                bot.send_message(target_uid, rejected_text)
            except Exception:
                pass
        bot.edit_message_text("❌ Rejected", cid, call.message.message_id)

# ===================== BOT RUN =====================
def run_bot():
    keep_alive()
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception:
        logging.error(traceback.format_exc())

    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=60, long_polling_timeout=60)
        except Exception:
            logging.error("Bot polling crashed, restarting in 3 seconds...")
            logging.error(traceback.format_exc())
            time.sleep(3)
        except BaseException:
            # ✅ যেকোনো অপ্রত্যাশিত এরর (এমনকি Exception-এর বাইরেরও) ধরে রাখছি,
            # যাতে বট পুরোপুরি বন্ধ না হয়ে আবার নিজে থেকে চালু হয়
            logging.error("Unexpected crash, restarting in 5 seconds...")
            logging.error(traceback.format_exc())
            time.sleep(5)

if __name__ == "__main__":
    run_bot()