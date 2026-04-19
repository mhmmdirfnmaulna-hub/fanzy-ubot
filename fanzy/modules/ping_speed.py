import asyncio
import os
import json
import platform
import sys
import psutil
from datetime import datetime
from time import time
from speedtest import Speedtest
from pyrogram import Client, filters
from pyrogram import __version__
from pyrogram.raw.functions import Ping
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from fanzy import *

__MODULE__ = "System"
__HELP__ = """
<b>📁 SYSTEM TOOLS</b>

╭ <code>{0}ping</code> - Check bot ping
├ <code>{0}speed</code> - Test VPS speed
╰ <code>{0}spc</code> - View system info
"""


# ============================================
# HELPER FUNCTIONS
# ============================================

def humanbytes(size):
    power = 2**10
    n = 0
    power_labels = {0: "B", 1: "KB", 2: "MB", 3: "GB", 4: "TB"}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}"

def get_vps_uptime():
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    now = datetime.now()
    uptime = now - boot_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m"

def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor


# ============================================
# PING
# ============================================

@PY.UBOT("ping")
@PY.TOP_CMD
async def ping_cmd(client, message):
    import time
    from datetime import datetime
    
    msg = await message.reply("<b>⏳ Measuring ping...</b>")
    
    # ============ TELEGRAM PING ============
    start = datetime.now()
    await client.invoke(Ping(ping_id=0))
    end = datetime.now()
    tg_ping = round((end - start).microseconds / 1000, 2)
    
    # ============ VPS PING ============
    start_vps = time.time()
    await asyncio.sleep(0.1)
    vps_ping = round((time.time() - start_vps) * 1000, 2)
    
    # ============ HITUNG BOT UPTIME (MANUAL) ============
    from fanzy import start_time as bot_start_time
    current_time = time.time()
    uptime_seconds = int(current_time - bot_start_time)
    
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    
    if days > 0:
        uptime = f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        uptime = f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        uptime = f"{minutes}m {seconds}s"
    else:
        uptime = f"{seconds}s"
    
    # ============ VPS UPTIME ============
    vps_uptime = get_vps_uptime()
    
    # ============ STATUS ============
    if tg_ping < 50:
        status_icon = "⚡"
        status_text = "Excellent"
    elif tg_ping < 100:
        status_icon = "✅"
        status_text = "Good"
    elif tg_ping < 200:
        status_icon = "⚠️"
        status_text = "Slow"
    else:
        status_icon = "❌"
        status_text = "Very Slow"
    
    text = f"""
<b>🏓 TOOLS PINGS {status_icon}</b>

<b>📡 Telegram API:</b> <code>{tg_ping} ms</code>
<b>🖥️ VPS Local:</b> <code>{vps_ping} ms</code>
<b>⏱️ Bot Uptime:</b> <code>{uptime}</code>
<b>🖥️ VPS Uptime:</b> <code>{vps_uptime}</code>

<b>📌 note:</b> Ping < 100ms = optiml
<blockquote><b>⚡ Power By Fanzy Userbotz</b></blockquote>
"""
    
    await msg.edit(text)


# ============================================
# SPEEDTEST
# ============================================

@PY.UBOT("speed")
@PY.TOP_CMD
async def speedtest_cmd(client, message):
    msg = await message.reply("<b>⏳ Running speedtest...</b>")

    try:
        test = Speedtest()
        test.get_best_server()
        
        download_speed = await asyncio.to_thread(test.download)
        upload_speed = await asyncio.to_thread(test.upload)
        test.results.share()

        result = test.results.dict()
        vps_uptime = get_vps_uptime()
        
        caption = f"""
<b>📊 SPEEDTEST TOOLS</b>

<b>🌍 ISP:</b> <code>{result['client']['isp']}</code>
<b>📡 Server:</b> <code>{result['server']['name']}</code>
<b>⚡ Ping:</b> <code>{result['ping']} ms</code>
<b>📥 Download:</b> <code>{humanbytes(result['download'])}/s</code>
<b>📤 Upload:</b> <code>{humanbytes(result['upload'])}/s</code>
<b>⏳ VPS Uptime:</b> <code>{vps_uptime}</code>
<blockquote><b>⚡ Power By Fanzy Userbotz</b></blockquote>"""

        await msg.delete()
        await client.send_photo(message.chat.id, result["share"], caption=caption)

    except Exception as e:
        await msg.edit(f"<b>❌ Speedtest failed!</b>\n\n<code>{e}</code>")


# ============================================
# SYSTEM INFO
# ============================================

@PY.UBOT("spc")
@PY.TOP_CMD
async def system_info_cmd(client: Client, message: Message):
    ggl = await EMO.GAGAL(client)
    prs = await EMO.PROSES(client)
    
    status_msg = await message.reply(f"{prs} Fetching system info...")
    
    try:
        uname = platform.uname()
        svmem = psutil.virtual_memory()
        net_io = psutil.net_io_counters()
        cpufreq = psutil.cpu_freq()
        
        text = f"""
<b>🖥️ SYSTEM INFO TOLS</b>

<b>💻 OS:</b> <code>{uname.system}</code>
<b>🐍 Python:</b> <code>{sys.version.split()[0]}</code>
<b>⚡ Pyrogram:</b> <code>{__version__}</code>

<b>🖥️ CPU:</b>
├ <b>Cores:</b> <code>{psutil.cpu_count(logical=True)}</code>
├ <b>Usage:</b> <code>{psutil.cpu_percent()}%</code>
╰ <b>Freq:</b> <code>{cpufreq.current:.0f} MHz</code>

<b>💾 RAM:</b>
├ <b>Total:</b> <code>{get_size(svmem.total)}</code>
├ <b>Used:</b> <code>{get_size(svmem.used)}</code>
╰ <b>Free:</b> <code>{get_size(svmem.available)}</code>

<b>🌐 NETWORK:</b>
├ <b>Upload:</b> <code>{get_size(net_io.bytes_sent)}</code>
╰ <b>Download:</b> <code>{get_size(net_io.bytes_recv)}</code>

<b>⏱️ Uptime:</b> <code>{get_vps_uptime()}</code>
<blockquote><b>⚡ Power By Fanzy Userbotz</b></blockquote>
"""
        await status_msg.edit(text, disable_web_page_preview=True)
        
    except Exception as e:
        await status_msg.edit(f"{ggl} Error: <code>{str(e)[:100]}</code>")