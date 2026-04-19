import asyncio
import random
import requests
import aiohttp
from io import BytesIO
from pyrogram.enums import ChatAction
from pyrogram.types import InputMediaPhoto, Message
from fanzy import *

__MODULE__ = "search"
__HELP__ = """
<b>🔍 SEARCH MENU</b>
├ <code>{0}yts</code> - Youtube Search
├ <code>{0}tts</code> - Tiktok Search
├ <code>{0}pins</code> - Pinterest Search
╰ <code>{0}gif</code> - Gif Search

<b>📌 Format Penggunaan:</b>
╰ <code>{0}yts</code> [query]
"""

API_KEY = "fanzy"
PINTEREST_API_KEY = "fanzy"
PINTEREST_SEARCH_URL = "https://api.botcahx.eu.org/api/search/pinterest"
YOUTUBE_SEARCH_URL = "https://api.botcahx.eu.org/api/search/yts"
TIKTOK_SEARCH_URL = "https://api.botcahx.eu.org/api/search/tiktoks"

def is_list(obj):
    return hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, dict))

def is_dict(obj):
    return hasattr(obj, 'keys') and hasattr(obj, 'get')

def extract_urls_from_results(results):
    urls = []
    if is_list(results):
        for item in results:
            if isinstance(item, str) and item.startswith('http'):
                urls.append(item)
            elif is_dict(item):
                for key in ['image', 'images', 'url', 'link', 'src']:
                    if key in item and isinstance(item[key], str) and item[key].startswith('http'):
                        urls.append(item[key])
                        break
    elif is_dict(results):
        for key in ['data', 'images', 'result', 'urls']:
            if key in results:
                sub = results[key]
                if is_list(sub):
                    return extract_urls_from_results(sub)
        for val in results.values():
            if is_list(val):
                return extract_urls_from_results(val)
    return urls

def fetch_youtube(query):
    params = {"query": query, "apikey": API_KEY}
    try:
        response = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("result")
    except Exception:
        return None

# ============================================
# YOUTUBE SEARCH
# ============================================
@PY.UBOT("ytsearch|yts")
@PY.TOP_CMD
async def youtube_search(client, message):
    ggl = await EMO.GAGAL(client)
    prs = await EMO.PROSES(client)
    
    args = get_arg(message)
    if not args:
        return await message.reply_text(f"{ggl} **Gunakan:** `.yts [query]`")
    
    status_msg = await message.reply_text(f"{prs} **🔍 Searching YouTube...**")
    results = fetch_youtube(args)
    
    if results:
        response_text = f"<b>📹 YOUTUBE SEARCH!</b>\n━━━━━━━━━━━━━━━━━━━\n"
        for idx, result in enumerate(results[:5], start=1):
            title = result.get("title", "No Title")
            link = result.get("url", "#")
            dur = result.get("duration", "N/A")
            response_text += f"<b>{idx}. <a href='{link}'>{title}</a></b>\n╰ <i>{dur} | {result.get('views', '0')} views</i>\n\n"
        await status_msg.edit(response_text, disable_web_page_preview=True)
    else:
        await status_msg.edit(f"{ggl} **Video tidak ditemukan.**")

# ============================================
# TIKTOK SEARCH
# ============================================
@PY.UBOT("tiktoksearch|tts")
@PY.TOP_CMD
async def tiktok_search(client, message):
    ggl = await EMO.GAGAL(client)
    prs = await EMO.PROSES(client)
    sks = await EMO.BERHASIL(client)
    
    query = get_arg(message)
    if not query:
        return await message.reply(f"{ggl} **Gunakan:** `.tts [query]`")
    
    status_msg = await message.reply(f"{prs} <b>🔍 Searching...</b>")
    
    try:
        url = f"{TIKTOK_SEARCH_URL}?query={query}&apikey={API_KEY}"
        response = requests.get(url, timeout=15)
        data = response.json()
        
        if not data.get("status") or not data.get("result", {}).get("data"):
            return await status_msg.edit(f"{ggl} **Video tidak ditemukan.**")
        
        video = data["result"]["data"][0]

        # Limit teks agar tidak wrapping (turun baris)
        judul = video['title'][:12] + "..." if len(video['title']) > 12 else video['title']
        musik = video['music_info']['title'][:12] + "..." if len(video['music_info']['title']) > 12 else video['music_info']['title']
        
        # UX Ultra-Compact
        caption = f"""
<b>{sks} TIKTOK RESULT!</b>


<b>🎬 Judul:</b> {judul}
<b>🌍 Region:</b> {video['region']}
<b>🎵 Musik:</b> {musik}
<b>▶️ Play:</b> {video['play_count']}
<b>❤ Like:</b> {video['digg_count']}
<b>💬 Komentar:</b> {video['comment_count']}
━━━━━━━━━━━━━━━━━━━
"""
        await status_msg.edit(f"{prs} <b>📥 Downloading...</b>")
        
        r = requests.get(video["play"], timeout=30)
        file = BytesIO(r.content)
        file.name = "tiktok.mp4"
        
        await client.send_video(
            chat_id=message.chat.id,
            video=file,
            caption=caption,
            reply_to_message_id=message.id
        )
        await status_msg.delete()
        
    except Exception:
        await status_msg.edit(f"{ggl} <b>Sistem Error.</b>")



# ============================================
# PINTEREST SEARCH
# ============================================
@PY.UBOT("pins")
@PY.TOP_CMD
async def pinterest_search(client, message: Message):
    ggl = await EMO.GAGAL(client)
    prs = await EMO.PROSES(client)
    sks = await EMO.BERHASIL(client)
    
    query = get_arg(message)
    if not query:
        return await message.reply_text(f"{ggl} **Gunakan:** `.pins [query]`")
    
    status_msg = await message.reply_text(f"{prs} **🔍 Searching Pinterest...**")
    
    try:
        api_url = f"{PINTEREST_SEARCH_URL}?text1={query}&apikey={PINTEREST_API_KEY}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=30) as resp:
                data = await resp.json()
        
        image_urls = extract_urls_from_results(data.get("result"))
        if not image_urls:
            return await status_msg.edit(f"{ggl} **Gambar tidak ditemukan.**")
        
        await status_msg.edit(f"{prs} **📥 Uploading...**")
        for img_url in image_urls[:2]: # Kirim 2 saja biar rapi
            await client.send_photo(message.chat.id, photo=img_url, caption=f"{sks} **Result:** `{query}`")
        await status_msg.delete()
    except Exception:
        await status_msg.edit(f"{ggl} **Terjadi kesalahan.**")

# ============================================
# GIF SEARCH
# ============================================
@PY.UBOT("gif")
@PY.TOP_CMD
async def gif_search(client, message):
    ggl = await EMO.GAGAL(client)
    prs = await EMO.PROSES(client)
    
    query = get_arg(message)
    if not query:
        return await message.reply(f"{ggl} **Gunakan:** `.gif [query]`")
    
    status_msg = await message.reply(f"{prs} **🔍 Searching GIF...**")
    try:
        x = await client.get_inline_bot_results(message.command[0], query)
        if not x.results:
            return await status_msg.edit(f"{ggl} **GIF tidak ditemukan.**")
        
        random_gif = random.choice(x.results)
        saved = await client.send_inline_bot_result(client.me.id, x.query_id, random_gif.id)
        saved_msg = await client.get_messages(client.me.id, int(saved.updates[1].message.id))
        
        await client.send_animation(message.chat.id, saved_msg.animation.file_id, caption=f"{prs} **Result:** `{query}`")
        await saved_msg.delete()
        await status_msg.delete()
    except Exception:
        await status_msg.edit(f"{ggl} **Terjadi kesalahan.**")


