import asyncio
import pytz
from datetime import datetime
from pyrogram.types import InputMediaPhoto
from fanzy import *
from fanzy.core.database import get_vars, set_vars, remove_from_vars

__MODULE__ = "done"
__HELP__ = """
<b>📁 DAFTAR PERINTAH</b>

<b>🔧 Commands:</b>
├ <code>{0}done</code> - Konfirmasi transaksi
├ <code>{0}setlog</code> - Set-log done
├ <code>{0}log</code> - melihat semua list log
╰ <code>{0}dellog</code> - delete log done

<b>📝 Format penggunaan:</b>
╰ <code>{0}done</code> item,harga,payment
"""

def limit_name(name, max_char=18):
    if len(name) > max_char:
        return name[:max_char] + "..."
    return name
    
@PY.UBOT("setlog")
async def set_log_done(client, message):
    chat_id = message.chat.id
    chat_title = message.chat.title or "Private Chat"
    await set_vars(client.me.id, "DONE_LOG_ID", chat_id)
    await message.reply(f"<b>✅ Channel log berhasil diatur ke:</b>\n<code>{chat_title}</code> (<code>{chat_id}</code>)")

@PY.UBOT("log")
async def list_log_done(client, message):
    log_channel = await get_vars(client.me.id, "DONE_LOG_ID")
    if not log_channel:
        return await message.reply("<b>❌ Belum ada channel log yang diatur.</b>")    
    try:
        chat = await client.get_chat(int(log_channel))
        target = f"{chat.title} (<code>{chat.id}</code>)"
    except:
        target = f"<code>{log_channel}</code>"        
    await message.reply(f"<b>📋 Channel Log Saat Ini:</b>\n╰ {target}")

@PY.UBOT("dellog")
async def delete_log_done(client, message):
    log_channel = await get_vars(client.me.id, "DONE_LOG_ID")
    if not log_channel:
        return await message.reply("<b>❌ Konfigurasi log memang tidak ada.</b>")    
    await set_vars(client.me.id, "DONE_LOG_ID", "")
    await message.reply("<b>✅ Berhasil menghapus konfigurasi channel log.</b>")

@PY.UBOT("done")
async def done_command(client, message):
    izzy_ganteng = await message.reply("<blockquote>⏳ Processing...</blockquote>")
    log_channel = await get_vars(client.me.id, "DONE_LOG_ID")    
    try:
        args = get_arg(message)
        if not args or "," not in args:
            return await izzy_ganteng.edit("<blockquote>❌ Format salah!\nContoh: <code>.done item,harga,payment</code></blockquote>")
        parts = args.split(",", 2)
        name_item = parts[0].strip()
        price = parts[1].strip()
        payment = parts[2].strip() if len(parts) > 2 else "Lainnya"        
        show_customer = False
        customer_name = ""
        customer_id = ""
        customer_username = ""
        if message.reply_to_message:
            if message.reply_to_message.from_user.id != client.me.id:
                show_customer = True
                target = message.reply_to_message.from_user
                customer_name = limit_name(target.first_name, 18)
                customer_id = target.id
                customer_username = f"@{target.username}" if target.username else "Tidak ada"                              
        owner = "@slyt6c"
        tz_jkt = pytz.timezone('Asia/Jakarta')
        now = datetime.now(tz_jkt) 
        tanggal = now.strftime("%d %B %Y") 
        waktu = now.strftime("%H:%M:%S WIB")        
        caption = "<b>「✅ TRANSAKSI SUCCESS」</b>\n\n"
        caption += "<blockquote><b>Terimakasih telah order di kami</b> berikut ini  <b>detail  orderan anda!</b></blockquote>\n\n"        
        if show_customer:
            caption += f"👤 <b>Nama:</b> {customer_name}\n"
            caption += f"🆔 <b>ID:</b> <code>{customer_id}</code>\n"
            caption += f"💢 <b>Username:</b> {customer_username}\n"             
        caption += f"📦 <b>Barang:</b> {name_item}\n"
        caption += f"💸 <b>Harga:</b> IDR {price}\n"
        caption += f"💳 <b>Payment:</b> {payment}\n"
        caption += f"📅 <b>Date:</b> {tanggal}\n"
        caption += f"⏰ <b>Time:</b> {waktu}\n\n"
        caption += f"<b> Nak Order? Pm Me!</b> {owner}\n"
        caption += f"<b>━━━━━━━━━━━━━━━━━━━</b>\n"
        caption += f"<blockquote><b><i>✅ Thanks telah order dikami!</i></b></blockquote>"
        if message.reply_to_message and message.reply_to_message.media_group_id:
            media_group = await client.get_media_group(message.chat.id, message.reply_to_message.id)
            album = []
            for i, m in enumerate(media_group):
                if m.photo:
                    album.append(InputMediaPhoto(m.photo.file_id, caption=caption if i == 0 else ""))            
            await client.send_media_group(chat_id=message.chat.id, media=album)
            if log_channel:
                await client.send_media_group(chat_id=int(log_channel), media=album)       
        elif message.reply_to_message and message.reply_to_message.photo:
            photo_id = message.reply_to_message.photo.file_id
            await client.send_photo(chat_id=message.chat.id, photo=photo_id, caption=caption)
            if log_channel:
                await client.send_photo(chat_id=int(log_channel), photo=photo_id, caption=caption)
        else:
            await client.send_message(chat_id=message.chat.id, text=caption)
            if log_channel:
                await client.send_message(chat_id=int(log_channel), text=caption)
        await izzy_ganteng.delete()
        await message.delete()        
    except Exception as e:
        await izzy_ganteng.edit(f"<b>❌ Error:</b> <code>{e}</code>")