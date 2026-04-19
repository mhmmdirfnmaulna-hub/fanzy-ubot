import time
import asyncio
import aiohttp
import re
import socket
import paramiko
from fanzy.core.database import mongodb
import html
from pyrogram.errors import MessageNotModified, FloodWait, MessageIdInvalid, RPCError
from fanzy.core.helpers.tools import get_arg
from fanzy import PY
from pyrogram.enums import ParseMode

bot_config = mongodb.bot_config

def clean_ansi(text):
    return re.sub(r'\x1b\[[0-9;]*[mGKH]', '', text)    
    
def is_valid_ip(ip):
    # Strict IPv4 Validation
    return bool(re.match(r"^(\d{1,3}\.){3}\d{1,3}$", ip))

def is_valid_domain(domain):
    # RFC 1035 compliant domain check
    return bool(re.match(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$", domain))

async def safe_edit(message, text, **kwargs):
    if not message:
        return None
    options = {
        "parse_mode": ParseMode.HTML,
        "disable_web_page_preview": True
    }
    options.update(kwargs)
    for attempt in range(5):
        try:
            return await message.edit_text(text, **options)       
        except MessageNotModified:
            return message            
        except FloodWait as e:
            await asyncio.sleep(e.value + 2)
            continue            
        except (MessageIdInvalid, RPCError):
            try:
                return await message.reply_text(text, **options)
            except Exception:
                return None                
        except Exception:
            await asyncio.sleep(1)
            continue
    return None

async def wait_for_ssh(host, port=22, timeout=500):
    start_time = time.time()
    while time.time() - start_time < timeout:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        try:
            result = sock.connect_ex((host, port))
            if result == 0:
                sock.close()
                return True
        except Exception:
            pass
        finally:
            sock.close()        
        await asyncio.sleep(5)
    return False

async def send_and_wait_uninstall(chan, command, logic_map):
    chan.send(f"{command}\n")
    start_time = time.time()
    full_output = ""
    last_send_time = time.time() 
    await asyncio.sleep(1.5)             
    while time.time() - start_time < 600:
        if chan.recv_ready():
            chunk = chan.recv(10240).decode("utf-8", errors="ignore")
            full_output += chunk
            for key in list(logic_map.keys()):
                if key.lower() in chunk.lower() or key.lower() in full_output.lower():
                    response = logic_map[key]
                    await asyncio.sleep(0.8)
                    chan.send(f"{response}\n")
                    del logic_map[key]
                    full_output = "" 
                    last_send_time = time.time()
                    break             
            
            current_buffer = clean_ansi(full_output.strip())[-250:]            
            if re.search(r"(root@.*|#|~#|:\s#|:\s\$)\s*$", current_buffer):
                if len(logic_map) == 0 or "Nothing to uninstall" in current_buffer:
                    break
                else:
                    if time.time() - last_send_time > 8:
                        chan.send("\n")
                        last_send_time = time.time()                   
            if "Nothing to uninstall" in current_buffer or "uninstallation completed" in current_buffer:
                break                                
        await asyncio.sleep(0.5)

async def send_and_wait(chan, command_to_run, logic_map, username="root"):
    chan.send(f"{command_to_run}\n")
    start_time = time.time()
    full_output = ""
    last_poke = time.time()     
    while time.time() - start_time < 900:
        if chan.recv_ready():
            chunk = chan.recv(10240).decode("utf-8", errors="ignore")
            full_output += chunk
            last_poke = time.time()
            found_key = False
            for key, response in list(logic_map.items()):
                if key.lower() in chunk.lower() or key.lower() in full_output.lower():
                    await asyncio.sleep(0.5) 
                    chan.send(f"{response}\n")
                    del logic_map[key]
                    found_key = True
                    full_output = ""
                    break 
            if found_key: continue        
        current_buffer = clean_ansi(full_output.strip())[-100:]
        if re.search(r"(root@|#|~#|:\s#|:\s\$)\s*$", current_buffer):
            if time.time() - start_time > 5:
                break
        if time.time() - last_poke > 30:
            chan.send("\n")
            last_poke = time.time()
        await asyncio.sleep(0.2)
    chan.send("\003") 
    await asyncio.sleep(1)
    while chan.recv_ready():
        chan.recv(10240)
        await asyncio.sleep(0.1)

async def run_cleardb_logic(ssh, proc, is_unpanel=False):
    await safe_edit(proc, "🧹 **proses cleardb...**")    
    deep_clean_cmd = (
        "sudo systemctl stop wings mariadb mysql redis-server nginx 2>/dev/null; "       
        "sudo killall -9 apt apt-get dpkg mariadbd mysqld nginx 2>/dev/null; "
        "sudo rm -f /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock*; "
        "sudo dpkg --configure -a; "                                   
        "sudo DEBIAN_FRONTEND=noninteractive apt-get purge -y mariadb-server mariadb-client mariadb-common mysql-common nginx-common nginx-full php* 2>/dev/null; "                        
        "sudo rm -rf /var/lib/mysql /etc/mysql /var/log/mysql /var/lib/mysql-files /var/lib/mysql-keyring; "                                     
        "sudo rm -rf /var/www/pterodactyl /etc/pterodactyl /var/lib/pterodactyl /var/log/pterodactyl; "            
        "sudo rm -rf /etc/nginx/sites-enabled/* /etc/nginx/sites-available/* /etc/nginx/conf.d/*; "
        "sudo apt-get install --reinstall nginx-common -y; "            
        "sudo userdel -r pterodactyl 2>/dev/null; sudo groupdel pterodactyl 2>/dev/null; "
        "sudo userdel -r mysql 2>/dev/null; sudo groupdel mysql 2>/dev/null; "
        "sudo rm -rf /etc/letsencrypt /var/lib/letsencrypt /var/log/letsencrypt; "                       
        "docker ps -aq | xargs -r docker rm -f; "
        "docker images -aq | xargs -r docker rmi -f; "
        "docker network prune -f; docker volume prune -f; "            
        "sudo apt-get autoremove -y; sudo apt-get autoclean; sudo apt-get install -f; "            
        "echo 'DEEP_CLEAN_DONE'"
    )
    stdin, stdout, stderr = ssh.exec_command(deep_clean_cmd)
    exit_status = stdout.channel.recv_exit_status() 
    success_msg = "✅ <b>SUCCES UNINSTALLPANEL</b>" if is_unpanel else "✅ <b>SUCCES CLEARDB</b>"
    if exit_status == 0:
        await safe_edit(proc, success_msg)
    else:
        await safe_edit(proc, "⚠️ **Pembersihan selesai dengan catatan.**")

# ==========================================
#        COMMAND: INSTALL PANEL & NODE
# ==========================================
@PY.UBOT("instllpnl")
async def install_panel_vps(client, message):
    args = get_arg(message)
    if not args or args.count("|") < 4:
        return await message.reply("❌ **Format:** `.instllpnl ipvps|pwvps|panel.com|node.com|ram`")    
    vii = args.split("|")
    ip_vps, pw_vps, domain_p, domain_n, ram = vii[0], vii[1], vii[2], vii[3], vii[4]
    if not is_valid_ip(ip_vps):
        return await message.reply("❌ **IP VPS Tidak Valid.**")
    if not is_valid_domain(domain_p):
        return await message.reply("❌ **Domain Panel Tidak Valid.**")
    password_panel = "admin001"    
    def get_progress_text(step1="⏳", step2="▫️", step3="▫️", status="Sedang memproses..."):
        return (
            f"<b>🚀 Proses Deployment Panel</b>\n<code>----------------------</code>\n"
            f"<b>📍 IP VPS :</b> <code>{ip_vps}</code>\n<b>🌐 Domain Panel :</b> <a href='https://{domain_p}'>Click Here</a>\n"
            f"<code>----------------------</code>\n{step1} <b>1. Install Panel</b>\n{step2} <b>2. Install Wings</b>\n"
            f"{step3} <b>3. Configure Node</b>\n<code>----------------------</code>\n<i>{status}</i>"
        )    
    proc = await message.reply(get_progress_text(), parse_mode=ParseMode.HTML)   
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        try:
            val_ram = int(ram)
            ram_mb = str(val_ram * 1024) if val_ram < 100 else str(val_ram)
        except:
            ram_mb = "1024"
        await safe_edit(proc, "🔍 **Memeriksa koneksi SSH VPS...**")
        if not await wait_for_ssh(ip_vps):
            return await safe_edit(proc, "❌ **Gagal:** Port SSH (22) tidak merespon/Timeout.")
        ssh.connect(ip_vps, username="root", password=pw_vps, timeout=30)
        chan = ssh.invoke_shell(term='xterm', width=250, height=50)        
        await safe_edit(proc, "🧹 **Membersihkan sisa-sisa panel lama...**")
        ssh.exec_command("rm -rf /var/www/pterodactyl /etc/nginx/sites-enabled/pterodactyl.conf")
        await asyncio.sleep(5) 
        await safe_edit(proc, get_progress_text("🔄", "▫️", "▫️", "Installing Pterodactyl Panel..."))
        panel_logic = {
            "Database name (panel)": "panel", "Database username (pterodactyl)": "admin", "Password (press enter to use randomly generated password)": "admin",
            "Select timezone": "Asia/Jakarta", "Provide the email address": "admin@gmail.com", "Email address for the initial admin account": "admin@gmail.com",
            "Username for the initial admin account": "admin", "First name for the initial admin account": "Admin", "Last name for the initial admin account": "Panel",
            "Password for the initial admin account": password_panel, "Set the FQDN of this panel": domain_p, "root password": pw_vps,
            "MySQL password": pw_vps, "Select the appropriate number [1-2]": "1", "Attempt to reinstall this existing certificate": "1",
            "Initial configuration completed. Continue with installation?": "y", "I agree that this HTTPS request is performed": "y", "Are you sure you want to proceed": "y",
            "Enable sending anonymous telemetry": "y", "automatically configure UFW": "y", "automatically configure HTTPS": "y", "Overwrite existing": "y",
            "Input 0-6": "0", "(y/N)": "y", "yes/no": "y", "y/n": "y"
        }
        await send_and_wait(chan, "bash <(curl -s https://pterodactyl-installer.se)", panel_logic)
        await safe_edit(proc, get_progress_text("✅", "🔄", "▫️", "Installing Wings Daemon..."))
        wings_logic = {
            "I agree that this HTTPS request": "y", "Database host username": "admin", "Database host password": "admin",
            "Enter the panel address": domain_p, "Set the FQDN": domain_n, "Enter email address": "admin@gmail.com",
            "Proceed with installation?": "y", "automatically configure UFW": "y", "automatically configure a user": "y",
            "configure MySQL to be accessed externally": "y", "allow incoming traffic to port 3306": "y", "automatically configure HTTPS": "y",
            "Input 0-6": "1", "(y/N)": "y", "Select the appropriate number [1-2]": "1", "Attempt to reinstall this existing certificate": "1"           
        }
        await send_and_wait(chan, "bash <(curl -s https://pterodactyl-installer.se)", wings_logic)
        await safe_edit(proc, get_progress_text("✅", "✅", "🔄", "Creating Node & Location..."))
        node_logic = {
            "Masukkan nama lokasi": "Singapore", "Masukkan deskripsi lokasi": "Node By Fanzy Bot", "Masukkan domain": domain_n,
            "Masukkan nama node": "NODE-FANZY", "Masukkan RAM": ram_mb, "over allocate": "0", "maximum filesize": "100",
            "Masukkan jumlah maksimum disk": ram_mb, "listening port": "8080", "SFTP listening port": "2022", "Masukkan Locid": "1", "yes/no": "y"
        }
        await send_and_wait(chan, "bash <(curl -s https://raw.githubusercontent.com/SkyzoOffc/Pterodactyl-Theme-Autoinstaller/main/createnode.sh)", node_logic)
        await asyncio.sleep(2)           
        chan.send("\n") 
        await asyncio.sleep(1)       
        while chan.recv_ready(): chan.recv(10240)
        await safe_edit(proc, get_progress_text("✅", "✅", "✅", "Verifying Services..."))        
        def get_service_status(service_name):
            _, stdout, _ = ssh.exec_command(f"systemctl is-active {service_name}")
            return "🟢 Online" if stdout.read().decode().strip() == "active" else "🔴 Offline"
        teks_selesai = (
            f"<b>✅ DEPLOYMENT COMPLETED</b>\n<code>--------------------------</code>\n"
            f"<b>🌐 Panel URL  :</b> <a href='https://{domain_p}'>Click Here</a>\n"
            f"<b>👤 Username   :</b> <code>admin</code>\n<b>🔑 Password   :</b> <code>{password_panel}</code>\n"
            f"<code>----------------------</code>\n<b>📊 SYSTEM STATUS:</b>\n"
            f"  ▫️ <b>Panel Web  :</b> {get_service_status('nginx')}\n  ▫️ <b>Wings Node :</b> {get_service_status('wings')}\n"
            f"  ▫️ <b>Location   :</b> 🇸🇬 Singapore\n\n✨ <i>Panel Pterodactyl Terinstall!</i>"
        )
        await safe_edit(proc, teks_selesai)        
    except Exception as e:
        await safe_edit(proc, f"❌ **DEPLOYMENT FAILED**\n\n<b>Error:</b> <code>{str(e)}</code>")
    finally:
        ssh.close()

# ==========================================
#        COMMAND: UNINSTALL & CLEARDB
# ==========================================
@PY.UBOT("|unpanel")
async def uninstall_full_vps(client, message):
    cmd = message.command[0]    
    args = get_arg(message)
    if not args or "|" not in args:
        return await message.reply(f"<b>Ex:</b> <code>.{cmd} ipvps|pwvps</code>", parse_mode=ParseMode.HTML)    
    vii = args.split("|")
    ipvps, passwd = vii[0], vii[1]    
    proc = await message.reply("🔄 **Menghubungkan ke VPS...**")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())    
    try:
        ssh.connect(ipvps, username="root", password=passwd, timeout=30)
        chan = ssh.invoke_shell(term='xterm', width=250, height=50)
        await safe_edit(proc, "♻️ **Menjalankan uninstall panel...**")        
        uninstall_logic = {
            "Input 0-6": "6", "remove panel?": "y", "remove Wings (daemon)": "y", "(y/N)": "y",
            "Database called panel has been detected": "y", "Choose the panel user": "", "Choose the panel database": "", "Are you sure": "y"
        }        
        await send_and_wait_uninstall(chan, "bash <(curl -s https://pterodactyl-installer.se)", uninstall_logic)
        chan.send("\x03")
        await asyncio.sleep(1)
        chan.send("\n")
        await asyncio.sleep(1)        
        if chan.recv_ready(): chan.recv(10240)
        await run_cleardb_logic(ssh, proc, is_unpanel=True)
    except Exception as e:
        await safe_edit(proc, f"❌ **Gagal:** <code>{str(e)}</code>")
    finally:
        ssh.close()

@PY.UBOT("cleardb")
async def cleardb_command(client, message):
    args = get_arg(message)
    if not args or "|" not in args:
        return await message.reply(f"<b>Ex:</b> <code>.cleardb ipvps|pwvps</code>", parse_mode=ParseMode.HTML)
    vii = args.split("|")
    ipvps, passwd = vii[0], vii[1]
    proc = await message.reply("🔄 **Menghubungkan ke VPS...**")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ipvps, username="root", password=passwd, timeout=30)
        await run_cleardb_logic(ssh, proc, is_unpanel=False)
    except Exception as e:
        await safe_edit(proc, f"❌ **Gagal:** <code>{str(e)}</code>")
    finally:
        ssh.close()

# ==========================================
#        COMMAND: STARTWINGS / CWINGS
# ==========================================
@PY.UBOT("wings")
async def start_wings_vps(client, message):
    args = get_arg(message)
    if not args or args.count("|") < 2:
        return await message.reply("❌ **EX:** `.wings ipvps|pwvps|token`")    
    vii = args.split("|")
    ipvps, passwd, token = vii[0], vii[1], vii[2]
    proc = await message.reply("⚡ **Sedang mengonfigurasi Wings...**")    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ipvps, username="root", password=passwd, timeout=30)
        await safe_edit(proc, "⚡ **Sedang mengonfigurasi Wings...**\n<i>Menjalankan token...</i>")        
        chan = ssh.invoke_shell(term='xterm')        
        await send_and_wait(chan, token, {"Are you sure": "y", "Overwrite": "y"})
        await safe_edit(proc, "⚡ **Konfigurasi File Selesai.**\n<i>Memeriksa keamanan SSL...</i>")        
        fix_wings_ssl = ("if [ ! -f /etc/letsencrypt/live/*/fullchain.pem ]; then sed -i 's/enabled: true/enabled: false/g' /etc/pterodactyl/config.yml; fi; systemctl daemon-reload && systemctl restart wings")        
        ssh.exec_command(fix_wings_ssl)
        await safe_edit(proc, "⚡ **Konfigurasi Selesai.**\n<i>Memverifikasi status service...</i>")        
        await asyncio.sleep(5)        
        _, stdout_status, _ = ssh.exec_command("systemctl is-active wings")
        status = stdout_status.read().decode().strip()            
        if status.lower() == "active":
            await safe_edit(proc, f"✅ **Konfigurasi Berhasil!**\n\n<b>Status Wings:</b> <code>ACTIVE (Online)</code>")
        else:
            _, stdout_err, _ = ssh.exec_command("journalctl -u wings -n 5 --no-pager")
            await safe_edit(proc, f"⚠️ **Wings gagal start!**\nStatus: <code>{status.upper()}</code>\n\n<b>Log:</b>\n<code>{stdout_err.read().decode()}</code>")
    except Exception as e:
        await safe_edit(proc, f"❌ **Gagal:** <code>{str(e)}</code>")
    finally:
        ssh.close()

# ==========================================
#        COMMAND: HEALTH MONITOR & AUTO-FIX
# ==========================================
@PY.UBOT("sp")
async def check_vps_health(client, message):
    args = get_arg(message)
    if not args or "|" not in args:
        return await message.reply("❌ **Format:** `.statuspanel ipvps|pwvps`")    
    vii = args.split("|")
    ipvps, passwd = vii[0], vii[1]
    proc = await message.reply("🔍 **Menganalisis kesehatan sistem...**")    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ipvps, username="root", password=passwd, timeout=20)        
        status_results = {svc: ("🟢 Online" if ssh.exec_command(f"systemctl is-active {svc}")[1].read().decode().strip() == "active" else "🔴 Offline") for svc in ["nginx", "wings", "mariadb"]}
        _, stdout_ram, _ = ssh.exec_command("free -m | awk 'NR==2{printf \"%.2f%%\", $3*100/$2}'")
        _, stdout_cpu, _ = ssh.exec_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4\"%\"}'")
        fix_log = ""
        if "🔴 Offline" in status_results.values():
            for svc, stat in status_results.items():
                if stat == "🔴 Offline": ssh.exec_command(f"systemctl restart {svc}")
            await asyncio.sleep(3)
            fix_log = "\n\n⚠️ *Auto-Fix dijalankan pada service yang mati.*"
        teks_status = (
            f"<b>📊 VPS HEALTH REPORT</b>\n<code>----------------------</code>\n"
            f"🖥 <b>CPU Usage :</b> <code>{stdout_cpu.read().decode().strip()}</code>\n"
            f"📟 <b>RAM Usage :</b> <code>{stdout_ram.read().decode().strip()}</code>\n"
            f"<code>----------------------</code>\n🌐 <b>Nginx :</b> {status_results['nginx']}\n"
            f"🦅 <b>Wings :</b> {status_results['wings']}\n🗄 <b>DB :</b> {status_results['mariadb']}"
            f"<code>----------------------</code>{fix_log}"
        )
        await safe_edit(proc, teks_status)
    except Exception as e:
        await safe_edit(proc, f"❌ **Gagal:** <code>{str(e)}</code>")
    finally:
        ssh.close()

@PY.UBOT("settoken")
async def set_api_key(client, message):
    args = get_arg(message)
    if not args: return await message.reply("❌ **Format:** `.settoken API_KEY_PTERODACTYL`")    
    await bot_config.update_one({"_id": "panel_settings"}, {"$set": {"api_key": args}}, upsert=True)
    await message.reply("✅ **API Key berhasil disimpan ke database!**")
    
@PY.UBOT("setdo")
async def set_domain(client, message):
    args = get_arg(message)
    if not args: return await message.reply("❌ **Format:** `.setdo <https://panel.domain.com>`")    
    domain = args.rstrip('/')
    await bot_config.update_one({"_id": "panel_settings"}, {"$set": {"panel_domain": domain}}, upsert=True)
    await message.reply(f"✅ **Domain berhasil disimpan:** <code>{domain}</code>")

@PY.UBOT("port")
async def add_bulk_allocations(client, message):
    args = get_arg(message)
    if not args or args.count("|") < 3: return await message.reply("❌ <b>EX:</b> port node_Id|Ip_vps|port_start|port_end|alias")        
    config = await mongodb.bot_config.find_one({"_id": "panel_settings"})
    if not config or not config.get("api_key") or not config.get("panel_domain"): return await message.reply("❌ <b>Konfigurasi panel tidak ditemukan!</b>")        
    PANEL_URL = config["panel_domain"].rstrip('/')    
    parts = args.split("|")
    node_id, ip_vps, p_start, p_end = parts[0], parts[1], parts[2], parts[3]
    alias = parts[4] if len(parts) > 4 else "fanzy"        
    proc = await message.reply(f"🔄 <b>Sedang Diproses......</b>")    
    headers = {"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json", "Accept": "application/json"}        
    success, failed = 0, 0
    async with aiohttp.ClientSession() as session:
        for port in range(int(p_start), int(p_end) + 1):
            async with session.post(f"{PANEL_URL}/api/application/nodes/{node_id}/allocations", json={"ip": ip_vps, "alias": alias, "ports": [str(port)]}, headers=headers) as resp:
                if resp.status in [201, 204]: success += 1
                else: failed += 1
                await asyncio.sleep(0.3)
    await safe_edit(proc, f"✅ <b>Berhasil Add Port!</b>\n\n📊 <b>Hasil</b>\n  • Succes: <code>{success}</code>\n  • Gagal: <code>{failed}</code>")
    
@PY.UBOT("delport")
async def delete_bulk_allocations(client, message):
    args = get_arg(message)
    if not args: return await message.reply("❌ <b>EX:</b> delport node_Id|alias")        
    config = await mongodb.bot_config.find_one({"_id": "panel_settings"})
    if not config or not config.get("api_key") or not config.get("panel_domain"): return await message.reply("❌ <b>Konfigurasi panel tidak ditemukan!</b>")        
    parts = args.split("|")
    node_id, target_alias = parts[0], parts[1] if len(parts) > 1 else "fanzy"    
    proc = await message.reply(f"🔄 **Sedang memindai port: `{target_alias}`...**")        
    headers = {"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json", "Accept": "application/json"}        
    PANEL_URL = config["panel_domain"].rstrip('/')
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{PANEL_URL}/api/application/nodes/{node_id}/allocations?per_page=500", headers=headers) as resp:
            data = await resp.json()
            to_delete = [a for a in data.get("data", []) if a["attributes"]["alias"] == target_alias and a["attributes"]["assigned"] is False]
            if not to_delete: return await safe_edit(proc, f"ℹ️ **Tidak ditemukan port kosong alias `{target_alias}`.**")
            await safe_edit(proc, f"🗑 **Menghapus {len(to_delete)} port...**")            
            deleted = 0
            for alloc in to_delete:
                async with session.delete(f"{PANEL_URL}/api/application/nodes/{node_id}/allocations/{alloc['attributes']['id']}", headers=headers) as del_resp:
                    if del_resp.status == 204: deleted += 1
                await asyncio.sleep(0.3)
    await safe_edit(proc, f"✅ <b>Berhasil Menghapus {deleted} Port!</b>")
    
__MODULE__ = "Installer"
__HELP__ = """
<b>🚀 Pterodactyl Installer</b>
├ <code>{0}instllpnl</code> - Install Panel
├ <code>{0}unpanel</code> - Uninstall panel
├ <code>{0}wings</code> - Konfigurasi wings
├ <code>{0}cleardb</code> - cleardb panel
├ <code>{0}settoken</code> - mengatur plta
├ <code>{0}setdo</code> - mengatur domain
├ <code>{0}port</code> - add port panel
╰ <code>{0}sp</code> - Monitor & Auto-Fix
"""
