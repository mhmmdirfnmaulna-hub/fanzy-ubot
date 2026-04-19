import asyncio
import os
import requests
import aiohttp
from pyrogram.enums import ChatAction
from pyrogram.types import Message
from fanzy import *

__MODULE__ = "downloader"
__HELP__ = """
<b>📥 DOWNLOADER TOOLS</b>
├ <code>{0}pin</code> - Download Pinterest
├ <code>{0}tt</code> - Vidio Tiktok No Wm
├ <code>{0}mp3</code> - Audio TikTok
╰ <code>{0}spotify</code> - Musik Spotify
"""


# ============================================
# KONFIGURASI
# ============================================
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# API Keys
PINTEREST_API_KEY = "fanzy"
API_KEY = "fanzy"
PINTEREST_BASE_URL = "https://api.botcahx.eu.org/api/download/pinterest"
SPOTIFY_SEARCH_URL = "https://api.botcahx.eu.org/api/search/spotify"
SPOTIFY_DOWNLOAD_URL = "https://api.botcahx.eu.org/api/download/spotify"


# ============================================
# PINTEREST
# ============================================
@PY.UBOT("pinterest")
@PY.UBOT("pin")
@PY.TOP_CMD
async def pinterest_download(client, message: Message):
    ggl = await EMO.GAGAL(client)
    prs = await EMO.PROSES(client)
    sks = await EMO.BERHASIL(client)    
    if len(message.command) < 2:
        return await message.reply_text(
            f"{ggl} **EX:** pinterest [link pinterest]"
        )
    url = message.command[1]
    if "pinterest" not in url and "pin.it" not in url:
        return await message.reply_text(f"{ggl} URL tidak valid! Pastikan link dari pinterest.com atau pin.it")    
    status_msg = await message.reply_text(f"{prs} **📥 Downloading....**")    
    try:
        api_url = f"{PINTEREST_BASE_URL}?url={url}&apikey={PINTEREST_API_KEY}"        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=30) as resp:
                if resp.status != 200:
                    return await status_msg.edit(f"{ggl} Gagal koneksi ke API (HTTP {resp.status})")                
                data = await resp.json()        
        if not data.get("result") or not data["result"].get("data"):
            return await status_msg.edit(f"{ggl} Tidak ada data yang ditemukan")        
        result = data["result"]["data"]
        media_type = result.get("media_type", "")
        image_url = result.get("image")
        video_url = result.get("video")
        title = result.get("title", "Pinterest Media")        
        await status_msg.edit(f"{prs} **📥 Mengirim media...**")        
        if video_url:
            await client.send_video(
                chat_id=message.chat.id,
                video=video_url,
                supports_streaming=True,
                reply_to_message_id=message.id
            )
        elif image_url:
            await client.send_photo(
                chat_id=message.chat.id,
                photo=image_url,
                reply_to_message_id=message.id
            )
        else:
            await status_msg.edit(f"{ggl} Tidak ada gambar atau video yang ditemukan")
            return        
        await status_msg.delete()        
    except asyncio.TimeoutError:
        await status_msg.edit(f"{ggl} Request timeout, server terlalu lambat")
    except aiohttp.ClientConnectorError:
        await status_msg.edit(f"{ggl} Gagal koneksi ke server")
    except Exception as e:
        await status_msg.edit(f"{ggl} Error: {str(e)[:100]}")


# ============================================
# TIKTOK
# ============================================
async def download_tiktok_api(url, as_audio=False):
    """Download TikTok pake API publik (TikWM)"""
    try:
        api_url = "https://www.tikwm.com/api/"        
        response = requests.post(
            api_url,
            data={"url": url},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        )        
        if response.status_code != 200:
            return None, f"API Error: {response.status_code}"        
        data = response.json()        
        if not data.get("data"):
            return None, "Gagal ambil data dari API"        
        video_data = data["data"]        
        if as_audio:
            if video_data.get("music_info"):
                download_url = video_data["music_info"].get("play")
            else:
                download_url = video_data.get("play")
        else:
            download_url = video_data.get("play")        
        if not download_url:
            return None, "URL download tidak ditemukan"        
        file_ext = "mp3" if as_audio else "mp4"
        file_name = f"{DOWNLOAD_DIR}/tt_{video_data['id']}.{file_ext}"        
        file_resp = requests.get(download_url, stream=True, timeout=30)        
        if file_resp.status_code != 200:
            return None, f"Gagal download file: {file_resp.status_code}"        
        with open(file_name, 'wb') as f:
            for chunk in file_resp.iter_content(chunk_size=1024):
                f.write(chunk)        
        metadata = {
            "title": video_data.get("title", "TikTok Video")[:100],
            "uploader": video_data.get("author", {}).get("nickname", "Unknown"),
            "duration": video_data.get("duration", 0),
            "views": video_data.get("play_count", 0),
            "likes": video_data.get("digg_count", 0),
            "comments": video_data.get("comment_count", 0),
            "shares": video_data.get("share_count", 0),
        }        
        return file_name, metadata        
    except Exception as e:
        return None, str(e)


@PY.UBOT("tiktok")
@PY.UBOT("tt")
@PY.TOP_CMD
async def tiktok_download(client, message: Message):
    ggl = await EMO.GAGAL(client)
    prs = await EMO.PROSES(client)
    sks = await EMO.BERHASIL(client)    
    if len(message.command) < 2:
        return await message.reply(f"{ggl} Gunakan: .tiktok [link TikTok]")    
    url = message.command[1]    
    if "tiktok.com" not in url and "tiktok" not in url:
        return await message.reply(f"{ggl} Link TikTok tidak valid!")    
    status = await message.reply(f"{prs} 📥 Downloading....")    
    try:
        file_path, metadata = await download_tiktok_api(url, as_audio=False)        
        if not file_path or not os.path.exists(file_path):
            return await status.edit(f"{ggl} Gagal download: {metadata}")  
        # Ambil data tambahan dari metadata
        comments = f"{metadata['comments']:,}".replace(",", ".")
        shares = f"{metadata['shares']:,}".replace(",", ".")                  
        views = f"{metadata['views']:,}".replace(",", ".")
        likes = f"{metadata['likes']:,}".replace(",", ".")        
        
        caption = f"""
╭{sks} **TikTok Downloader**
├⏱️ **Durasi:** {metadata['duration']//60}:{metadata['duration']%60:02d}
├👀 **Views:** {views}
├❤️ **Likes:** {likes}
├💬 **Command:** {comments}
├〽️ **Share:** {shares}
╰🔗 **Link:** <a href='{url}'>Click Here</a>
"""        
        await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)        
        await client.send_video(
            message.chat.id,
            video=file_path,
            caption=caption,
            duration=metadata['duration'],
            supports_streaming=True,
            reply_to_message_id=message.id
        )        
        os.remove(file_path)
        await status.delete()        
    except Exception as e:
        await status.edit(f"{ggl} Error: {str(e)}")
        
        
@PY.UBOT("mp3")
@PY.TOP_CMD
async def tiktok_audio(client, message: Message):
    ggl = await EMO.GAGAL(client)
    prs = await EMO.PROSES(client)
    sks = await EMO.BERHASIL(client)    
    if len(message.command) < 2:
        return await message.reply(f"{ggl} Gunakan: .mp3 [link TikTok]")    
    url = message.command[1]    
    if "tiktok.com" not in url:
        return await message.reply(f"{ggl} Link TikTok tidak valid!")    
    status = await message.reply(f"{prs} 📥 Downloading...")    
    try:
        file_path, metadata = await download_tiktok_api(url, as_audio=True)        
        if not file_path or not os.path.exists(file_path):
            return await status.edit(f"{ggl} Gagal download: {metadata}")        
            
        views = f"{metadata.get('views', 0):,}".replace(",", ".")
        likes = f"{metadata.get('likes', 0):,}".replace(",", ".")
        comments = f"{metadata.get('comments', 0):,}".replace(",", ".")
        shares = f"{metadata.get('shares', 0):,}".replace(",", ".")
               
        caption = f"""
╭{sks} **Succes Unduh Audio!**
├⏱️ **Durasi:** {metadata['duration']//60}:{metadata['duration']%60:02d}
├👀 **Views:** {views}
├❤️ **Likes:** {likes}
├💬 **Command:** {comments}
├〽️ **Share:** {shares}
╰🔗 **Link:** <a href='{url}'>Click Here</a>
"""        
        await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_AUDIO)        
        await client.send_audio(
            message.chat.id,
            audio=file_path,
            caption=caption,
            performer=metadata['uploader'],
            title=metadata['title'],
            duration=metadata['duration'],
            reply_to_message_id=message.id
        )        
        os.remove(file_path)
        await status.delete()        
    except Exception as e:
        await status.edit(f"{ggl} Error: {str(e)}")


@PY.UBOT("spotify")
@PY.TOP_CMD
async def spotify_search(client, message):
    ggl = await EMO.GAGAL(client)
    prs = await EMO.PROSES(client)
    sks = await EMO.BERHASIL(client)
    jam = await EMO.JAM(client)    
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply_text(f"{ggl} Gunakan format: .spotify <judul lagu>")    
    proses_msg = await message.reply_text(f"{prs} 🔎 Mencari lagu...")    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }    
    try:
        search_url = f"https://api.botcahx.eu.org/api/search/spotify?query={query}&apikey={API_KEY}"
        search_response = requests.get(search_url, headers=headers, timeout=450)        
        if search_response.status_code == 429:
            await proses_msg.edit_text(
                f"{jam} **Limit apikey telah tercapai!**")
            return     
        if search_response.status_code != 200:
            await proses_msg.edit_text(f"{ggl} Gagal koneksi ke API (HTTP {search_response.status_code})")
            return        
        search_data = search_response.json()        
        if search_data.get("message") and "limit" in search_data.get("message", "").lower():
            await proses_msg.edit_text(
                f"{jam} **Limit apikey telah tercapai!**")
            return        
        if not search_data.get("status"):
            await proses_msg.edit_text(f"{ggl} Lagu tidak ditemukan")
            return        
        result = search_data.get("result", {})
        tracks = result.get("data", []) if isinstance(result, dict) else []        
        if not tracks:
            await proses_msg.edit_text(f"{ggl} Lagu tidak ditemukan")
            return        
        track_list = []
        for idx, track in enumerate(tracks[:5], 1):
            title = track.get("title", "Unknown")
            duration = track.get("duration", "?")
            track_list.append(f"{idx}. {title} ({duration})")        
        await proses_msg.edit_text(
            f"{prs} **Silakan Pilih Lagu**\n\n" + "\n".join(track_list) + 
            f"\n\nKetik nomor (1-5) dalam 30 detik!"
        )        
        try:
            choice_msg = await client.listen(message.chat.id, timeout=120)
            choice = int(choice_msg.text.strip())
            if choice < 1 or choice > len(tracks[:5]):
                await proses_msg.edit_text(f"{ggl} Pilihan tidak valid!")
                return
        except asyncio.TimeoutError:
            await proses_msg.edit_text(f"{ggl} Waktu habis! Silakan coba lagi.")
            return
        except ValueError:
            await proses_msg.edit_text(f"{ggl} Pilihan harus berupa angka!")
            return        
        selected_track = tracks[choice - 1]
        track_url = selected_track.get("url")
        track_title = selected_track.get("title", "Unknown")
        track_duration = selected_track.get("duration", "0:00")
        artist_name = selected_track.get("artist", "Unknown")        
        await proses_msg.edit_text(f"{prs} 📥 Mengunduh lagu....")        
        download_url = f"https://api.botcahx.eu.org/api/download/spotify?url={track_url}&apikey={API_KEY}"        
        await asyncio.sleep(2)        
        download_response = requests.get(download_url, headers=headers, timeout=250)        
        if download_response.status_code == 429:
            await proses_msg.edit_text(
                f"{jam} **Limit apikey telah tercapai!**"
            )
            return        
        if download_response.status_code != 200:
            await proses_msg.edit_text(f"{ggl} Gagal mengunduh lagu (HTTP {download_response.status_code})")
            return        
        download_data = download_response.json()        
        if download_data.get("message") and "limit" in download_data.get("message", "").lower():
            await proses_msg.edit_text(
                f"{jam} **Limit apikey telah tercapai!**")
            return        
        if not download_data.get("status"):
            error_msg = download_data.get("message", "Unknown error")
            if "limit" in error_msg.lower():
                await proses_msg.edit_text(
                f"{jam} **Limit apikey telah tercapai!**")
                return
            else:
                await proses_msg.edit_text(f"{ggl} Gagal download: {error_msg}")
                return        
        result_data = download_data.get("result", {})
        data_result = result_data.get("data", result_data)        
        file_url = None
        if isinstance(data_result, dict):
            url_field = data_result.get("url", {})
            if isinstance(url_field, str):
                file_url = url_field
            elif isinstance(url_field, dict):
                file_url = url_field.get("url") or url_field.get("link")
            if not file_url:
                file_url = data_result.get("download_url") or data_result.get("link")
        elif isinstance(data_result, list):
            file_url = data_result[0].get("url") if data_result else None        
        if not file_url:
            await proses_msg.edit_text(
                f"{ggl} **Tidak dapat menemukan URL download!**"
            )
            return        
        user_id = message.from_user.id
        audio_path = f"{DOWNLOAD_DIR}/spotify_{user_id}.mp3"        
        await proses_msg.edit_text(f"{prs} 📥 Mengunduh file audio...")        
        r = requests.get(file_url, headers=headers, stream=True, timeout=120)        
        if r.status_code != 200:
            await proses_msg.edit_text(f"{ggl} Gagal mengunduh file (HTTP {r.status_code})")
            return        
        with open(audio_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        caption = f"""
╭ {sks} **{track_title}**
├👤 **Artist:** {artist_name}
╰⏳ **Durasi:** {track_duration}
"""        
        await client.send_audio(
            chat_id=message.chat.id,
            audio=audio_path,
            title=track_title,
            performer=artist_name,
            caption=caption,
            reply_to_message_id=message.id
        )        
        os.remove(audio_path)
        await proses_msg.delete()        
    except Exception as e:
        await proses_msg.edit_text(f"{ggl} Error: {str(e)[:200]}")
        
