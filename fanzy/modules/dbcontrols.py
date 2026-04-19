import asyncio
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pytz import timezone
from fanzy import *
from fanzy.config import OWNER_ID
from fanzy.core.database.variabel import (
    get_list_from_vars, 
    add_to_vars, 
    remove_from_vars, 
    set_vars, 
    get_vars
)
from fanzy.core.database.expired import set_expired_date, rem_expired_date, get_expired_date
from fanzy.core.helpers.tools import extract_user, extract_user_and_reason

__MODULE__ = "dbcontrol"
__HELP__ = """
📋 <b>DAFTAR PERINTAH</b>

╭ <code>{0}prem</code> - Tambah premium
├ <code>{0}unprem</code> - Hapus premium
├ <code>{0}getprem</code> - Lihat premium
╰ <code>{0}addadmin</code> - Tambah admin

╭ <code>{0}unadmin</code> - Hapus admin
├ <code>{0}getadmin</code> - Lihat admin
├ <code>{0}seles</code> - Tambah seles
├ <code>{0}unseles</code> - Hapus seles
╰ <code>{0}getseles</code> - Lihat seles

╭ <code>{0}addowner</code> - Tambah owner
├ <code>{0}unowner</code> - Hapus owner
╰ <code>{0}getowner</code> - Lihat owner

╭ <code>{0}time</code> - Tambah masa aktif
╰ <code>{0}cek</code> - Cek masa aktif
"""
# ============================================
# VARIABEL UNTUK MONGODB
# ============================================
VARS_OWNER_USERS = "OWNER_USERS"
VARS_OWNER_ADDED_BY = "OWNER_ADDED_BY"
VARS_PREM_ADDED_BY = "PREM_ADDED_BY"
VARS_ADMIN_ADDED_BY = "ADMIN_ADDED_BY"
VARS_SELER_ADDED_BY = "SELER_ADDED_BY"

LOG_GROUP_ID = -1003755731850
# ============================================
# FUNGSI PEMBANTU
# ============================================

def fmt_user(user):
    if user.username:
        return f"@{user.username}"
    name = f"{user.first_name} {user.last_name or ''}".strip()
    return name[:12] + "..." if len(name) > 15 else name

def fmt_id(user):
    return f"<a href=tg://user?id={user.id}>{fmt_user(user)}</a>"

async def get_owner_users():
    return await get_list_from_vars(bot.me.id, VARS_OWNER_USERS)
    
async def send_security_log(client, executor, command, target_id, status, details):
    """
    Mengirimkan laporan keamanan ke grup log khusus.
    """
    now = datetime.now(timezone("Asia/Jakarta"))
    waktu = now.strftime("%d/%m/%Y %H:%M:%S")
    
    icon = "✅" if status == "SUCCESS" else "⚠️"
    
    text = (
        f"<blockquote><b>{icon} SECURITY AUDIT LOGS</b></blockquote>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b>📅 Waktu :</b> <code>{waktu}</code>\n"
        f"<b>👤 Eksekutor :</b> {fmt_id(executor)}\n"
        f"<b>🆔 ID Pelaku : {executor.id}\n"
        f"<b>⌨️ Perintah :</b> <code>.{command}</code>\n"
        f"<b>🎯 Target ID :</b> <code>{target_id or 'N/A'}</code>\n"
        f"<b>📊 Status :</b> <code>{status}</code>\n"
        f"<b>📝 Detail :</b> <i>{details}</i>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<b><blockquote>✨ Fanzy Userbot Security System</blockquote></b>"
    )
    
    try:
        await bot.send_message(LOG_GROUP_ID, text)
    except Exception as e:
        print(f"Gagal mengirim log keamanan: {e}")

async def add_owner_user(user_id, added_by, masa_aktif_bulan=12):
    owners = await get_owner_users()
    if user_id not in owners and user_id != OWNER_ID:
        now = datetime.now(timezone("Asia/Jakarta"))
        expired = now + relativedelta(months=masa_aktif_bulan)
        
        # Add to Premium
        prem_data = await get_vars(bot.me.id, "PREM_USERS") or ""
        prem_list = [int(x) for x in str(prem_data).split() if x]
        if user_id not in prem_list:
            prem_list.append(user_id)
            await set_vars(bot.me.id, "PREM_USERS", " ".join(map(str, prem_list)))
            await set_expired_date(user_id, expired)
            await add_prem_record(user_id, added_by, masa_aktif_bulan)
        
        # Add to Owner
        await add_to_vars(bot.me.id, VARS_OWNER_USERS, user_id)
        added_by_list = await get_vars(bot.me.id, VARS_OWNER_ADDED_BY) or []
        if isinstance(added_by_list, str):
            added_by_list = json.loads(added_by_list) if added_by_list else []
        added_by_list.append({"owner_id": user_id, "added_by": added_by})
        await set_vars(bot.me.id, VARS_OWNER_ADDED_BY, json.dumps(added_by_list))
        
        # Add to Seller
        seles_data = await get_vars(bot.me.id, "SELER_USERS") or ""
        seles_list = [int(x) for x in str(seles_data).split() if x]
        if user_id not in seles_list:
            seles_list.append(user_id)
            await set_vars(bot.me.id, "SELER_USERS", " ".join(map(str, seles_list)))
            await add_seler_record(user_id, added_by)
            
        # Add to Admin
        admin_data = await get_vars(bot.me.id, "ADMIN_USERS") or ""
        admin_list = [int(x) for x in str(admin_data).split() if x]
        if user_id not in admin_list:
            admin_list.append(user_id)
            await set_vars(bot.me.id, "ADMIN_USERS", " ".join(map(str, admin_list)))
            await add_admin_record(user_id, added_by)
        return True
    return False

async def remove_owner_user(user_id):
    owners = await get_owner_users()
    if user_id in owners:
        await remove_from_vars(bot.me.id, VARS_OWNER_USERS, user_id)
        added_by_list = await get_vars(bot.me.id, VARS_OWNER_ADDED_BY) or []
        if isinstance(added_by_list, str):
            added_by_list = json.loads(added_by_list) if added_by_list else []
        new_list = [item for item in added_by_list if item["owner_id"] != user_id]
        await set_vars(bot.me.id, VARS_OWNER_ADDED_BY, json.dumps(new_list))        
        prem_users = await get_list_from_vars(bot.me.id, "PREM_USERS")
        if user_id in prem_users:
            await remove_from_vars(bot.me.id, "PREM_USERS", user_id)
            await rem_expired_date(user_id)
            await remove_prem_record(user_id)        
        seles_users = await get_list_from_vars(bot.me.id, "SELER_USERS")
        if user_id in seles_users:
            await remove_from_vars(bot.me.id, "SELER_USERS", user_id)
            await remove_seler_record(user_id)        
        admin_users = await get_list_from_vars(bot.me.id, "ADMIN_USERS")
        if user_id in admin_users:
            await remove_from_vars(bot.me.id, "ADMIN_USERS", user_id)
            await remove_admin_record(user_id)
        return True
    return False

async def check_access(user_id, command, client=None, message=None):    
    if user_id == OWNER_ID:
        return True, "Owner Asli"        
    owner_users = await get_owner_users()
    if user_id in owner_users:
        return True, "Owner Tambahan"        
    admin_users = await get_list_from_vars(bot.me.id, "ADMIN_USERS") or []
    if user_id in admin_users:
        allowed = ["prem", "seles", "unprem", "unseles", "getprem", "getseles", "getadmin"]
        if command in allowed:
            return True, "Admin"        
        if client and message:
            await send_security_log(client, message.from_user, command, "N/A", "REJECTED", "User mencoba mengakses perintah yang diluar wewenang Admin")
        return False, "AKSES ANDA DITOLAK ❗\nanda bukan owner userbot !"        
    seles_users = await get_list_from_vars(bot.me.id, "SELER_USERS") or []
    if user_id in seles_users:
        allowed = ["prem", "unprem", "getprem", "getseles"]
        if command in allowed:
            return True, "Seles"            
        if client and message:
            await send_security_log(client, message.from_user, command, "N/A", "REJECTED", "User mencoba mengakses perintah yang diluar wewenang Seller")
        return False, "AKSES ANDA DITOLAK ❗\nanda bukan admin userbot !"        
    prem_users = await get_list_from_vars(bot.me.id, "PREM_USERS") or []
    if user_id in prem_users:
        allowed = []
        if command in allowed:
            return True, "Premium"
        if client and message:            
            await send_security_log(client, message.from_user, command, "N/A", "REJECTED", "User Premium Mencoba Untuk Mengakses Fitur Staff! 😂😂")            
        return False, "upgrade role dulu ke owner! "        
    if client and message:
        await send_security_log(client, message.from_user, command, "N/A", "UNAUTHORIZED", "Akses Anda Ditolak!! upgrade Role Dulu Lawak 😂😂")        
    return False, "Anda Tidak memilik Akses !"


async def can_remove_user(user_id, target_user_id, added_by_var_name, role_name):
    if user_id == OWNER_ID:
        return True, "Owner Asli - akses penuh"    
    added_by_list = await get_vars(bot.me.id, added_by_var_name) or []
    if isinstance(added_by_list, str):
        added_by_list = json.loads(added_by_list) if added_by_list else []
    
    # PERBAIKAN: Menyamakan pengambilan key ID antara "user_id" (Admin/Seles/Prem) dan "owner_id" (Owner Tambahan)
    target_data = next((item for item in added_by_list if int(item.get("user_id") or item.get("owner_id") or 0) == int(target_user_id)), None)
    
    if target_data:
        added_by = target_data.get("added_by")        
        if added_by == user_id:
            return True, f"{role_name} - dihapus oleh penambahnya ({user_id})"
        else:
            return False, f"User ini Di Add Oleh (ID: {added_by}) Tidak bisa Di Hapus Oleh Mu. <b><i>~Fanzy Userbot</i></b>"
    else:
        # Logika owner asli tetap dipertahankan sesuai kode awal
        if user_id == OWNER_ID:
            return True, "Owner Asli - data lama"
        else:
            return False, f"{role_name} tidak memiliki record penambah, hanya Owner Asli yang bisa menghapus!"


async def add_prem_record(user_id, added_by, bulan):
    records = await get_vars(bot.me.id, VARS_PREM_ADDED_BY) or []
    if isinstance(records, str):
        records = json.loads(records) if records else []
    records.append({"user_id": user_id, "added_by": added_by, "bulan": bulan})
    await set_vars(bot.me.id, VARS_PREM_ADDED_BY, json.dumps(records))

async def remove_prem_record(user_id):
    records = await get_vars(bot.me.id, VARS_PREM_ADDED_BY) or []
    if isinstance(records, str):
        records = json.loads(records) if records else []
    new_records = [item for item in records if item["user_id"] != user_id]
    await set_vars(bot.me.id, VARS_PREM_ADDED_BY, json.dumps(new_records))

async def add_admin_record(user_id, added_by):
    records = await get_vars(bot.me.id, VARS_ADMIN_ADDED_BY) or []
    if isinstance(records, str):
        records = json.loads(records) if records else []
    records.append({"user_id": user_id, "added_by": added_by})
    await set_vars(bot.me.id, VARS_ADMIN_ADDED_BY, json.dumps(records))

async def remove_admin_record(user_id):
    records = await get_vars(bot.me.id, VARS_ADMIN_ADDED_BY) or []
    if isinstance(records, str):
        records = json.loads(records) if records else []
    new_records = [item for item in records if item["user_id"] != user_id]
    await set_vars(bot.me.id, VARS_ADMIN_ADDED_BY, json.dumps(new_records))

async def add_seler_record(user_id, added_by):
    records = await get_vars(bot.me.id, VARS_SELER_ADDED_BY) or []
    if isinstance(records, str):
        records = json.loads(records) if records else []
    records.append({"user_id": user_id, "added_by": added_by})
    await set_vars(bot.me.id, VARS_SELER_ADDED_BY, json.dumps(records))

async def remove_seler_record(user_id):
    records = await get_vars(bot.me.id, VARS_SELER_ADDED_BY) or []
    if isinstance(records, str):
        records = json.loads(records) if records else []
    new_records = [item for item in records if item["user_id"] != user_id]
    await set_vars(bot.me.id, VARS_SELER_ADDED_BY, json.dumps(new_records))

# ============================================
# PREMIUM MANAGEMENT
# ============================================
@PY.BOT("prem")
@PY.SELLER
async def prem_cmd(client, message):
    user = message.from_user    
    can_access, role = await check_access(user.id, "prem", client, message)
    if not can_access:
        return await message.reply(f"⚠️ {role}")    
    args = message.command
    if len(args) >= 2:
        user_id = args[1]
        get_bulan = args[2] if len(args) > 2 else "1"
    else:
        user_id, get_bulan = await extract_user_and_reason(message)
    msg = await message.reply("<b><i>🔁 Prosessing....</b></i>")        
    if not user_id:
        return await msg.edit(f"❌ <code>{message.text} user_id/username bulan</code>")        
    try:
        if isinstance(user_id, str):
            user_id = user_id.split()[0]
        target_user = await client.get_users(user_id)
    except Exception as error:
        return await msg.edit(f"❌ Gagal mendapatkan user: {str(error)[:50]}")
    import random
    clean_val = str(get_bulan).replace("-", "").strip()
    now = datetime.now(timezone("Asia/Jakarta"))
    tgl_random = random.randint(1, 28)     
    if clean_val == "0":
        expired = datetime(2027, 2, 10, tzinfo=timezone("Asia/Jakarta"))
    else:
        try:
            val_int = int(clean_val)
            target_date = now + relativedelta(months=val_int)
            expired = datetime(target_date.year, target_date.month, tgl_random, tzinfo=timezone("Asia/Jakarta"))
        except:
            target_date = now + relativedelta(months=1)
            expired = datetime(target_date.year, target_date.month, tgl_random, tzinfo=timezone("Asia/Jakarta"))
    prem_users = await get_list_from_vars(bot.me.id, "PREM_USERS")
    if target_user.id in prem_users:
        return await msg.edit(f"<b>✅ USER SUDAH PREMIUM!</b>")        
    try:
        await set_expired_date(target_user.id, expired)
        await add_to_vars(bot.me.id, "PREM_USERS", target_user.id)
        await add_prem_record(target_user.id, user.id, clean_val)
        await send_security_log(client, user, "prem", target_user.id, "SUCCESS", f"Succes Add Premium")        
        await msg.edit(f"✅ <b>Succesfully add prem.</b> User\ndengan Id {target_user.id} <b>telah di</b>\n<b>tambahkan ke dalam d a f t a r</b>\n<b>premium userbot</b>  dngn  <b>durasi\n{clean_val} mont.</b></b> Silakan utk membuat\n<b>u s e r b o t</b> anda di @{bot.me.username}!")        
        await bot.send_message(OWNER_ID, f"• ɪᴅ-ꜱᴇʟʟᴇʀ: `{message.from_user.id}`\n\n• ɪᴅ-ᴄᴜꜱᴛᴏᴍᴇʀ: `{target_user.id}`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⁉️ ꜱᴇʟʟᴇʀ", callback_data=f"profil {message.from_user.id}"), InlineKeyboardButton("ᴄᴜꜱᴛᴏᴍᴇʀ ⁉️", callback_data=f"profil {target_user.id}")]]))
    except Exception as error:
        await send_security_log(client, user, "prem", user_id, "ERROR", str(error))
        return await msg.edit(f"❌ {error}")

@PY.BOT("unprem")
@PY.SELLER
async def unprem_cmd(client, message):
    user = message.from_user    
    can_access, role = await check_access(user.id, "unprem", client, message)
    if not can_access:
        return await message.reply(f"⚠️ {role}")    
    msg = await message.reply("<b><i>🔁 Processing....</b></i>")
    user_id = await extract_user(message)    
    if not user_id:
        return await msg.edit(f"❌ <code>{message.text} user_id/username</code>")    
    prem_raw = await get_vars(bot.me.id, "PREM_USERS") or ""
    prem_list = [int(x) for x in prem_raw.replace("\n", " ").split() if x]    
    if user_id not in prem_list:
        return await msg.edit(f"❌ User ID <code>{user_id}</code> tidak ada dalam daftar premium!")  
    can_remove, reason = await can_remove_user(
        user_id=user.id, 
        target_user_id=user_id, 
        added_by_var_name=VARS_PREM_ADDED_BY, 
        role_name="Premium"
    )   
    if not can_remove:
        error_msg = f"<b><blockquote>❌ AKSES ANDA DITOLAK!</blockquote></b>\n<b>━━━━━━━━━━━━━━━━━━━</b>\n📋 <b>Alasan :</b> {reason}\n\n\n<b>👮 <b>Fitur Kemanan Active</b>\n<blockquote><b>✨ Power By Fanzy Userbot</b></blockquote>"
        return await msg.edit(error_msg)
    try:
        prem_list.remove(user_id)
        await set_vars(bot.me.id, "PREM_USERS", " ".join(map(str, prem_list)))
        await rem_expired_date(user_id)
        await remove_prem_record(user_id)
        await send_security_log(client, user, "unprem", user_id, "SUCCESS", "Berhasil unpremium")        
        now = datetime.now(timezone("Asia/Jakarta"))
        waktu = now.strftime("%H:%M")
        tanggal = now.strftime("%d/%m/%Y")        
        try:
            target_user = await client.get_users(user_id)
            nama = fmt_id(target_user)
        except:
            nama = f"<code>{user_id}</code>"        
        return await msg.edit(f"✅ <b>Succesfully  unprem.</b>  User\ndengan Id {user_id} <b>telah di</b>\n<b>hapus dari dalam daftar prem!</b>")
    except Exception as error:
        await send_security_log(client, user, "unprem", user_id, "ERROR", str(error))    
        return await msg.edit(f"❌ Error: {error}")

@PY.BOT("getprem")
@PY.SELLER
async def getprem_bot(client, message):
    user = message.from_user
    can_access, role = await check_access(user.id, "getprem", client, message)
    if not can_access: 
        return await message.reply(f"⚠️ {role}")    
    await send_security_log(client, user, "getprem", "N/A", "SUCCESS", "Melihat daftar Prem")        
    msg = await message.reply("<b><i>🔁 Fetching Data...</i></b>")    
    raw = await get_vars(bot.me.id, "PREM_USERS") or ""
    users = [int(x) for x in str(raw).split() if x]
    
    if not users:
        return await msg.edit("<blockquote><b>📋 LIST PREMIUM KOSONG!</b></blockquote>")    
    header = "<b>📋 𝗟𝗜𝗦𝗧 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗨𝗦𝗘𝗥𝗦</b>"    
    content = ""
    for i, uid in enumerate(users, 1):
        try:
            u = await client.get_users(uid)
            content += f"{i:02d}. {u.mention} | <code>{uid}</code>\n"
        except:
            content += f"{i:02d}. 👤 <code>{uid}</code> | (not found)\n"
    footer = f"✨ <i><b>Power By Fanzy Userbot</b></i>"    
    final_text = (
        f"<blockquote>{header}</blockquote>\n"
        f"<blockquote>{content.strip()}</blockquote>\n"
        f"<blockquote>{footer}</blockquote>"
    )    
    await msg.edit(final_text)


# ============================================
# SELES MANAGEMENT
# ============================================
@PY.BOT("seles")
@PY.ADMIN
async def seles_cmd(client, message):
    user = message.from_user    
    can_access, role = await check_access(user.id, "seles", client, message)
    if not can_access:
        return await message.reply(f"⚠️ {role}")    
    msg = await message.reply("<b><i>🔁 Prosessing....</b></i>")
    user_id = await extract_user(message)    
    if not user_id:
        return await msg.edit(f"❌ <code>{message.text} user_id/username</code>")    
    try:
        target_user = await client.get_users(user_id)
    except Exception as error:
        error_msg = str(error)
        if "USER_ID_INVALID" in error_msg:
            return await msg.edit("❌ ID pengguna tidak valid!")
        elif "USERNAME_NOT_OCCUPIED" in error_msg:
            return await msg.edit("❌ Username tidak ditemukan!")
        elif "PEER_ID_INVALID" in error_msg:
            return await msg.edit("❌ User belum pernah chat dengan bot!")
        elif "USER_IS_BLOCKED" in error_msg:
            return await msg.edit("❌ Anda memblokir bot, buka blokir dulu!")
        else:
            return await msg.edit(f"❌ Terjadi kesalahan: {error_msg[:100]}")    
    seles_users = await get_list_from_vars(bot.me.id, "SELER_USERS")    
    if target_user.id in seles_users:
        return await msg.edit(f"<b>✅ USERS SUDAH SELLER!</b>")    
    try:
        await add_to_vars(bot.me.id, "SELER_USERS", target_user.id)
        await add_seler_record(target_user.id, user.id)
        await send_security_log(client, user, "seles", target_user.id, "SUCCESS", "Berhasil add seles")        
        await msg.edit(f"✅ <b>Succesfully add seller.</b> User\ndengan Id {target_user.id} <b>telah di</b>\n<b>tambahkan ke dalam d a f t a r</b>\n<b>seller.</b> Silakan untuk membuat\n<b>u s e r b o t</b> anda di @{bot.me.username}!")
    except Exception as error:
        await send_security_log(client, user, "seles", user_id, "ERROR", str(error))    
        return await msg.edit(f"❌ {error}")


@PY.BOT("unseles")
@PY.ADMIN
async def unseles_cmd(client, message):
    user = message.from_user    
    can_access, role = await check_access(user.id, "unseles", client, message)
    if not can_access:
        return await message.reply(f"⚠️ {role}")    
    msg = await message.reply("<b><i>🔁 Processing....</b></i>")
    user_id = await extract_user(message)    
    if not user_id:
        return await msg.edit(f"❌ <code>{message.text} user_id/username</code>")    
    seles_raw = await get_vars(bot.me.id, "SELER_USERS") or ""
    seles_list = [int(x) for x in seles_raw.replace("\n", " ").split() if x]    
    if user_id not in seles_list:
        return await msg.edit(f"❌ User ID <code>{user_id}</code> tidak ada dalam daftar seles!")    
    can_remove, reason = await can_remove_user(
        user_id=user.id, 
        target_user_id=user_id, 
        added_by_var_name=VARS_SELER_ADDED_BY, 
        role_name="Seles"
    )
    if not can_remove:
        error_msg = f"<b><blockquote>❌ AKSES ANDA DITOLAK!</blockquote></b>\n<b>━━━━━━━━━━━━━━━━━━━</b>\n📋 <b>Alasan :</b> {reason}\n\n\n<b>👮 <b>Fitur Kemanan Active</b>\n<blockquote><b>✨ Power By Fanzy Userbot</b></blockquote>"
        return await msg.edit(error_msg)       
    try:
        seles_list.remove(user_id)
        await set_vars(bot.me.id, "SELER_USERS", " ".join(map(str, seles_list)))
        await remove_seler_record(user_id) 
        await send_security_log(client, user, "unseles", user_id, "SUCCESS", "Berhasil unseles")               
        now = datetime.now(timezone("Asia/Jakarta"))
        waktu = now.strftime("%H:%M")
        tanggal = now.strftime("%d/%m/%Y")        
        try:
            target_user = await client.get_users(user_id)
            nama = fmt_id(target_user)
        except:
            nama = f"<code>{user_id}</code>"        
        return await msg.edit(f"✅ <b>Succesfully  unseles.</b>  User\ndengan Id {user_id} <b>telah di</b>\n<b>hapus dari dalam daftar seles!</b>")
    except Exception as error:
        await send_security_log(client, user, "unseles", user_id, "ERROR", str(error))    
        return await msg.edit(f"❌ Error: {error}")

@PY.BOT("getseles")
@PY.ADMIN
async def getseles_bot(client, message):
    user = message.from_user
    can_access, role = await check_access(user.id, "getseles", client, message)
    if not can_access: 
        return await message.reply(f"⚠️ {role}")    
    await send_security_log(client, user, "getseles", "N/A", "SUCCESS", "Melihat daftar seles")        
    msg = await message.reply("<b><i>🔁 Fetching Data...</i></b>")
    raw = await get_vars(bot.me.id, "SELER_USERS") or ""
    users = [int(x) for x in str(raw).split() if x]    
    if not users:
        return await msg.edit("<blockquote><b>⭐ LIST SELLER KOSONG!</b></blockquote>")    
    header = "<b>📋 𝗟𝗜𝗦𝗧 𝗦𝗘𝗟𝗟𝗘𝗥 𝗨𝗦𝗘𝗥𝗕𝗢𝗧</b>"
    content = ""
    for i, uid in enumerate(users, 1):
        try:
            u = await client.get_users(uid)
            content += f"{i:02d}. {u.mention} | <code>{uid}</code>\n"
        except:
            content += f"{i:02d}. 👤 <code>{uid}</code> | (not found)\n"    
    footer = f"✨ <i><b>Power By Fanzy Userbot</b></i>"    
    await msg.edit(
        f"<blockquote>{header}</blockquote>\n"
        f"<blockquote>{content.strip()}</blockquote>\n"
        f"<blockquote>{footer}</blockquote>"
    )


# ============================================
# ADMIN MANAGEMENT
# ============================================
@PY.BOT("addadmin")
@PY.OWNER
async def addadmin_cmd(client, message):
    user = message.from_user        
    can_access, role = await check_access(user.id, "addadmin", client, message)
    if not can_access:
        return await message.reply("❌ KHUSUS OWNER !")
    msg = await message.reply("<b><i>🔁 Prosessing....</b></i>")
    user_id = await extract_user(message)    
    if not user_id:
        return await msg.edit(f"❌ <code>{message.text} user_id/username</code>")        
    try:
        target_user = await client.get_users(user_id)
    except Exception as error:
        error_msg = str(error)
        if "USER_ID_INVALID" in error_msg:
            return await msg.edit("❌ ID pengguna tidak valid!")
        elif "USERNAME_NOT_OCCUPIED" in error_msg:
            return await msg.edit("❌ Username tidak ditemukan!")
        elif "PEER_ID_INVALID" in error_msg:
            return await msg.edit("❌ User belum pernah chat dengan bot!")
        elif "USER_IS_BLOCKED" in error_msg:
            return await msg.edit("❌ Anda memblokir bot, buka blokir dulu!")
        else:
            return await msg.edit(f"❌ Terjadi kesalahan: {error_msg[:100]}")        
    admin_users = await get_list_from_vars(bot.me.id, "ADMIN_USERS") or []
    if target_user.id in admin_users:
        return await msg.edit(f"<b>✅ USER SUDAH ADMIN!</b>")        
    try:
        await add_to_vars(bot.me.id, "ADMIN_USERS", target_user.id)
        await add_admin_record(target_user.id, user.id)        
        await send_security_log(client, user, "addadmin", target_user.id, "SUCCESS", "Berhasil Add admin")
        await msg.edit(f"✅ <b>Succesfully add admin.</b> User\ndengan Id {target_user.id} <b>telah di</b>\n<b>tambahkan ke dalam  d a f t a r</b>\n<b>admin.</b> Silakan untuk membuat\n<b>u s e r b o t</b> anda di @{bot.me.username}!")
    except Exception as error:
        await send_security_log(client, user, "addadmin", user_id, "ERROR", str(error))
        return await msg.edit(f"❌ {error}")


@PY.BOT("unadmin")
@PY.OWNER
async def unadmin_cmd(client, message):
    user = message.from_user    
    can_access, role = await check_access(user.id, "unadmin", client, message)
    if not can_access:
        return await message.reply(f"⚠️ {role}")    
    msg = await message.reply("<b><i>🔁 Processing....</b></i>")
    user_id = await extract_user(message)    
    if not user_id:
        return await msg.edit(f"❌ <code>{message.text} user_id/username</code>")    
    admin_raw = await get_vars(bot.me.id, "ADMIN_USERS") or ""
    admin_list = [int(x) for x in admin_raw.replace("\n", " ").split() if x]    
    if user_id not in admin_list:
        return await msg.edit(f"❌ User ID <code>{user_id}</code> tidak ada dalam daftar admin!")
    can_remove, reason = await can_remove_user(
        user_id=user.id, 
        target_user_id=user_id, 
        added_by_var_name=VARS_ADMIN_ADDED_BY, 
        role_name="Admin"
    )
    if not can_remove:
        error_msg = f"<b><blockquote>❌ AKSES ANDA DITOLAK!</blockquote></b>\n<b>━━━━━━━━━━━━━━━━━━━</b>\n📋 <b>Alasan :</b> {reason}\n\n\n<b>👮 <b>Fitur Kemanan Active</b>\n<blockquote><b>✨ Power By Fanzy Userbot</b></blockquote>"
        return await msg.edit(error_msg)    
    try:
        admin_list.remove(user_id)
        await set_vars(bot.me.id, "ADMIN_USERS", " ".join(map(str, admin_list)))
        await remove_admin_record(user_id) 
        await send_security_log(client, user, "unadmin", user_id, "SUCCESS", "berhasil unadmin user")               
        now = datetime.now(timezone("Asia/Jakarta"))
        waktu = now.strftime("%H:%M")
        tanggal = now.strftime("%d/%m/%Y")        
        try:
            target_user = await client.get_users(user_id)
            nama = fmt_id(target_user)
        except:
            nama = f"<code>{user_id}</code>"        
        return await msg.edit(f"✅ <b>Succesfully  unadmin.</b> User\ndengan Id {user_id} <b>telah di</b>\n<b>hapus dari dalam daftar admin!</b>")
    except Exception as error:
        return await msg.edit(f"❌ Error: {error}")
        
@PY.BOT("getadmin")
@PY.OWNER
async def getadmin_bot(client, message):
    user = message.from_user
    can_access, role = await check_access(user.id, "getadmin", client, message)
    if not can_access: 
        return await message.reply(f"⚠️ {role}")
    await send_security_log(client, user, "getadmin", "N/A", "SUCCESS", "Melihat daftar admin")    
    msg = await message.reply("<b><i>🔁 Fetching Data...</i></b>")
    raw = await get_vars(bot.me.id, "ADMIN_USERS") or ""
    users = [int(x) for x in str(raw).split() if x]    
    if not users:
        return await msg.edit("<blockquote><b>🛡️ LIST ADMIN KOSONG!</b></blockquote>")    
    header = "<b>📋 𝗟𝗜𝗦𝗧 𝗔𝗗𝗠𝗜𝗡 𝗨𝗦𝗘𝗥𝗕𝗢𝗧</b>"
    content = ""
    for i, uid in enumerate(users, 1):
        try:
            u = await client.get_users(uid)
            content += f"{i:02d}. {u.mention} | <code>{uid}</code>\n"
        except:
            content += f"{i:02d}. 👤 <code>{uid}</code> | (not found)\n"    
    footer = f"✨ <i><b>Power By Fanzy Userbot</b></i>"    
    await msg.edit(
        f"<blockquote>{header}</blockquote>\n"
        f"<blockquote>{content.strip()}</blockquote>\n"
        f"<blockquote>{footer}</blockquote>"
    )


# ============================================
# OWNER MANAGEMENT
# ============================================
@PY.BOT("addowner")
@PY.OWNER
async def addowner_cmd(client, message):
    user = message.from_user    
    can_access, role = await check_access(user.id, "addowner", client, message)
    if not can_access:
        return await message.reply("⚠️ <b>Khusus Owner Userbot !</b> ")
    msg = await message.reply("<b><i>🔁 Prosessing....</b></i>")
    user_id = await extract_user(message)   
    if not user_id:
        return await msg.edit(f"❌ <code>{message.text} user_id/username</code>")        
    try:
        target_user = await client.get_users(user_id)
    except Exception as error:
        error_msg = str(error)
        if "USER_ID_INVALID" in error_msg:
            return await msg.edit("❌ ID pengguna tidak valid!")
        elif "USERNAME_NOT_OCCUPIED" in error_msg:
            return await msg.edit("❌ Username tidak ditemukan!")
        elif "PEER_ID_INVALID" in error_msg:
            return await msg.edit("❌ User belum pernah chat dengan bot!")
        elif "USER_IS_BLOCKED" in error_msg:
            return await msg.edit("❌ Anda memblokir bot, buka blokir dulu!")
        else:
            return await msg.edit(f"❌ Terjadi kesalahan: {error_msg[:100]}")        
    owner_users = await get_owner_users()    
    if target_user.id == OWNER_ID:
        return await msg.edit("❌ Tidak bisa add Owner Asli")    
    if target_user.id in owner_users:
        return await msg.edit(f"<b>✅ USERS SUDAH OWNER</b>")        
    try:
        await add_owner_user(target_user.id, user.id, masa_aktif_bulan=12)
        await asyncio.sleep(2)        
        now = datetime.now(timezone("Asia/Jakarta"))
        expired = now + relativedelta(months=12)
        expired_str = expired.strftime("%d-%m-%Y")            
        await send_security_log(client, user, "addowner", target_user.id, "SUCCESS", "Succes Add Owner")
        await msg.edit(f"✅ <b>Succesfully add owner.</b> User\ndengan Id {target_user.id} <b>telah di</b>\n<b>tambahkan ke dalam  d a f t a r</b>\n<b>Owner.</b> Silakan untuk membuat\n<b>u s e r b o t</b> anda di @{bot.me.username}!")    
        await client.send_message(target_user.id, f"✅ Selamat andaa sekarang adalahh <b>OWNER</b> di userbot <b>FANZY USERBOT</b>\n\n📋 <b>Akses:</b> premium, seles, addadmin\n📅 <b>Expired data:</b> {expired_str}")
    except Exception as error:
        await send_security_log(client, user, "addowner", user_id, "ERROR", str(error))
        return await msg.edit(f"❌ Terjadi kesalahan: {error}")

@PY.BOT("unowner")
@PY.OWNER
async def unowner_cmd(client, message):
    user = message.from_user        
    can_access, role = await check_access(user.id, "unowner", client, message)
    if not can_access:
        return await message.reply("⚠️ **KHUSUS DEVOLOPMENT**")    
    msg = await message.reply("<b><i>🔁 Processing....</b></i>")
    user_id = await extract_user(message)    
    if not user_id:
        return await msg.edit(f"❌ <code>{message.text} user_id/username</code>")    
    if user_id == OWNER_ID:
        return await msg.edit("❌ Tidak bisa menghapus Owner Asli!")    
    owner_raw = await get_vars(bot.me.id, VARS_OWNER_USERS) or ""
    owner_list = [int(x) for x in owner_raw.replace("\n", " ").split() if x]        
    if user_id not in owner_list:
        return await msg.edit(f"❌ User ID <code>{user_id}</code> bukan Owner Tambahan!")    
    try:
        await remove_owner_user(user_id)        
        now = datetime.now(timezone("Asia/Jakarta"))
        waktu = now.strftime("%H:%M")
        tanggal = now.strftime("%d/%m/%Y")                
        try:
            target_user = await client.get_users(user_id)
            nama = fmt_id(target_user)
        except:
            nama = f"<code>{user_id}</code>"        
        await send_security_log(client, user, "unowner", user_id, "SUCCESS", "Berhasil unowner user")
        await msg.edit(f"✅ <b>Succesfully  unowner.</b>  User\ndengan Id {user_id} <b>telah di</b>\n<b>hapus dari dalam daftar owner!</b>")        
        try:
            await client.send_message(user_id, f"❌ Status Owner Anda di @{bot.me.username} telah dicabut oleh Owner Asli!")
        except:
            pass            
    except Exception as error:
        await send_security_log(client, user, "unowner", user_id, "ERROR", str(error))
        return await msg.edit(f"❌ Error: {error}")

@PY.BOT("getowner")
@PY.OWNER
async def getowner_bot(client, message):
    user = message.from_user
    can_access, role = await check_access(user.id, "getowner", client, message)
    if not can_access: 
        return await message.reply(f"⚠️ {role}")    
    await send_security_log(client, user, "getowner", "N/A", "SUCCESS", "Melihat daftar owner")        
    msg = await message.reply("<b><i>🔁 Fetching Data...</i></b>")    
    header = "<b>📋 𝗟𝗜𝗦𝗧 𝗢𝗪𝗡𝗘𝗥 𝗨𝗦𝗘𝗥𝗕𝗢𝗧</b>"
    content = ""    
    try:
        owner_asli = await client.get_users(OWNER_ID)
        content += f"01. 👑 {owner_asli.mention} | <code>{OWNER_ID}</code>\n"
    except:
        content += f"01. 👑 Owner Asli | <code>{OWNER_ID}</code>\n"    
    raw = await get_vars(bot.me.id, VARS_OWNER_USERS) or ""
    owner_tambahan = [int(x) for x in str(raw).split() if x]    
    for i, uid in enumerate(owner_tambahan, 2): # Mulai dari angka 2
        try:
            u = await client.get_users(uid)
            content += f"{i:02d}. 👤 {u.mention} | <code>{uid}</code>\n"
        except:
            content += f"{i:02d}. 👤 <code>{uid}</code> | (not found)\n"    
    footer = f"✨ <b><i>Power By Fanzy Userbot</b></i>"    
    await msg.edit(
        f"<blockquote>{header}</blockquote>\n"
        f"<blockquote>{content.strip()}</blockquote>\n"
        f"<blockquote>{footer}</blockquote>"
    )

# ============================================
# TIME & CEK MANAGEMENT
# ============================================

@PY.BOT("time")
@PY.OWNER
async def time_cmd(client, message):
    user = message.from_user
    can_access, role = await check_access(user.id, "time", client, message)
    if not can_access: return await message.reply(role)    
    args = message.command
    if len(args) != 3: return await message.reply("<b>❌ FORMAT:</b> <code>.time [id] [hari]</code>")    
    msg = await message.reply("<b><i>🔁 Updating...</i></b>")
    user_id, days = int(args[1]), int(args[2])
    expire = datetime.now(timezone("Asia/Jakarta")) + timedelta(days=days)
    await set_expired_date(user_id, expire)
    await send_security_log(client, user, "time", user_id, "SUCCESS", f"Succes Menambah Masa Aktif User")    
    await msg.edit(f"<b>✅ User Dengan ID</b> {user_id} <b>Masa Active Ditambah {days} hari</b>")



@PY.BOT("cek")
async def cek_cmd(client, message):
    user = message.from_user
    can_access, role = await check_access(user.id, "cek", client, message)
    if not can_access: return await message.reply(role)    
    msg = await message.reply("<b><i>🔁 Checking...</i></b>")
    user_id = await extract_user(message)
    if not user_id: return await msg.edit("<b>❌ USER TIDAK ADA</b>")    
    exp_date = await get_expired_date(user_id)
    target = await client.get_users(user_id)
    exp_str = exp_date.strftime("%d/%m/%Y") if exp_date else "Non-Aktif"    
    await msg.edit(f"<b>👤 USER INFORMATION</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n<b>👤 Name :</b> {fmt_id(target)}\n<b>🆔 ID :</b> {target.id}\n<b>⌛ Expired :</b> <code>{exp_str}</code>\n\n<blockquote><b>✨ Fanzy Userbot Premium</b></blockquote>")

@PY.BOT("cekdb")
@PY.OWNER
async def cek_db(client, message):
    user = message.from_user
    can_access, role = await check_access(user.id, "cekdb", client, message)
    if not can_access or user.id != OWNER_ID:
        return await message.reply("⚠️ **Hanya Owner Utama yang bisa melihat database raw.**")
    p = await get_vars(bot.me.id, "PREM_USERS") or "∅"
    o = await get_vars(bot.me.id, "OWNER_USERS") or "∅"
    s = await get_vars(bot.me.id, "SELER_USERS") or "∅"
    a = await get_vars(bot.me.id, "ADMIN_USERS") or "∅"
    await send_security_log(client, user, "cekdb", "DATABASE", "SUCCESS", "Memeriksa database raw userbot.")    
    await message.reply(f"<b>📋 DATABASE RAW</b>\n\n<code>PREM:</code> {p}\n<code>OWNER:</code> {o}\n<code>SELES:</code> {s}\n<code>ADMIN:</code> {a}")

@PY.BOT("fixpremdata")
@PY.OWNER
async def fix_prem_data(client, message):
    user = message.from_user
    can_access, role = await check_access(user.id, "fixpremdata", client, message)
    if not can_access or user.id != OWNER_ID:
        return
    msg = await message.reply("<b><i>🔁 Fixing...</i></b>")
    raw = await get_vars(bot.me.id, "PREM_USERS") or ""
    plist = [int(x) for x in raw.replace("\n", " ").split() if x.isdigit()]    
    try:
        await set_vars(bot.me.id, "PREM_USERS", " ".join(map(str, plist)))        
        await send_security_log(client, user, "fixpremdata", "DATABASE", "SUCCESS", "Berhasil merapikan data Premium di database.")        
        await msg.edit(f"<b>✅ DB FIXED!</b>\n<code>{' '.join(map(str, plist))}</code>")
    except Exception as error:
        await send_security_log(client, user, "fixpremdata", "DATABASE", "ERROR", str(error))
        await msg.edit(f"❌ Error: {error}")