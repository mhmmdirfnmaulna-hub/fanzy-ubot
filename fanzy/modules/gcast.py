#Version Vinal
import asyncio
from fanzy.config import *
import random
import re
from gc import get_objects
from asyncio import sleep
from datetime import datetime
from pyrogram.errors import (
    SlowmodeWait, 
    FloodWait, 
    RPCError, 
    ChatWriteForbidden,
    ChatAdminRequired,
    ChannelPrivate,
)
from fanzy.core.database import (
    get_vars, 
    set_vars, 
    add_to_vars, 
    remove_from_vars, 
    get_list_from_vars
)
from fanzy.core.helpers.tools import (
    get_arg, 
    extract_type_and_msg, 
    get_data_id, 
    extract_type_and_text
)
from pyrogram.enums import ChatType
from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent
from pyrogram.raw.functions.messages import DeleteHistory, StartBot
from fanzy import PY, EMO

__MODULE__ = "Broadcast"
__HELP__ = """
📣 <b>TOOLS BROADCAST</b>
├ <b><code>{0}gcast</b></code> - Gcast all usr/gb/ch
├ <b><code>{0}stop</b></code> - Stop proses gcast 
├ <b><code>{0}cfd</b></code> - Gcast secara forward
├ <b><code>{0}auto</b></code> - Gcast otomatis 
├ <code>{0}shedit</code> - Shadow edit on/off
├ <code>{0}wm</code> - Watermark on/off
├ <code>{0}setwm</code> - Set watermark
╰ <b><code>{0}delay</b></code> - setdelay broadcast


🚫 <b>MANEJEMEN BLACKLIST</b>
├ <b><code>{0}addbl</b></code> - add blacklist group
├ <b><code>{0}unbl</b></code> - unblacklist group
├ <b><code>{0}listbl</b></code> - daftar blacklist 
╰ <b><code>{0}rallbl</b></code> - Clear all blacklist

📝 <b>Examples:</b>
├ <b><code>{0}gcast</b></code> group Hello world
├ <b><code>{0}gcast</b></code> all Hai 5 wm
├ <b><code>{0}auto</b></code> on
╰ <b><code>{0}delay</b></code> 3
"""

# ============================================
# VARIABEL GLOBAL
# ============================================
gcast_progress = [] 
last_gcast_time = {}
AG = []
LT = []

def spintax(text):
    """Mengacak kata: {Halo|Hai} -> Halo atau Hai"""
    while True:
        match = re.search(r'\{([^{}]+)\}', text)
        if not match:
            break
        choices = match.group(1).split('|')
        text = text.replace(match.group(0), random.choice(choices), 1)
    return text

# --- SAKLAR PENGATURAN (DATABASE) ---

@PY.UBOT("shedit")
async def set_shadow_toggle(client, message):
    args = get_arg(message).lower()
    status = True if args == "on" else False
    await set_vars(client.me.id, "SHADOW_GCAST", status)
    await message.reply(f"<b>👥 Shadow Edit:</b> <code>{'ON' if status else 'OFF'}</code>")

@PY.UBOT("wm")
async def set_wm_toggle(client, message):
    args = get_arg(message).lower()
    status = True if args == "on" else False
    await set_vars(client.me.id, "WM_GCAST", status)
    await message.reply(f"<b>💧 Watermark :</b> <code>{'ON' if status else 'OFF'}</code>")

# --- SAKLAR PENGATURAN ---

@PY.UBOT("setwm")
async def set_custom_wm(client, message):
    args = get_arg(message)
    if not args: 
        return await message.reply("<b>❌ Masukkan teks Wm/ketik <code>default</code></b>")    
    
    # Logic Setwm Default: Jika ketik 'default', hapus data di DB
    if args.lower() == "default":
        await set_vars(client.me.id, "CUSTOM_WM_TEXT", "") 
        return await message.reply("<b>🔄 Wm Di ubah ke dafault!</b>")        
    
    # Simpan teks custom ke DB
    await set_vars(client.me.id, "CUSTOM_WM_TEXT", args)
    await message.reply(f"<b>📝 Berhasil Ubah Watermak Ke</b>\n<code>{args}</code>")

@PY.UBOT("delay")
async def set_delay_gcast(client, message):
    args = get_arg(message)
    if not args.isdigit(): 
        return await message.reply("<b>❌ Masukkan angka delay</b>")
    
    await set_vars(client.me.id, "GROUP_DELAY", int(args))
    status = f"{args}s" if args != "0" else "No Delay"
    await message.reply(f"<b>⏱️ Delay Di Ubah menjadi</b> <code>{status}</code>")

@PY.UBOT("gcast")
@PY.TOP_CMD
async def gcast_handler(client, message):
    start_time = datetime.now()
    user_id = client.me.id    
    if user_id in gcast_progress:
        return await message.reply("<b>❌ Masih ada broadcast yang berjalan!</b>")
    command, text_from_cmd = extract_type_and_msg(message)    
    valid_commands = ["group", "all", "users"]    
    if not command or command not in valid_commands:
        return await message.reply(f"<b>❌ Gunakan:</b> <code>.gcast [group/all/users] [teks]</code>")        
    now = datetime.now()
    if user_id in last_gcast_time:
        if (now - last_gcast_time[user_id]).total_seconds() / 60 >= 5:
            await set_vars(user_id, "GROUP_DELAY", 0)    
    last_gcast_time[user_id] = now
    gcast_progress.append(user_id)        
    use_shadow = await get_vars(user_id, "SHADOW_GCAST")
    use_wm = await get_vars(user_id, "WM_GCAST")
    custom_wm = await get_vars(user_id, "CUSTOM_WM_TEXT")
    group_delay = await get_vars(user_id, "GROUP_DELAY") or 0
    selected_wm = custom_wm if custom_wm else "Broadcast By Fanzy Userbot"
    msg_markup = None
    if message.reply_to_message:
        target = message.reply_to_message
        raw_text = target.text.html if target.text else (target.caption.html if target.caption else "")
        msg_markup = target.reply_markup
    else:
        raw_text = text_from_cmd or ""
    if not raw_text.strip():
        if user_id in gcast_progress: gcast_progress.remove(user_id)
        return await message.reply("<b>❌ Pesan tidak ditemukan!</b>")
    chats = await get_data_id(client, command)
    total_chats = len(chats)    
    if total_chats == 0:
        if user_id in gcast_progress: gcast_progress.remove(user_id)
        return await message.reply("<b>❌ Tidak ditemukan chat untuk broadcast!</b>")
    gcs = await message.reply("<b>◜ Prosess Gcast....</b>")    
    db_blacklist = await get_list_from_vars(user_id, "BL_ID")
    blacklist = db_blacklist if db_blacklist else []     
    done, failed = 0, 0
    wm_text = f"\n\n<blockquote><i>-- <b>{selected_wm}</b> --</i></blockquote>" if use_wm else ""    
    animation_chars = ['◜', '◠', '◝', '◞', '◡', '◟']
    last_update_time = datetime.now()
    for i, chat_id in enumerate(chats, 1):
        if user_id not in gcast_progress: break
        if chat_id in blacklist or chat_id in globals().get('BLACKLIST_CHAT', []):
            total_chats -= 1
            continue
        msg_to_send = spintax(raw_text) + wm_text
        try:
            for attempt in range(3):
                try:
                    if use_shadow:
                        shadow = await client.send_message(chat_id, "•")
                        await asyncio.sleep(0.3)
                        await shadow.edit(msg_to_send, reply_markup=msg_markup)
                    else:
                        await client.send_message(chat_id, msg_to_send, reply_markup=msg_markup)
                    done += 1
                    break 
                except FloodWait as e:
                    await asyncio.sleep(e.value + 2)
                    continue 
                except (ChatWriteForbidden, ChatAdminRequired, UserBannedInChannel):
                    try:
                        if chat_id < 0: await client.leave_chat(chat_id)
                    except: pass
                    failed += 1
                    break
                except Exception:
                    failed += 1
                    break
        except: failed += 1
        if (datetime.now() - last_update_time).total_seconds() >= 2.0 or i == total_chats:
            char = animation_chars[i % len(animation_chars)]
            pct = min(int((i / max(total_chats, 1)) * 100), 100)
            bar = "■" * int(pct / 10) + "□" * (10 - int(pct / 10))
            try:
                await gcs.edit(
                    f"<b>{char} Gcast Processing...</b>\n"
                    f"<code>[{bar}]</code> <b>{pct}%</b>\n\n"
                    f"✅ <b>Berhasil:</b> <code>{done}</code>\n"
                    f"❌ <b>Gagal:</b> <code>{failed}</code>\n"
                    f"📂 <b>Target:</b> <code>{i}/{total_chats}</code>"
                )
                last_update_time = datetime.now()
            except: pass                        
        if group_delay > 0:
            await asyncio.sleep(int(group_delay) + random.randint(1, 3))            
    if user_id in gcast_progress: gcast_progress.remove(user_id)        
    duration = (datetime.now() - start_time).seconds
    m, s = divmod(duration, 60)
    waktu_proses = f"{s}d" if m == 0 else f"{m}m {s}d"
    status_list = []
    status_list.append(f"⏳ <b>Delay :</b> <code>{group_delay if group_delay > 0 else 'No Delay'}</code>")
    status_list.append(f"⏱️ <b>Durasi :</b> <code>{waktu_proses}</code>")    
    if len(blacklist) > 0:
        status_list.append(f"🚫 <b>Blacklist :</b> <code>{len(blacklist)}</code>")    
    if use_shadow:
        status_list.append(f"👤 <b>Shadow :</b> <code>On</code>")        
    if use_wm:
        status_list.append(f"💧 <b>Watermark :</b> <code>On</code>")        
    extra_info = "\n".join(status_list)    
    report = (
        f"<blockquote><b>📡 BROADCAST COMPLETED</b></blockquote>\n"
        f"✅ <b>Berhasil :</b> <code>{done}</code>/{total_chats}\n"
        f"❌ <b>Gagal :</b> <code>{failed}</code>\n"
        f"🆔 <b>Task ID :</b> {message.id}\n"
        f"📌 <b>Type :</b> {command}\n"
        f"{extra_info}\n"
        f"<blockquote><b>─ Fanzy Userbot Premium ─</b></blockquote>"
    )
    
    try:
        await gcs.edit(report)
    except:
        await message.reply(report)

# --- FUNGSI STOP ---
@PY.UBOT("stop")
async def stop_gcast(client, message):
    if client.me.id in gcast_progress:
        gcast_progress.remove(client.me.id) # Pakai remove karena ini LIST
        await message.reply("<b>✅ Sesi Broadcast dihentikan!</b>")
    else:
        await message.reply("<b>❌ Tidak ada sesi berjalan.</b>")

# ============================================
# BROADCAST FORWARD
# ============================================
@PY.UBOT("cfd")
@PY.TOP_CMD
async def forward_broadcast(client, message):
    if not message.reply_to_message:
        return await message.reply("<b>❌ Mohon reply ke pesan yang ingin di-forward!</b>")
    
    prs = await EMO.PROSES(client)
    gcs = await message.reply(f"{prs} Processing...")
    
    command, _ = extract_type_and_msg(message)
    if command not in ["group", "users", "all"]:
        command = "group" # Default

    chats = await get_data_id(client, command)
    blacklist = await get_list_from_vars(client.me.id, "BL_ID")

    done, failed = 0, 0
    for chat_id in chats:
        if chat_id in blacklist or chat_id in BLACKLIST_CHAT:
            continue
        try:
            await message.reply_to_message.forward(chat_id)
            done += 1
            await asyncio.sleep(1.0) # Jeda tipis agar tidak spam
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.reply_to_message.forward(chat_id)
            done += 1
        except Exception:
            failed += 1

    await gcs.delete()    
    msg = f"""
<blockquote><b>📡 SUCCESFULY FORWARD</b></blockquote>
<b>✅ Success:</b> <code>{done}</code>
<b>❌ Failed:</b> <code>{failed}</code>
<b>🆔 Taks ID:</b> {message.id}
<b>📌 Type:</b> {command}
<b>⛔ Blacklist:</b> {len(blacklist)}
<blockquote><b>─ Fanzy Userbot Premium ─</b></blockquote>
"""
    return await message.reply(msg)
    
# ============================================
# BLACKLIST
# ============================================
@PY.UBOT("addbl")
@PY.TOP_CMD
async def add_blacklist(client, message):
    msg = await message.reply("<b>⏳ Processing...</b>")
    try:
        chat_id = message.chat.id
        chat_name = message.chat.title or "Private/Unknown"
        blacklist = await get_list_from_vars(client.me.id, "BL_ID")

        if chat_id in blacklist:
            txt = (
                f"<b>❌ Group Has Been Blacklisted!</b>\n"
                f"<b>╰ID:</b> <code>{chat_id}</code>"
            )
        else:
            await add_to_vars(client.me.id, "BL_ID", chat_id)
            txt = (
                f"<b>✅ Success Blacklist Group!</b>\n"
                f"<b>╰ID:</b> {chat_id}"
            )
        return await msg.edit(txt)        
    except SlowmodeWait as e:
        await asyncio.sleep(e.value)
        return await add_blacklist(client, message)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await add_blacklist(client, message)
    except Exception as error:
        return await msg.edit(str(error))

@PY.UBOT("unbl")
@PY.TOP_CMD
async def unblacklist(client, message):
    msg = await message.reply("<b>⏳ Processing...</b>")
    try:
        target_id = get_arg(message)
        chat_id = int(target_id) if target_id and target_id.replace("-", "").isdigit() else message.chat.id
        try:
            chat = await client.get_chat(chat_id)
            chat_name = chat.title or "Unknown"
        except:
            chat_name = "Manual ID"
        blacklist = await get_list_from_vars(client.me.id, "BL_ID")
        if chat_id not in blacklist:
            response = (
                f"<b>❌ Group is not on BL list!</b>\n"
                f"<b>╰ID:</b> {chat_id}"
            )
        else:
            await remove_from_vars(client.me.id, "BL_ID", chat_id)
            response = (
                f"<b>✅ Success Unblacklist group!</b>\n"
                f"<b>╰ID:</b> {chat_id}"
            )
        return await msg.edit(response)
    except Exception as error:
        return await msg.edit(f"<b>❌ Error:</b> <code>{str(error)}</code>")


@PY.UBOT("listbl")
@PY.TOP_CMD
async def list_blacklist(client, message):
    mzg = await message.reply("<b>⏳ Processing...</b>")

    blacklist = await get_list_from_vars(client.me.id, "BL_ID")
    total_blacklist = len(blacklist)

    if total_blacklist == 0:
        return await mzg.edit("<b>📋 Blacklist is empty!</b>")

    list_text = "<b>📋 DAFTAR BLACKLIST</b>\n\n"
    for chat_id in blacklist:
        try:
            chat = await client.get_chat(chat_id)
            list_text += f"├ {chat.title}\n├ <code>{chat.id}</code>\n\n"
        except:
            list_text += f"├ <code>{chat_id}</code>\n\n"

    list_text += f"━━━━━━━━━━━━━━━━━━❍\n<b>📊 Total Group Blacklist:</b> <code>{total_blacklist}</code>\n\n<b><blockquote>⚡ Power By Fanzy Userbot</b></blockquote>"
    return await mzg.edit(list_text)

@PY.UBOT("rallbl")
@PY.TOP_CMD
async def remove_all_blacklist(client, message):
    msg = await message.reply("<b>⏳ Processing...</b>")
    blacklists = await get_list_from_vars(client.me.id, "BL_ID")

    if not blacklists:
        return await msg.edit("<b>❌ Blacklist is empty!</b>")

    for chat_id in blacklists:
        await remove_from_vars(client.me.id, "BL_ID", chat_id)

    await msg.edit("<b>✅ All blacklist cleared!</b>")

# ============================================
# SEND MESSAGE
# ============================================
@PY.UBOT("send")
@PY.TOP_CMD
async def send_message_handler(client, message):
    if message.reply_to_message:
        chat_id = message.chat.id if len(message.command) < 2 else message.text.split()[1]
        try:
            if client.me.id != bot.me.id:
                if message.reply_to_message.reply_markup:
                    x = await client.get_inline_bot_results(
                        bot.me.username, f"get_send {id(message)}"
                    )
                    return await client.send_inline_bot_result(
                        chat_id, x.query_id, x.results[0].id
                    )
        except Exception as error:
            return await message.reply(str(error))
        else:
            try:
                return await message.reply_to_message.copy(chat_id)
            except Exception as t:
                return await message.reply(str(t))
    else:
        if len(message.command) < 3:
            return await message.reply("<b>❌ Usage:</b> <code>send [chat_id] [text]</code>")
        chat_id, chat_text = message.text.split(None, 2)[1:]
        try:
            if "_" in chat_id:
                msg_id, to_chat = chat_id.split("_")
                return await client.send_message(
                    to_chat, chat_text, reply_to_message_id=int(msg_id)
                )
            else:
                return await client.send_message(chat_id, chat_text)
        except Exception as t:
            return await message.reply(str(t))

@PY.INLINE("^get_send")
async def get_send_inline(client, inline_query):
    _id = int(inline_query.query.split()[1])
    m = next((obj for obj in get_objects() if id(obj) == _id), None)
    if m:
        await client.answer_inline_query(
            inline_query.id,
            cache_time=0,
            results=[
                InlineQueryResultArticle(
                    title="get send!",
                    reply_markup=m.reply_to_message.reply_markup,
                    input_message_content=InputTextMessageContent(
                        m.reply_to_message.text
                    ),
                )
            ],
        )

# ============================================
# AUTO BROADCAST
# ============================================
# ============================================
#       LOGIC AUTO BROADCAST & LIMIT
# ============================================

async def add_auto_text(client, text):
    """Fungsi helper buat nambahin teks ke database"""
    auto_text = await get_vars(client.me.id, "AUTO_TEXT") or []
    auto_text.append(text)
    await set_vars(client.me.id, "AUTO_TEXT", auto_text)

@PY.UBOT("auto")
@PY.TOP_CMD
async def auto_broadcast(client, message):
    msg = await message.reply("<b>⏳ Processing...</b>")
    type, value = extract_type_and_text(message)
    
    # 1. SAKLAR ON
    if type == "on":
        auto_text_vars_initial = await get_vars(client.me.id, "AUTO_TEXT") or []
        if not auto_text_vars_initial:
            return await msg.edit("<b>❌ Set teks dulu Puh!</b>")

        if client.me.id not in AG:
            AG.append(client.me.id)
            await msg.edit("<b>✅ Auto Broadcast AKTIF!</b>")
            
            count = 0
            while client.me.id in AG:
                current_texts = await get_vars(client.me.id, "AUTO_TEXT") or []
                current_wm = await get_vars(client.me.id, "AUTO_WATERMARK") or ""
                db_delay = await get_vars(client.me.id, "DELAY_GCAST")
                try: 
                    delay = int(db_delay) if db_delay else 1 
                except:
                     delay = 5    
                 
                chats = await get_data_id(client, "group")
                blacklist = await get_list_from_vars(client.me.id, "BL_ID")
                
                if not current_texts:
                    await msg.reply("<b>❌ Auto Gcast terhenti karena list teks kosong!</b>")
                    if client.me.id in AG: AG.remove(client.me.id)
                    break

                txt = random.choice(current_texts)
                if current_wm:
                    txt = f"{txt}\n\n<blockquote><i><b>{current_wm}</b></i></blockquote>"

                sent_count = 0
                for chat_id in chats:
                    if client.me.id not in AG: break                   
                    if chat_id in blacklist or chat_id in BLACKLIST_CHAT: continue                        
                    try:
                        await client.send_message(chat_id, txt)
                        sent_count += 1
                        await asyncio.sleep(1.5) 
                    except FloodWait as e:
                        await asyncio.sleep(e.value)
                        await client.send_message(chat_id, txt)
                        sent_count += 1
                    except Exception:
                        continue

                if client.me.id not in AG: break
                count += 1
                await msg.reply(
                    f"<blockquote><b>📡 AUTO GCAST DONE</b></blockquote>\n"
                    f"<b>🔄 Putaran:</b> <code>{count}</code>\n"
                    f"<b>📊 Terkirim:</b> <code>{sent_count} Grup</code>\n"
                    f"<b>⏱️ Delay:</b> <code>{delay} Menit</code>\n"
                    f"<b><blockquote>─ Fanzy Userbot Premium ─</blockquote></b>", 
                    quote=True
                )
                await asyncio.sleep(int(60 * delay))

        else:
            await msg.edit("<b>⚠️ Auto Gcast sudah berjalan.</b>")

    # 2. OFF
    elif type == "off":
        if client.me.id in AG:
            AG.remove(client.me.id)
            return await msg.edit("<b>✅ Auto Broadcast DIMATIKAN!</b>")
        return await msg.delete()

    # 3. TEXT (TAMBAH)
    elif type == "text":
        if not value: return await msg.edit("<b>❌ Masukkan teks!</b>")
        await add_auto_text(client, value)
        return await msg.edit("<b>✅ Teks berhasil disimpan!</b>")

    # 4. LIST (PERBAIKAN: Ambil data terbaru di sini)
    elif type == "list":
        current_list = await get_vars(client.me.id, "AUTO_TEXT") or []
        current_wm = await get_vars(client.me.id, "AUTO_WATERMARK") or ""
        if not current_list:
            return await msg.edit("<b>📋 Belum ada teks yang disimpan.</b>")
        
        txt = "<b>📋 AUTO TEXT LIST</b>\n\n"
        for i, t in enumerate(current_list, 1):
            txt += f"<b>{i}.</b> <code>{t[:50]}...</code>\n\n"
        
        txt += f"<b>💧 Watermark:</b> <code>{current_wm or 'Off'}</code>\n"
        txt += "━━━━━━━━━━━━━━━━━━❍"
        return await msg.edit(txt)

    # 5. REMOVE (PERBAIKAN: Ambil data terbaru sebelum remove)
    elif type == "remove":
        current_list = await get_vars(client.me.id, "AUTO_TEXT") or []
        if not value: return await msg.edit("<b>❌ Masukkan nomor/all!</b>")
        
        if value.lower() == "all":
            await set_vars(client.me.id, "AUTO_TEXT", [])
            return await msg.edit("<b>✅ Semua teks dihapus!</b>")
        
        try:
            idx = int(value) - 1
            if idx < 0 or idx >= len(current_list):
                return await msg.edit("<b>❌ Nomor tidak ditemukan!</b>")
                
            removed = current_list.pop(idx)
            await set_vars(client.me.id, "AUTO_TEXT", current_list)
            return await msg.edit(f"<b>✅ Terhapus:</b>\n<code>{removed[:50]}...</code>")
        except:
            return await msg.edit("<b>❌ Masukkan angka!</b>")
    
    # 6. WATERMARK KHUSUS AUTO (WM)
    # 6. WATERMARK
    elif type == "wm":
        if not value: return await msg.edit("<b>❌ Masukkan teks WM atau 'off'!</b>")
        val = "" if value.lower() == "off" else value
        await set_vars(client.me.id, "AUTO_WATERMARK", val)
        return await msg.edit(f"<b>✅ Watermark diset:</b> <code>{value}</code>")

    # 7. DELAY
    elif type == "delay":
        if not value or not value.isdigit():
            return await msg.edit("<b>❌ Masukkan angka menit!</b>")
        await set_vars(client.me.id, "DELAY_GCAST", int(value))
        return await msg.edit(f"<b>✅ Delay diset:</b> <code>{value} menit</code>")

    # 8. LIMIT
    elif type == "limit":
        # Logika limit kamu sudah oke karena menggunakan LT.append/remove
        if value == "on":
            if client.me.id not in LT:
                LT.append(client.me.id)
                await msg.edit("<b>✅ Auto Limit AKTIF!</b>")
                while client.me.id in LT:
                    try:
                        from fanzy.core.helpers.tools import limit_cmd
                        await limit_cmd(client, message)
                    except: pass
                    await asyncio.sleep(1200)
            else:
                await msg.edit("<b>⚠️ Auto Limit sudah berjalan.</b>")
        elif value == "off":
            if client.me.id in LT: LT.remove(client.me.id)
            return await msg.edit("<b>✅ Auto Limit MATI!</b>")
        else:
            return await msg.edit("<b>❌ Gunakan:</b> <code>.auto limit on/off</code>")

    # HELPER JIKA TYPO
    else:
        return await msg.edit(
            "<b>❌ Sub-Command salah!</b>\n"
            "Gunakan: <code>on, off, text, list, remove, wm, delay, limit</code>"
        )


# ============================================
# BOT BROADCAST
# ============================================
@PY.BOT("bcubot")
@PY.ADMIN
async def broadcast_bot(client, message):
    msg = await message.reply("<b>⏳ Processing...</b>", quote=True)
    done = 0
    if not message.reply_to_message:
        return await msg.edit("<b>❌ Please reply to a message!</b>")
    for x in ubot._ubot:
        try:
            await x.unblock_user(bot.me.username)
            await message.reply_to_message.copy(x.me.id)
            done += 1
        except Exception:
            pass
    
    result_msg = f"""
<blockquote><b>📢 SUCCESFULY BROADCASD</b></blockquote>
<b>✅ Sent:</b> <code>{done}</code> userbots
<blockquote><b>---  Fanzy Userbot Premium ---</b></blockquote>
"""
    return await msg.edit(result_msg)
    
    
    
    
    
