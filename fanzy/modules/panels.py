import os, requests, json, asyncio, secrets, string, sys
from cryptography.fernet import Fernet
from fanzy import *
from pyrogram.types import *

# ================== CONFIGURATION ==================
OWNER_IDS = [1322982688]

# ================== SECURITY & DB SYSTEM ==================
PATH_DB = "database/"
if not os.path.exists(PATH_DB): os.makedirs(PATH_DB)
KEY_FILE = PATH_DB + "vault.key"
if not os.path.exists(KEY_FILE):
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f: f.write(key)
else:
    with open(KEY_FILE, "rb") as f: key = f.read()

cipher = Fernet(key)
def enc(t): return cipher.encrypt(str(t).encode()).decode()
def dec(t):
    try: return cipher.decrypt(str(t).encode()).decode()
    except: return t

def manage_db(file, data=None, delete_key=None):
    f_path = PATH_DB + file
    db = {}
    if os.path.exists(f_path):
        with open(f_path, 'r') as f: 
            try: db = json.load(f)
            except: db = {}
    if delete_key:
        if delete_key in db: del db[delete_key]
    elif data:
        db.update(data)
    with open(f_path, 'w') as f: json.dump(db, f, indent=2)
    return db

def log_debug(msg, status=None, response=None):
    print(f"\n[DEBUG] {msg}")
    if status: print(f"[DEBUG] Status Code: {status}")
    if response: print(f"[DEBUG] Raw Response: {response}")

def handle_error(res):
    if not res: 
        return "❌ <b>Koneksi Gagal!</b>\nPanel mungkin sedang Down, Restart, atau diblokir Firewall/Cloudflare."    
    status = res.status_code
    if "text/html" in res.headers.get("Content-Type", "") or res.text.startswith("<!DOCTYPE html>"):
        return (
            f"🌐 <b>PANEL ERROR (HTML) [{status}]</b>\n\n"
            "Panel mengirim tampilan Web, bukan data API. Ini biasanya karena:\n"
            "1. Domain salah (Cek https/http).\n"
            "2. Cloudflare 'Under Attack Mode' aktif.\n"
            "3. Panel sedang maintenance/error internal."
        )
    try:
        data = res.json()
        errors = data.get('errors', [])
        if errors:
            detail = errors[0].get('detail', 'Terjadi kesalahan sistem.')
            code = errors[0].get('code', 'N/A')
            return f"⚠️ <b>PTERO ERROR [{status}]</b>\n\n<b>Detail:</b> <code>{detail}</code>\n<b>Code:</b> <code>{code}</code>"
    except:
        return f"❌ <b>Error {status}:</b> Gagal memproses data API."
    error_map = {
        401: "🔑 <b>TOKEN SALAH!</b>\nToken PLTA expired atau salah ketik.",
        403: "🚫 <b>IZIN DITOLAK!</b>\nToken tidak punya akses (Acl) fitur ini.",
        404: "🌐 <b>URL TIDAK DITEMUKAN!</b>\nCek kembali Domain atau ID tujuan.",
        429: "⏳ <b>RATE LIMIT!</b>\nTerlalu banyak request, tunggu sebentar.",
        500: "🔥 <b>SERVER ERROR!</b>\nPanel tujuan sedang bermasalah internal."
    }
    return error_map.get(status, f"❌ <b>Error {status}:</b> Terjadi kesalahan tidak dikenal.")



# ================== CORE API ENGINE ==================
async def ptero_api(method, url, token, data=None):
    import re
    url = re.sub(r'(?<!:)/+', '/', url) 
    headers = {
        "Authorization": f"Bearer {dec(token)}", 
        "Accept": "application/json", 
        "Content-Type": "application/json"
    }    
    try:
        if method == "GET": r = requests.get(url, headers=headers, timeout=120)
        elif method == "POST": r = requests.post(url, headers=headers, json=data, timeout=120)
        elif method == "DELETE": r = requests.delete(url, headers=headers, timeout=120)
        if r.text.startswith("<!DOCTYPE html>") or "<html" in r.text.lower():
            log_debug("WARNING: Panel ngirim HTML, bukan JSON!")
            r.status_code = 406             
        log_debug("API Response", r.status_code, r.text[:200])
        return r
    except Exception as e:
        log_debug(f"CRITICAL ERROR: {str(e)}")
        return None


async def deploy_logic(client, message, plan, is_admin_panel=False, db_type="public"):
    args = (get_arg(message) or "").split()
    if not args: 
        return await message.reply(f"❌ <b>Format Salah!</b>\nGunakan: <code>.{message.command[0]} [nama_panel] [user]</code>")
    
    pnl_name = args[0]
    target_user = args[1] if len(args) > 1 else f"u_{secrets.token_hex(2)}"
    db_file = "private_panels.json" if db_type == "private" else "public_panels.json"
    db = manage_db(db_file)
    p_data = db.get(pnl_name)
    
    if not p_data: 
        return await message.reply(f"❌ <b>Panel '{pnl_name}'</b> tidak ditemukan di database <code>{db_type.upper()}</code>!")

    # ================= VALIDASI KEAMANAN =================
    if db_type == "public":
        if p_data.get("owner") != message.from_user.id:
            return await message.reply(
                f"🚫 <b>AKSES DITOLAK!</b>\n\n"
                f"Panel <code>{pnl_name}</code> bukan milik Anda.\n"
                f"Anda hanya bisa deploy di panel yang Anda daftarkan sendiri."
            )
    proc = await message.reply(
        f"🚀 <b>PROSES DEPLOY DIMULAI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📂 <b>Database:</b> <code>{db_type.upper()}</code>\n"
        f"📦 <b>Plan:</b> <code>{plan}</code>\n"
        f"👤 <b>User:</b> <code>{target_user}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛰 <i>Sedang menyinkronkan resource...</i>"
    )
    # ---------------------------------

    dom, token = p_data['domain'].rstrip('/'), p_data['plta']
    
    # SCAN NODES & ALLOCATIONS
    res_nodes = await ptero_api("GET", f"{dom}/api/application/locations/{p_data['loc']}?include=nodes", token)
    if not res_nodes or res_nodes.status_code != 200: 
        return await proc.edit(handle_error(res_nodes))    
    try:
        nodes = res_nodes.json()['attributes']['relationships']['nodes']['data']
    except Exception as e:
        log_debug(f"Gagal Parse Nodes: {str(e)}")
        return await proc.edit("❌ <b>Gagal Scan Nodes!</b>\nPanel mengirim respon JSON yang tidak valid.")
    alloc = None
    for node in nodes:
        node_id = node['attributes']['id']
        res_alloc = await ptero_api("GET", f"{dom}/api/application/nodes/{node_id}/allocations", token)        
        if res_alloc and res_alloc.status_code == 200:
            try:
                allocs = res_alloc.json().get('data', [])
                alloc = next((a['attributes']['id'] for a in allocs if not a['attributes']['assigned']), None)
                if alloc: break
            except Exception:
                continue                
    if not alloc: 
        return await proc.edit("❌ **Alokasi Penuh!**\nTidak ditemukan IP/Port kosong di lokasi ini.")
        
    # CREATE USER
    pw = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    u_data = {"email": f"{target_user}{secrets.token_hex(2)}@fanzy.net", "username": target_user, "first_name": target_user, "last_name": "User", "language": "en", "password": pw, "root_admin": is_admin_panel}    
    res_u = await ptero_api("POST", f"{dom}/api/application/users", token, u_data)    
    if not res_u or res_u.status_code not in [200, 201]: 
        return await proc.edit(handle_error(res_u))
    try:
        u_id = res_u.json()['attributes']['id']
    except Exception as e:
        log_debug(f"Gagal Parse User ID: {str(e)}")
        return await proc.edit("❌ <b>Gagal mengambil ID User!</b>\nUser mungkin berhasil dibuat, tapi panel mengirim respon yang tidak valid.")

    # CREATE SERVER
    ram_map = {"1GB": 1024, "2GB": 2048, "5GB": 5120, "UNLIMITED": 0}
    ram = ram_map.get(plan, 2048)
    srv_data = {
        "name": f"{target_user}", "user": u_id, "nest": p_data['nest'], "egg": p_data['egg'],
        "docker_image": "ghcr.io/parkervcp/yolks:nodejs_18", "startup": "npm start",
        "environment": {"CMD_RUN": "npm start"},
        "limits": {"memory": ram, "swap": 0, "disk": 10240, "io": 500, "cpu": 0},
        "feature_limits": {"databases": 5, "allocations": 1, "backups": 5},
        "allocation": {"default": alloc}
    }
    res_s = await ptero_api("POST", f"{dom}/api/application/servers", token, srv_data)
    if res_s and res_s.status_code == 201:
        try:
            s_data = res_s.json()['attributes']
            s_id = s_data['id']
            s_uuid = s_data['uuid'][:8] # Ambil 8 karakter awal UUID biar keren
            s_name = s_data['name']
        except:
            s_id, s_uuid, s_name = "N/A", "N/A", target_user
        await proc.delete()
        caption = (
            f"<b>✅ DEPLOY {db_type.upper()} SUCCES</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"📑 <b>INFORMASI SERVER</b>\n"
            f" • <b>ID Server:</b> <code>{s_id}</code> (<code>{s_uuid}</code>)\n"
            f" • <b>Username:</b> <code>{target_user}</code>\n"
            f" • <b>Password:</b> <code>{pw}</code>\n"
            f" • <b>Ram Panel:</b> <code>{plan}</code>\n"
            f" • <b>Role Panel:</b> <code>{'Admin' if is_admin_panel else 'Member'}</code>\n"
            f" • <b>ID User:</b> <code>{u_id}</code>\n"                        
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 <b>DOMAIN PANEL:</b> [ <a href='{p_data['domain']}'>Click</a> ]\n"
            f"👷 <b>Pelaku:</b> <a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"<b><blockquote>✨ Power By Fanzy Userbot</blockquote></b>"
        )        
        await client.send_photo(
            message.chat.id, 
            "https://files.catbox.moe/a7ljii.jpeg", 
            caption=caption
        )
    else: 
        await proc.edit(handle_error(res_s))

# ================== 1. FITUR PUBLIC ==================

@PY.UBOT("setpnl")
async def public_add(client, message):
    args = get_arg(message).split()
    if not message.reply_to_message or len(args) < 5:
        return await message.reply("⚠️ **Format:** <code>.setpnl [nama] [dom] [egg] [loc] [nest]</code> (Reply Token)")   
    token = message.reply_to_message.text.strip()
    name = args[0].strip().strip(",.;'\"")    
    dom = args[1].strip().strip(",.;'\"").rstrip("/")
    if not dom.startswith("http"): 
        dom = f"https://{dom}"
    def clean_int(val):
        import re
        num = re.sub(r'\D', '', str(val))
        return int(num) if num else 0 
    try:
        egg_val = clean_int(args[2])
        loc_val = clean_int(args[3])
        nest_val = clean_int(args[4])
        if any(v == 0 for v in [egg_val, loc_val, nest_val]):
            return await message.reply("❌ <b>Error:</b> Egg, Loc, atau Nest tidak boleh 0 atau kosong!")
    except Exception:
        return await message.reply("❌ <b>Error:</b> Pastikan Egg, Loc, dan Nest adalah angka valid!")
    data = {
        name: {
            "domain": dom, 
            "plta": enc(token), 
            "egg": egg_val, 
            "loc": loc_val, 
            "nest": nest_val,
            "owner": message.from_user.id
        }
    }
    manage_db("public_panels.json", data=data)
    await message.reply(
        f"✅ <b>SUCCESSFULY ADD PANEL! </b>\n\n"
        f"• 👤 <b>Users:</b> <code>{message.from_user.id}</code>\n"
        f"• 🏷 <b>Nama:</b> <code>{name}</code>\n"
        f"• 🌐 <b>Host:</b> [ <a href='{dom}'>Click</a> ]\n"
        f"• 🥚 <b>Egg ID:</b> <code>{egg_val}</code>\n"
        f"<b><blockquote>✨ Power By Fanzy Userbot</blockquote></b>", 
        disable_web_page_preview=True 
    )

@PY.UBOT("listpnl")
async def public_list(client, message):
    db = manage_db("public_panels.json")
    if not db: 
        return await message.reply("📑 <b>DATABASE PUBLIK KOSONG</b>")        
    
    txt = "<b>🌐 LIST DOMAIN PANEL</b>\n"
    txt += "━━━━━━━━━━━━━━━━━━━\n\n"
    
    all_items = [i for i in db.items()]
    total = len(all_items)
    
    for index, (k, v) in enumerate(all_items):
        txt += f" • 🆔 <b>ID:</b> <code>{index + 1}</code>\n"
        txt += f" • 🏷 <b>Nama Panel:</b> <code>{k}</code>\n"
        txt += f" • 🌐 <b>Domain:</b> [ <a href='{v['domain']}'>Click Here</a> ]"        
        if index < total - 1:
            txt += "\n\n"
        else:
            txt += "\n"                
    txt += "━━━━━━━━━━━━━━━━━━━\n"
    txt += f"<b><blockquote>✨ Power By Fanzy Userbot</blockquote></b>"    
    await message.reply(txt, disable_web_page_preview=True)



@PY.UBOT("delpnl")
async def public_del(client, message):
    arg = get_arg(message)
    if not arg: return await message.reply("❌ Nama panel?")
    db = manage_db("public_panels.json")
    p = db.get(arg)
    if not p: return await message.reply("❌ Panel tidak ditemukan.")
    if p.get("owner") != message.from_user.id:
        return await message.reply("🚫 **Akses Ditolak!** Anda tidak punya izin menghapus panel ini.")
    manage_db("public_panels.json", delete_key=arg)
    await message.reply(f"🗑 Panel **{arg}** berhasil dihapus dari database.")


@PY.UBOT("c1gb|c2gb|c5gb|cunlimited")
async def public_deploy(client, message):
    plan = message.command[0][1:].upper()
    await deploy_logic(client, message, plan, is_admin_panel=False, db_type="public")

@PY.UBOT("cadmin")
async def public_deploy_admin(client, message):
    await deploy_logic(client, message, "2GB", is_admin_panel=True, db_type="public")

@PY.UBOT("listsrv|listusr")
async def public_fetch(client, message):
    args = get_arg(message).split()
    if not args: 
        return await message.reply("❌ **Format:** <code>.listsrv [nama_panel]</code>")        
    db = manage_db("public_panels.json")
    p = db.get(args[0])
    if not p: 
        return await message.reply("❌ Panel tidak ditemukan!")    
    if p.get("owner") != message.from_user.id:
        return await message.reply("🚫 **Akses Ditolak!** Anda bukan pemilik panel ini.")        
    cmd = message.command[0]
    path = "servers" if "srv" in cmd else "users"    
    res = await ptero_api("GET", f"{p['domain']}/api/application/{path}", p['plta'])
    if not res or res.status_code != 200: 
        return await message.reply(handle_error(res))       
    try:
        data_json = res.json()
        items = data_json.get('data', [])
    except Exception as e:
        log_debug(f"Gagal Parse JSON: {str(e)}")
        return await message.reply("❌ <b>Gagal Memproses Data!</b>\nRespon dari panel tidak valid.")    
    if not items: 
        return await message.reply(f"📭 Tidak ada data {path} di panel ini.")    
    
    txt = f"<b>📋 LIST {path.upper()} - {args[0].upper()}</b>\n"
    txt += "━━━━━━━━━━━━━━━━━━━\n\n"    
    
    display_items = items[:25]
    total_display = len(display_items)
    
    for index, i in enumerate(display_items):
        attr = i.get('attributes', {})
        
        if "srv" in cmd:
            is_suspended = attr.get('suspended', False)
            status_icon = "🔴" if is_suspended else "🟢"
            status_text = "OFF" if is_suspended else "ACTIVE"            
            name_val = attr.get('name', 'Unknown')         
            limits = attr.get('limits', {})
            created = attr.get('created_at', '2026-04-09')[:10]
            txt += f" • ID: <code>{attr.get('id')}</code>\n"
            txt += f" • Nama Server: <b>{attr.get('name', 'Unknown')}</b>\n"
            txt += f" • RAM: <code>{limits.get('memory', 'Unlimited')}</code>\n"
            txt += f" • Disk: <code>{limits.get('disk', 'Unlimited')}</code>\n"
            txt += f" • CPU: <code>{limits.get('cpu', 'Unlimited')}</code>\n"
            txt += f" • Dibuat: <code>{created}</code>\n"
            txt += f" • Status Server: {status_icon} {status_text}"
        else:
            # Tampilan Listusr (Konsep sama, tapi UX berbeda dari gambar)
            is_admin = attr.get('root_admin', False)
            status = "🌟 Admin" if is_admin else "👤 Member"
            txt += f"👤 <b>Username:</b> <code>{attr.get('username', 'Unknown')}</code>\n"
            txt += f"🆔 <b>ID User:</b> <code>{attr.get('id')}</code>\n"
            txt += f"🛡 <b>Role:</b> <code>{status}</code>"
            
        if index < total_display - 1:
            txt += "\n\n"
        else:
            txt += "\n"
            
    txt += f"━━━━━━━━━━━━━━━━━━━\n"           
    txt += f"<b>Total {path.capitalize()} Panels:</b> {len(items)} {path}\n"
    txt += f"<b><blockquote>✨ Power By Fanzy Userbot</blockquote></b>"    
    await message.reply(txt)


@PY.UBOT("delsrv|delusr")
async def public_delete_res(client, message):
    args = get_arg(message).split()
    if len(args) < 2: return await message.reply("❌ <b>Format:</b> <code>.delsrv [pnl] [id_angka]</code>")    
    if not args[1].isdigit():
        return await message.reply("⚠️ <b>Gunakan ID Angka!</b>\nCek ID server/user dulu pakai <code>.listsrv</code> atau <code>.listusr</code>")        
    db = manage_db("public_panels.json")
    p = db.get(args[0])
    if not p: 
        return await message.reply(f"❌ Panel <b>{args[0]}</b> tidak ditemukan.")    
    if p.get("owner") != message.from_user.id:
        return await message.reply("🚫 <b>Akses Ditolak!</b> Anda bukan pemilik panel ini.")        
    cmd = message.command[0]
    path = "servers" if "srv" in cmd else "users"
    proc = await message.reply(f"🗑 <b>Menghapus {path[:-1]} ID {args[1]}...</b>")
    res = await ptero_api("DELETE", f"{p['domain']}/api/application/{path}/{args[1]}", p['plta'])
    if res and res.status_code == 204: 
        await proc.edit(f"✅ <b>Berhasil!</b> ID <code>{args[1]}</code> dihapus.")
    else:
        await proc.edit(handle_error(res))

@PY.UBOT("listadmin")
async def public_list_admin(client, message):
    args = (get_arg(message) or "").split()
    if not args: 
        return await message.reply("❌ **Format:** <code>.listadmin [nama_panel]</code>")        
    db = manage_db("public_panels.json")
    p = db.get(args[0])
    if not p: 
        return await message.reply(f"❌ Panel <b>{args[0]}</b> tidak ditemukan!")    
    if p.get("owner") != message.from_user.id:
        return await message.reply("🚫 **Akses Ditolak!** Anda bukan pemilik panel ini.")            
    proc = await message.reply(f"🔍 <b>Scanning Admin di {args[0].upper()}...</b>")
    res = await ptero_api("GET", f"{p['domain']}/api/application/users", p['plta'])
    
    if not res or res.status_code != 200: 
        return await proc.edit(handle_error(res))           
    try:
        users = res.json().get('data', [])
        admins = [u['attributes'] for u in users if u['attributes'].get('root_admin')]
    except Exception:
        return await proc.edit("❌ <b>Gagal Parse Data!</b>")
    if not admins:
        return await proc.edit(f"📭 Tidak ada Admin di panel <b>{args[0]}</b>.")    
    txt = f"<b>Total admin panels :</b> <code>{len(admins)}</code>\n\n"
    for adm in admins:
        txt += f"• 🆔 <b>ID:</b> <code>{adm['id']}</code>\n"
        txt += f"• 👤 <b>Username:</b> <code>{adm['username']}</code>\n\n"
    txt += f"<b><blockquote>✨ Power By Fanzy Userbot</blockquote></b>"
    await proc.edit(txt)



# ================== 2. FITUR PRIVATE (OWNER ONLY) ==================

@PY.UBOT("addpnl")
async def private_add(client, message):
    if message.from_user.id not in OWNER_IDS: return
    args = get_arg(message).split()
    if not message.reply_to_message or len(args) < 5:
        return await message.reply("⚠️ **Owner Format:** <code>.addpnl [nama] [dom] [egg] [loc] [nest]</code> (Reply Token)")    
    token = message.reply_to_message.text.strip()    
    name = args[0].strip().strip(",.;'\"")
    dom = args[1].strip().strip(",.;'\"").rstrip("/")
    if not dom.startswith("http"): dom = f"https://{dom}"
    import re
    try:
        egg = int(re.sub(r'\D', '', args[2]))
        loc = int(re.sub(r'\D', '', args[3]))
        nest = int(re.sub(r'\D', '', args[4]))
    except Exception:
        return await message.reply("❌ <b>Error:</b> Data Resource (Egg/Loc/Nest) harus angka!")
    data = {
        name: {
            "domain": dom, 
            "plta": enc(token), 
            "egg": egg, 
            "loc": loc, 
            "nest": nest
        }
    }
    manage_db("private_panels.json", data=data)
    await message.reply(
        f"✅ <b>PANEL PRIVAT DISIMPAN! </b>\n\n"
        f"• 🏷 <b>Nama:</b> <code>{name}</code>\n"
        f"• 🌐 <b>Host:</b> [ <a href='{dom}'>Click</a> ]\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"<b><blockquote>✨ Power By Fanzy Userbot</blockquote></b>",
        disable_web_page_preview=True 
    )

@PY.UBOT("listpanel")
async def private_list(client, message):
    if message.from_user.id not in OWNER_IDS: return
    db = manage_db("private_panels.json")
    if not db: 
        return await message.reply("📑 <b>DATABASE PRIVATE KOSONG</b>")    
    
    txt = "<b>🔐 LIST DOMAIN PANEL</b>\n"
    txt += "━━━━━━━━━━━━━━━━━━━\n\n"        
    all_items = [i for i in db.items()]
    total = len(all_items)        
    for index, (k, v) in enumerate(all_items):
        # Format list singkat dan rapi (ID, Nama, Domain)
        txt += f" • 🆔 <b>ID:</b> <code>{index + 1}</code>\n"
        txt += f" • 🏷 <b>Nama Panel:</b> <code>{k}</code>\n"
        txt += f" • 🌐 <b>Host:</b> [ <a href='{v['domain']}'>Click</a> ]"        
        
        if index < total - 1:
            txt += "\n\n"
        else:
            txt += "\n"            
    txt += "━━━━━━━━━━━━━━━━━━━\n"        
    txt += f"<b><blockquote>✨ Power By Fanzy Userbot</blockquote></b>"
    await message.reply(txt, disable_web_page_preview=True)


@PY.UBOT("delete")
async def private_del(client, message):
    if message.from_user.id not in OWNER_IDS: return
    arg = get_arg(message)
    manage_db("private_panels.json", delete_key=arg)
    await message.reply(f"🗑 Panel **{arg}** dihapus dari Private.")

@PY.UBOT("1gb|2gb|5gb|unlimited")
async def private_deploy(client, message):
    if message.from_user.id not in OWNER_IDS: return
    await deploy_logic(client, message, message.command[0].upper(), is_admin_panel=False, db_type="private")
    
@PY.UBOT("admin")
async def private_deploy_admin(client, message):
    if message.from_user.id not in OWNER_IDS: return
    await deploy_logic(client, message, "2GB", is_admin_panel=True, db_type="private")
    
@PY.UBOT("serverlist|userlist")
async def private_fetch(client, message):
    if message.from_user.id not in OWNER_IDS: return
    args = (get_arg(message) or "").split()
    if not args: 
        return await message.reply("❌ <b>Nama panel?</b>")    
    db = manage_db("private_panels.json")
    p = db.get(args[0])
    if not p: 
        return await message.reply("❌ <b>Panel tidak ditemukan!</b>")            
    cmd = message.command[0]
    path = "servers" if "server" in cmd else "users"    
    res = await ptero_api("GET", f"{p['domain']}/api/application/{path}", p['plta'])
    
    if not res or res.status_code != 200: 
        return await message.reply(handle_error(res))        
    try:
        data_json = res.json()
        items = data_json.get('data', [])
    except Exception as e:
        log_debug(f"Gagal Parse JSON Private: {str(e)}")
        return await message.reply("❌ <b>Gagal memproses data API!</b>\nRespon panel tidak valid.")        
    if not items: 
        return await message.reply(f"📭 Tidak ada data {path} di panel ini.")        
    
    txt = f"<b>🛡️ PRIVATE {path.upper()} - {args[0].upper()}</b>\n"
    txt += "━━━━━━━━━━━━━━━━━━━\n\n"        
    display_items = items[:25]
    total_display = len(display_items)        
    for index, i in enumerate(display_items):
        attr = i.get('attributes', {})
        if "server" in cmd:
            is_suspended = attr.get('suspended', False)
            status_icon = "🔴" if is_suspended else "🟢"
            status_text = "OFF" if is_suspended else "ACTIVE"            
            name_val = attr.get('name', 'Unknown')            
            limits = attr.get('limits', {})
            created = attr.get('created_at', '2026-04-09')[:10]            
            txt += f" • ID: <code>{attr.get('id')}</code>\n"
            txt += f" • Nama Server: <b>{name_val}</b>\n"
            txt += f" • RAM: <code>{limits.get('memory', 'Unlimited')}</code>\n"
            txt += f" • Disk: <code>{limits.get('disk', 'Unlimited')}</code>\n"
            txt += f" • CPU: <code>{limits.get('cpu', 'Unlimited')}</code>\n"
            txt += f" • Dibuat: <code>{created}</code>\n"
            txt += f" • Status Server: {status_icon} {status_text}"
        else:
            is_admin = attr.get('root_admin', False)
            role_icont = "🌟" if is_admin else "👤"
            role_teks = "admin" if is_admin else "member"
            user_val = attr.get('username', 'Unknown')
            
            # Format User List
            txt += f"👤 <b>Username:</b> <code>{user_val}</code>\n"
            txt += f"🆔 <b>ID User:</b> <code>{attr.get('id')}</code>\n"
            txt += f"🛡 <b>Role:</b> <code>{role_icont} {role_teks}</code>"
            
        if index < total_display - 1:
            txt += "\n\n"
        else:
            txt += "\n"            
    txt += "━━━━━━━━━━━━━━━━━━━\n"
    txt += f"<b><blockquote>✨ Power By Fanzy Userbot</blockquote></b>"    
    await message.reply(txt)



@PY.UBOT("serverdel|userdel")
async def private_delete_res(client, message):
    if message.from_user.id not in OWNER_IDS: return
    args = get_arg(message).split()
    if len(args) < 2: return await message.reply("❌ **Format:** `[nama_pnl] [id]`")
    db = manage_db("private_panels.json")
    p = db.get(args[0])
    if not p:
        return await message.reply(f"❌ Panel **{args[0]}** tidak ditemukan!")
    cmd = message.command[0]
    path = "servers" if "server" in cmd else "users"
    proc = await message.reply(f"🗑 **Menghapus {path[:-1]} ID {args[1]}...**")
    res = await ptero_api("DELETE", f"{p['domain']}/api/application/{path}/{args[1]}", p['plta'])
    if res and res.status_code == 204: 
        await proc.edit(f"✅ **Berhasil!** ID <code>{args[1]}</code> telah dihapus dari panel <b>{args[0]}</b>.")
    else:
        err_msg = handle_error(res)
        if "active servers" in err_msg.lower():
            await proc.edit(f"⚠️ **Gagal Hapus User!**\n\nUser ID <code>{args[1]}</code> masih memiliki server aktif. Silakan hapus semua server milik user tersebut dulu dengan perintah `.serverdel` baru hapus usernya.")
        else:
            await proc.edit(err_msg)

@PY.UBOT("listatmin") 
async def private_list_admin(client, message):
    if message.from_user.id not in OWNER_IDS: return
    args = (get_arg(message) or "").split()
    if not args: 
        return await message.reply("❌ <b>Nama panel?</b>")    
    db = manage_db("private_panels.json")
    p = db.get(args[0])
    if not p: 
        return await message.reply(f"❌ Panel <b>{args[0]}</b> tidak ditemukan!")        
    proc = await message.reply(f"🛡️ <b>Scanning Admin Private: {args[0].upper()}...</b>")
    res = await ptero_api("GET", f"{p['domain']}/api/application/users", p['plta'])    
    if not res or res.status_code != 200: 
        return await proc.edit(handle_error(res))    
    try:
        users = res.json().get('data', [])
        admins = [u['attributes'] for u in users if u['attributes'].get('root_admin')]
    except Exception:
        return await proc.edit("❌ <b>Gagal memproses data API!</b>")
    if not admins:
        return await proc.edit(f"📭 Tidak ada admin di panel private <b>{args[0]}</b>.")    
    txt = f"<b>🛡️ PRIVATE ADMINS - {args[0].upper()}</b>\n"
    txt += "━━━━━━━━━━━━━━━━━━━\n\n"    
    for adm in admins:
        txt += f" • 🆔 <b>ID:</b> <code>{adm['id']}</code>\n"
        txt += f" • 👤 <b>Username:</b> <code>{adm['username']}</code>\n"
    txt += "━━━━━━━━━━━━━━━━━━━\n"
    txt += f"<b><blockquote>✨ Power By Fanzy Userbot</blockquote></b>"    
    await proc.edit(txt)


__MODULE__ = "Panel"
__HELP__ = """
<b>::: 💠 PTERO GODMODE V7 :::</b>

<b>🌍 PUBLIC COMMANDS:</b>
├ <code>{0}setpnl</code> 
├ <code>{0}listpnl</code>
├ <code>{0}delpnl</code>
├ <code>{0}c1gb</code>
├ <code>{0}cunlimited</code>
├ <code>{0}cadmin</code>
├ <code>{0}listadmin</code>
├ <code>{0}listsrv</code>
├ <code>{0}listusr</code>
├ <code>{0}delsrv</code>
╰ <code>{0}delusr</code>

<b>🔐 OWNER COMMANDS:</b>
├ <code>{0}addpnl</code>
├ <code>{0}listpanel</code>
├ <code>{0}delete</code>
├ <code>{0}1gb</code>
├ <code>{0}unlimited</code>
├ <code>{0}admin</code>
├ <code>{0}listatmin</code>
├ <code>{0}serverlist</code>
├ <code>{0}userlist</code>
├ <code>{0}serverdel</code>
╰ <code>{0}userdel</code>

📌 Penggunaan: <a href='https://t.me/Tutorialubot'>Click Here</a>
"""