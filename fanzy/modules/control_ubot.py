import asyncio
import importlib
import sys
from datetime import datetime
from fanzy.core.database.pref import get_pref, set_pref, rem_pref, clear_prefix_cache
from pyrogram.enums import SentCodeType
from pyrogram.errors import *
from pyrogram.types import *
from pyrogram.raw import functions
from pyrogram.raw.functions.messages import DeleteHistory, StartBot
from pyrogram.errors.exceptions.not_acceptable_406 import ChannelPrivate

from fanzy import *

__MODULE__ = "Control"
__HELP__ = """
📋 <b>DAFTAR PERINTAH</b>

╭ <code>{0}prefix</code> - Merubah Prefixs
├ <code>{0}emo</code> - Ubah emoji settings
╰ <code>{0}limit</code> - Cek account limit

📝 <b>Examples:</b>
├ <code>{0}prefix</code>  .
├ <code>{0}emo</code>  pong 🏓
╰ <code>{0}limit</code> 
"""


# ============================================
# PREFIX
# ============================================
@PY.UBOT("prefix")
@PY.TOP_CMD
async def _(client, message):
    import time
    
    prs = await EMO.PROSES(client)
    brhsl = await EMO.BERHASIL(client)
    ggl = await EMO.GAGAL(client)
    
    if len(message.command) < 2:
        return await message.reply(f"{ggl} Usage: <code>prefix [symbols]</code>")
    
    ub_prefix = []
    for prefix in message.command[1:]:
        if prefix.lower() == "no":
            ub_prefix.append("")
        else:
            ub_prefix.append(prefix)
    
    try:
        start_time = time.time()
        
        # Simpan ke database dan update cache
        await set_pref(message.from_user.id, ub_prefix)
        
        db_time = (time.time() - start_time) * 1000
        
        parsed_prefix = " ".join(f"`{p}`" for p in ub_prefix if p)
        
        await message.reply(
            f"<b>✅ Prefix Change To:</b> {parsed_prefix}\n\n"
            f"Awas Kalau <b>mengubah prefix</b>\n"
            f"Jangan sampai lupa apa <b>prefix</b>\n"
            f"<b>Yang kalian ubah.</b> Nanti malah\n"
            f"Gak bisa pakai <b>Userbot</b> kalian !\n"
            f"<b><blockquote>✨ Power By Fanzy Userbotz</b></blockquote>"
        )
    except Exception as error:
        await message.reply(str(error))


# ============================================
# LIMIT
# ============================================
@PY.UBOT("limit")
@PY.TOP_CMD
async def _(client, message):
    ggl = await EMO.GAGAL(client)
    sks = await EMO.BERHASIL(client)
    prs = await EMO.PROSES(client)
    pong = await EMO.PING(client)
    tion = await EMO.MENTION(client)
    yubot = await EMO.UBOT(client)
    
    await client.unblock_user("SpamBot")
    bot_info = await client.resolve_peer("SpamBot")
    msg = await message.reply(f"{prs} Processing...")
    
    response = await client.invoke(
        StartBot(
            bot=bot_info,
            peer=bot_info,
            random_id=client.rnd_id(),
            start_param="start",
        )
    )
    
    await asyncio.sleep(1)
    await msg.delete()
    
    status = await client.get_messages("SpamBot", response.updates[1].message.id + 1)
    
    if status and hasattr(status, "text"):
        pjg = len(status.text)
        print(pjg)
        
        if pjg <= 100:
            if client.me.is_premium:
                text = f"""
<b>📊 ACCOUNT STATUS</b>

📌 <b>Status premium:</b> <code>True</code>
⚠️ <b>Limit:</b> <code>Tidak dibatasi</code>
<blockquote><b>⚡ Power By Fanzy Userbot</b></blockquote>
"""
            else:
                text = f"""
<b>📊 ACCOUNT STATUS</b>

📌 <b>Status premium:</b> <code>False</code>
⚠️ <b>Limit:</b> <code>Tidak Dibatasi</code>
<blockquote><b>⚡ Power By Fanzy Userbot</b></blockquote>
"""
            await client.send_message(message.chat.id, text)
            return await client.invoke(DeleteHistory(peer=bot_info, max_id=0, revoke=True))
        else:
            if client.me.is_premium:
                text = f"""
<b>📊 ACCOUNT STATUS</b>

📌 <b>Status Premium:</b> <code>True</code>
⚠️ <b>Limit:</b> <code>Anda Dibatasi</code>
<blockquote><b>⚡ Power By Fanzy Userbot</b></blockquote>
"""
            else:
                text = f"""
<b>📊 ACCOUNT STATUS</b>

📌 <b>Status premium:</b> <code>False</code>
⚠️ <b>Limit:</b> <code>Anda Dibatasi</code>
<blockquote><b>⚡ Power By Fanzy Userbot</b></blockquote>
"""
            await client.send_message(message.chat.id, text)
            return await client.invoke(DeleteHistory(peer=bot_info, max_id=0, revoke=True))
    else:
        print("Status tidak valid atau status.text tidak ada")


# ============================================
# EMOJI
# ============================================
@PY.UBOT("emo")
@PY.TOP_CMD
async def _(client, message):
    prs = await EMO.PROSES(client)
    brhsl = await EMO.BERHASIL(client)
    ggl = await EMO.GAGAL(client)
    
    msg = await message.reply(f"{prs} Processing...", quote=True)

    # CEK APAKAH USER YANG MENGGUNAKAN PERINTAH ADALAH PREMIUM
    user_id = message.from_user.id
    
    # Ambil daftar user premium dari database
    premium_users = await get_list_from_vars(client.me.id, "PREM_USERS")
    ultra_premium_users = await get_list_from_vars(client.me.id, "ULTRA_PREM")
    
    # Cek apakah user premium
    is_premium_user = user_id in premium_users or user_id in ultra_premium_users or user_id == OWNER_ID
    
    if not is_premium_user:
        return await msg.edit(f"{ggl} Premium feature only!")

    if len(message.command) < 3:
        return await msg.edit(f"{ggl} Usage: <code>emo [query] [emoji]</code>\n\n<b>Query Emoji:</b>\npong\nowner\nubot\nproses\ngcast\nsukses\ngagal\ncatatan\ngroup\nmenunggu\nalasan\nwaktu\nafk")

    # Query mapping
    query_mapping = {
        "pong": "EMOJI_PING",
        "owner": "EMOJI_MENTION",
        "ubot": "EMOJI_USERBOT",
        "proses": "EMOJI_PROSES",
        "gcast": "EMOJI_BROADCAST",
        "sukses": "EMOJI_BERHASIL",
        "gagal": "EMOJI_GAGAL",
        "catatan": "EMOJI_KETERANGAN",
        "group": "EMOJI_GROUP",
        "menunggu": "EMOJI_MENUNGGU",
        "alasan": "EMOJI_ALASAN",
        "waktu": "EMOJI_WAKTU",
        "afk": "EMOJI_AFKA",
    }
    
    # Ambil mapping dan value
    mapping = message.command[1].lower()
    value = " ".join(message.command[2:])
    
    if mapping not in query_mapping:
        return await msg.edit(f"{ggl} Query not found!\n\nAvailable: {', '.join(query_mapping.keys())}")
    
    query_var = query_mapping[mapping]
    emoji_id = None
    
    # Cek custom emoji
    if message.entities:
        for entity in message.entities:
            if hasattr(entity, 'custom_emoji_id') and entity.custom_emoji_id:
                emoji_id = entity.custom_emoji_id
                break
    
    if emoji_id:
        await set_vars(client.me.id, query_var, emoji_id)
        await msg.edit(
            f"<b>✅ Emoji saved!</b>\n\n<b>Query:</b> <code>{mapping}</code>\n<b>Emoji:</b> <emoji id={emoji_id}>{value}</emoji>\n<blockquote><b>⚡ Power By Fanzy Userbot</b></blockquote>"
        )
    else:
        await msg.edit(f"{ggl} Custom emoji not found!\nSend a premium emoji.")