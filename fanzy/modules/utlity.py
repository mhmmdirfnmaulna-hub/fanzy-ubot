import asyncio
import requests
import aiohttp
import filetype
from pyrogram import filters
import os
from datetime import datetime
from gc import get_objects
from geopy.geocoders import Nominatim
from io import BytesIO
from pykeyboard import InlineKeyboard
from pyrogram.types import (
    InlineKeyboardButton, InlineQueryResultArticle,
    InlineQueryResultPhoto, InputTextMessageContent,
    InlineKeyboardMarkup
)
from fanzy import *

__MODULE__ = "utility"
__HELP__ = """
<b>🛠 UTILITY TOOLS</b>
├ <code>{0}gps</code> - Lacak lokasi
╰ <code>{0}tg</code> - Media ke URL


<b>🛡 PM SECURITY</b>
├ <code>{0}pmpermit</code> - Aktifkan (on/off)
├ <code>{0}tg</code> - upload foto ke catbox
├ <code>{0}setpm</code> - Atur (limit/txt/img)
├ <code>{0}ok</code> - Izinkan chat
╰ <code>{0}no</code> - Blokir/Tolak chat
"""

# ============================================
# GPS & MAPS
# ============================================
USER_HASH = "b2558207a2d4313a6434ae124"
MAX_FILE_SIZE_MB = 200
FLOOD = {}
MSG_ID = {}
PM_TEXT = """
<blockquote>👋 <b>Halo</b> {mention}

<i>Saya adalah keamanan fanzy userbot, mohon untuk tidak  melakukan  spam terhadap majikan saya, anda  akan di blokir otomatis jika melakukan spam!</i>

⚠️ <b>PERINGATAN:</b> {warn}
<b>━━━━━━━━━━━━━━━━━━━━━━━</b></blockquote>
"""

@PY.UBOT("gps|maps")
@PY.TOP_CMD
async def gps_cmd(client, message):
    prs = await EMO.PROSES(client)
    ggl = await EMO.GAGAL(client)
    
    args = get_arg(message)
    if not args:
        return await message.reply(f"{ggl} **Berikan nama lokasi!**")
    
    status_msg = await message.reply(f"{prs} **🔍 Mencari lokasi...**")
    geolocator = Nominatim(user_agent="bot")
    
    try:
        geoloc = geolocator.geocode(args)
        if geoloc:
            await message.reply_location(geoloc.latitude, geoloc.longitude)
            await status_msg.delete()
        else:
            await status_msg.edit(f"{ggl} **Lokasi tidak ditemukan.**")
    except Exception:
        await status_msg.edit(f"{ggl} **Terjadi kesalahan server.**")


async def upload_file(buffer: BytesIO) -> str:
    kind = filetype.guess(buffer)
    if kind is None:
        raise ValueError("Format file tidak didukung.")    
    ext = kind.extension
    buffer.seek(0)
    file_bytes = buffer.read()    
    url = 'https://catbox.moe/user/api.php'    
    boundary = f'------WebKitFormBoundary{os.urandom(8).hex()}'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Accept": "text/plain, */*; q=0.01",
        "Origin": "https://catbox.moe",
        "Referer": "https://catbox.moe/"
    }

    body = BytesIO()    
    body.write(f'--{boundary}\r\n'.encode())
    body.write(b'Content-Disposition: form-data; name="reqtype"\r\n\r\n')
    body.write(b'fileupload\r\n')    
    body.write(f'--{boundary}\r\n'.encode())
    body.write(b'Content-Disposition: form-data; name="userhash"\r\n\r\n')
    body.write(f'{USER_HASH}\r\n'.encode())    
    body.write(f'--{boundary}\r\n'.encode())
    random_filename = f"fanzy_{os.urandom(4).hex()}.{ext}"
    body.write(f'Content-Disposition: form-data; name="fileToUpload"; filename="{random_filename}"\r\n'.encode())
    body.write(f'Content-Type: {kind.mime}\r\n\r\n'.encode())
    body.write(file_bytes)
    body.write(b'\r\n')    
    body.write(f'--{boundary}--\r\n'.encode())    
    payload = body.getvalue()
    async with aiohttp.ClientSession(headers=headers) as session:
        timeout = aiohttp.ClientTimeout(total=300) # Timeout 5 menit untuk file besar
        async with session.post(url, data=payload, timeout=timeout) as response:
            result = await response.text()
            if response.status != 200:
                raise Exception(f"Server Menolak ({response.status}): {result}")
            
            if not result.strip().startswith("http"):
                raise Exception(f"API Error: {result}")
                
            return result.strip()

# ============================================
# HANDLER COMMAND TOURL / TG (VERSI GAMBAR)
# ============================================
@PY.UBOT("tourl|tg")
async def tourl_handler(client, message):
    msg = await message.reply("<b>⏳ Prosess Upload....</b>")
    reply = message.reply_to_message    
    if reply and reply.media:
        path = None
        try:
            path = await reply.download()            
            file_size_bytes = os.path.getsize(path)
            if file_size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024:
                return await msg.edit(f"<b>❌ File terlalu besar (Maks {MAX_FILE_SIZE_MB}MB).</b>")            
            with open(path, 'rb') as f:
                content = f.read()
                buffer = BytesIO(content)
                buffer.name = path
                media_url = await upload_file(buffer)            
            await msg.delete()            
            await client.send_photo(
                chat_id=message.chat.id,
                photo=path,
                caption=f"🔗 <b>Link photo:</b> <a href='{media_url}'>Click Here</a>",
                reply_to_message_id=reply.id
            )            
        except Exception as e:
            error_msg = str(e)
            if "412" in error_msg:
                await msg.edit(f"<b>❌ Ralat 412:</b> <code>IP VPS Anda diblokir untuk upload anonim. Pastikan USER_HASH sudah benar.</code>")
            else:
                await msg.edit(f"<b>❌ Gagal Mengunggah:</b>\n<code>{error_msg}</code>")
        
        finally:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
    else:
        await msg.edit("<b>⚠️ Harap balas ke pesan media (foto/video/stiker).</b>")

# ============================================
# PM PERMIT LOGIC
# ============================================

async def delete_old_message(message, msg_id):
    try:
        await message._client.delete_messages(message.chat.id, msg_id)
    except:
        pass


async def pmpermit_button(m):
    buttons = InlineKeyboard(row_width=1)
    keyboard = []
    for X in m.split("~>", 1)[1].split():
        X_parts = X.split(":", 1)
        keyboard.append(InlineKeyboardButton(X_parts[0].replace("_", " "), url=X_parts[1]))
    buttons.add(*keyboard)
    text = m.split("~>", 1)[0]
    return buttons, text


@PY.NO_CMD_UBOT("PMPERMIT", ubot)
async def pmpermit_handler(client, message):
    DEVS = [1825618929, 1831850761]
    user = message.from_user
    if user.id in DEVS:
        return
    pm_on = await get_vars(client.me.id, "PMPERMIT")
    if pm_on:
        if user.id in MSG_ID:
            await delete_old_message(message, MSG_ID.get(user.id, 0))
        check = await get_pm_id(client.me.id)
        if user.id not in check:
            if user.id in FLOOD:
                FLOOD[user.id] += 1
            else:
                FLOOD[user.id] = 1
            pm_limit = await get_vars(client.me.id, "PM_LIMIT") or "5"
            try:
                if FLOOD[user.id] > int(pm_limit):
                    del FLOOD[user.id]
                    await message.reply("sudah diingatkan jangan spam, sekarang Anda diblokir.")
                    return await client.block_user(user.id)
            except ValueError:
                await set_vars(client.me.id, "PM_LIMIT", "5")
            pm_msg = await get_vars(client.me.id, "PM_TEXT") or PM_TEXT
            if "~>" in pm_msg:
                x = await client.get_inline_bot_results(bot.me.username, f"pm_pr {id(message)} {FLOOD[user.id]}")
                msg = await client.send_inline_bot_result(message.chat.id, x.query_id, x.results[0].id, reply_to_message_id=message.id)
                MSG_ID[user.id] = int(msg.updates[0].id)
            else:
                try:
                    pm_img = await get_vars(client.me.id, "PM_IMG")
                    rpk = f"[{user.first_name} {user.last_name or ''}](tg://user?id={user.id})"
                    peringatan = f"{FLOOD[user.id]} / {pm_limit}"
                    if pm_img:
                        try:
                            msg = await message.reply_photo(pm_img, caption=pm_msg.format(mention=rpk, warn=peringatan))
                        except ValueError:
                            await set_vars(client.me.id, "PM_IMG", "https://telegra.ph//file/be22060c145c058bf4558.jpg")
                    else:
                        msg = await message.reply(pm_msg.format(mention=rpk, warn=peringatan))
                    MSG_ID[user.id] = msg.id
                except UnboundLocalError:
                    pass


@PY.UBOT("setpm")
@PY.TOP_CMD
async def setpm_cmd(client, message):
    brhsl = await EMO.BERHASIL(client)
    ggl = await EMO.GAGAL(client)    
    if len(message.command) < 2:
        return await message.reply(f"{ggl} **Format:** `.setpm [query] [value/reply]`")        
    query_map = {"limit": "PM_LIMIT", "text": "PM_TEXT", "img": "PM_IMG"}
    query_key = message.command[1].lower()    
    if query_key not in query_map:
        return await message.reply(f"{ggl} **Query tidak valid!** (limit/text/img)")    
    if message.reply_to_message:
        if query_key == "img" and message.reply_to_message.photo:
            value_str = message.reply_to_message.photo.file_id
        else:
            value_str = message.reply_to_message.text or message.reply_to_message.caption
    else:
        if len(message.command) < 3:
            return await message.reply(f"{ggl} **Silakan masukkan value atau reply ke pesan.**")
        value_str = message.text.split(None, 2)[2]
    if str(value_str).lower() == "none":
        value_str = False        
    db_variable = query_map[query_key]
    await set_vars(client.me.id, db_variable, value_str)    
    return await message.reply(f"{brhsl} **PM-Permit {query_key} berhasil diatur!**")
        


@PY.UBOT("pmpermit")
@PY.TOP_CMD
async def pmpermit_cmd(client, message):
    brhsl = await EMO.BERHASIL(client)
    ggl = await EMO.GAGAL(client)
    if len(message.command) < 2:
        return await message.reply(f"{ggl}{message.text.split()[0]} [on/off]")

    toggle_options = {"off": False, "on": True}
    toggle_option = message.command[1].lower()

    if toggle_option not in toggle_options:
        return await message.reply(f"{ggl}opsi tidak valid. Harap gunakan 'on' atau 'off'.")

    value = toggle_options[toggle_option]
    text = "diaktifkan" if value else "dinonaktifkan"

    await set_vars(client.me.id, "PMPERMIT", value)
    await message.reply(f"**{brhsl}pmpermit berhasil {text}**")


@PY.INLINE("pm_pr")
async def pm_pr_inline(client, inline_query):
    get_id = inline_query.query.split()
    m = [obj for obj in get_objects() if id(obj) == int(get_id[1])][0]
    pm_msg = await get_vars(m._client.me.id, "PM_TEXT") or PM_TEXT
    pm_limit = await get_vars(m._client.me.id, "PM_LIMIT") or 5
    pm_img = await get_vars(m._client.me.id, "PM_IMG")
    rpk = f"[{m.from_user.first_name} {m.from_user.last_name or ''}](tg://user?id={m.from_user.id})"
    peringatan = f"{int(get_id[2])} / {pm_limit}"
    buttons, text = await pmpermit_button(pm_msg)
    if pm_img:
        photo_video = InlineQueryResultVideo if pm_img.endswith(".mp4") else InlineQueryResultPhoto
        photo_video_url = {"video_url": pm_img, "thumb_url": pm_img} if pm_img.endswith(".mp4") else {"photo_url": pm_img}
        hasil = [photo_video(**photo_video_url, title="Dapatkan tombol!", caption=text.format(mention=rpk, warn=peringatan), reply_markup=buttons)]
    else:
        hasil = [InlineQueryResultArticle(title="Dapatkan tombol!", reply_markup=buttons, input_message_content=InputTextMessageContent(text.format(mention=rpk, warn=peringatan)))]
    await client.answer_inline_query(inline_query.id, cache_time=0, results=hasil)


@PY.UBOT("ok")
@PY.UBOT("terima")
@PY.TOP_CMD
@PY.PRIVATE
async def ok_cmd(client, message):
    brhsl = await EMO.BERHASIL(client)
    user = message.chat
    rpk = f"[{user.first_name} {user.last_name or ''}](tg://user?id={user.id})"
    vars = await get_pm_id(client.me.id)
    if user.id not in vars:
        await add_pm_id(client.me.id, user.id)
        return await message.reply(f"{brhsl}baiklah, {rpk} telah diterima")
    else:
        return await message.reply(f"{brhsl}{rpk} sudah diterima")


@PY.UBOT("no")
@PY.UBOT("tolak")
@PY.TOP_CMD
@PY.PRIVATE
async def no_cmd(client, message):
    ggl = await EMO.GAGAL(client)
    user = message.chat
    rpk = f"[{user.first_name} {user.last_name or ''}](tg://user?id={user.id})"
    vars = await get_pm_id(client.me.id)
    if user.id not in vars:
        await message.reply(f"{ggl}🙏🏻 maaf {rpk} anda telah diblokir")
        return await client.block_user(user.id)
    else:
        await remove_pm_id(client.me.id, user.id)
        return await message.reply(f"{ggl}🙏🏻 maaf {rpk} anda telah ditolak untuk menghubungi akun ini lagi")
        
     
     
