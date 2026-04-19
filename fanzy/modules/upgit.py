from fanzy import *
import os
import requests
import base64
import json
import zipfile
import tempfile
import time
from datetime import datetime
from pyrogram import *
from pyrogram.types import *
import io

__MODULE__ = "github"
__HELP__ = """
<b>🗂 TOOLS GITHUB</b>
├ <code>{0}setkey</code> - set token
├ <code>{0}setusr</code> - set username
├ <code>{0}upgit</code> - upload file ke github
├ <code>{0}cd</code> - melihat data github
├ <code>{0}algit</code> - lihat all data github
├ <code>{0}delgit</code> - delete repository
├ <code>{0}gits</code> -  lihat daftar repository
├ <code>{0}gitcek</code> - cek token & limit
├ <code>{0}rm</code> - delete token github
├ <code>{0}rmusr</code> - delete username
├ <code>{0}clear</code> delete all data github
├ <code>{0}src</code> - mencari code digithub
╰ <code>{0}sr</code> - mencari repository
"""

CONFIG_FILE = "github_config.json"
CONFIRM_TIMEOUT = 320

# Helper untuk mengambil data dari MongoDB
async def get_github_config(user_id):
    token = await get_vars(user_id, "GIT_TOKEN")
    username = await get_vars(user_id, "GIT_USERNAME")
    return token, username

# Helper Header GitHub
def get_headers(token):
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

# Helper untuk mendapatkan Branch utama secara dinamis
def get_default_branch(username, repo, headers):
    url = f"https://api.github.com/repos/{username}/{repo}"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json().get("default_branch", "main")
    return "main"

def check_rate_limit(headers):
    remaining = int(headers.get('x-ratelimit-remaining', 5000))
    reset_time = int(headers.get('x-ratelimit-reset', 0))
    return remaining, reset_time

# ==================== PERINTAH SET DATA ====================

@PY.UBOT("setkey")
async def set_token(client, message):
    args = get_arg(message)
    if not args and message.reply_to_message:
        args = message.reply_to_message.text
        
    if not args:
        return await message.reply("❌ **Gunakan:** `.setkey ghp_xxxxx` atau reply ke token.")
    
    await set_vars(client.me.id, "GIT_TOKEN", args)
    await message.reply("✅ **Token berhasil disimpan ke Database!**")

@PY.UBOT("setusr")
async def set_username(client, message):
    args = get_arg(message)
    if not args and message.reply_to_message:
        args = message.reply_to_message.text

    if not args:
        return await message.reply("❌ **Gunakan:** `.setusr [username]` atau reply ke username.")
    
    await set_vars(client.me.id, "GIT_USERNAME", args)
    await message.reply(f"✅ **Username disimpan:** `{args}`")

# ==================== PERINTAH HAPUS DATA ====================

# ==================== PERINTAH HAPUS DATA ====================

@PY.UBOT("rm")
async def remove_token(client, message):
    await set_vars(client.me.id, "GIT_TOKEN", "")
    await message.reply("✅ **Success Delete Token dari Database!**")

@PY.UBOT("rmusr")
async def remove_username(client, message):
    await set_vars(client.me.id, "GIT_USERNAME", "")
    await message.reply("✅ **Success Delete User dari Database!**")

@PY.UBOT("clear")
async def clear_all_data(client, message):
    await set_vars(client.me.id, "GIT_TOKEN", "")
    await set_vars(client.me.id, "GIT_USERNAME", "")
    await message.reply("✅ **Semua data GitHub di Database berhasil dihapus!**")

# ==================== PERINTAH CEK ====================

@PY.UBOT("gitcek")
async def check_github(client, message):
    token, username = await get_github_config(client.me.id)
    if not token or not username:
        return await message.reply("❌ **Token/Username belum diatur di database!**")
    
    processing = await message.reply("🔄 **Mengecek koneksi GitHub...**")
    try:
        headers = get_headers(token)
        user_resp = requests.get("https://api.github.com/user", headers=headers)
        if user_resp.status_code != 200:
            return await processing.edit("❌ **Token tidak valid atau expired!**")
        
        user_data = user_resp.json()
        await processing.edit(f"✅ **Terhubung sebagai:** `{user_data.get('login')}`")
    except Exception as e:
        await processing.edit(f"❌ **Error:** `{e}`")


# ==================== PERINTAH LIST ====================

@PY.UBOT("gits")
@PY.TOP_CMD
async def list_repos(client, message):
    # Mengambil data dari Database (MongoDB)
    token, username = await get_github_config(client.me.id)
    
    if not token or not username:
        await message.reply("❌ **Token/username belum diset di database!**")
        return
    
    processing = await message.reply("🔄 **Mengambil daftar repository...**")
    
    try:
        # Menambahkan per_page=20 agar hasil konsisten
        url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=20"
        headers = get_headers(token)
        
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            error_msg = response.json().get('message', 'Error')
            await processing.edit_text(f"❌ **Gagal:** {error_msg}")
            return
        
        repos = response.json()
        
        if not repos:
            await processing.edit_text("📭 **Akun ini tidak memiliki repository.**")
            return
        
        remaining, _ = check_rate_limit(response.headers)
        
        msg = f"📦 **DAFTAR REPOSITORY**\n"
        msg += f"━━━━━━━━━━━━━━━━━━━\n"
        msg += f"👤 **User:** `{username}`\n"
        msg += f"⏳ **Limit:** `{remaining}`\n"
        msg += f"📊 **Total Repo:** `{len(repos)}`\n"
        msg += f"━━━━━━━━━━━━━━━━━━━\n\n"
        
        repo_list = []
        for i, repo in enumerate(repos, 1):
            name = repo['name']
            is_private = repo['private']
            stars = repo['stargazers_count']
            lang = repo['language'] or "Misc"
            link = repo['html_url']
            
            mode_icon = "🔒" if is_private else "🌐"
            
            # Format baris repo yang lebih informatif
            item = (
                f"{i}. {mode_icon} **{name}**\n"
                f"   ├ ⭐ `{stars}` stars\n"
                f"   ├ 🏷 `{lang}`\n"
                f"   ╰ 🔗 **Link Repo:** [Click Here]({link})"
            )
            repo_list.append(item)
        
        msg += "\n\n".join(repo_list)
        
        # Jika repo sangat banyak
        if len(repos) >= 20:
            msg += f"\n\n━━━━━━━━━━━━━━━━━━━\n"
            msg += f"*Menampilkan 20 repository New.*"
        
        # disable_web_page_preview=True penting agar tidak muncul kotak link besar
        await processing.edit_text(msg, disable_web_page_preview=True)
        
    except Exception as e:
        await processing.edit_text(f"❌ **Error:** `{str(e)}`")


# ==================== PERINTAH DELETE REPO ====================

@PY.UBOT("delgit")
@PY.TOP_CMD
async def delete_repo(client, message):
    """Hapus repository dari GitHub LANGSUNG tanpa konfirmasi"""
    # PERBAIKAN: Mengambil data dari Database (MongoDB)
    token, username = await get_github_config(client.me.id)
    
    if not token or not username:
        await message.reply("❌ **Token/username belum diset di database!**")
        return
    
    if len(message.command) < 2:
        await message.reply(
            "❌ **Masukkan nama repository!**\n\n"
            "Contoh: `.delgit repo-name`"
        )
        return
    
    repo_name = message.command[1]
    
    processing = await message.reply(f"🔄 **Menghapus `{repo_name}`...**")
    
    try:
        url = f"https://api.github.com/repos/{username}/{repo_name}"
        headers = get_headers(token)
        
        response = requests.delete(url, headers=headers)
        
        if response.status_code == 204:
            await processing.edit_text(
                f"✅ **Succes Delete Repository**\n\n"
                f"📦 `{username}/{repo_name}` telah dihapus."
            )
        elif response.status_code == 403:
            if response.headers.get('x-ratelimit-remaining') == '0':
                remaining, reset_time = check_rate_limit(response.headers)
                wait_time = reset_time - int(time.time())
                minutes = wait_time // 60
                await processing.edit_text(
                    f"⏳ **Rate limit tercapai!**\n\n"
                    f"Harap tunggu {minutes} menit untuk reset."
                )
            else:
                await processing.edit_text(
                    "❌ **Tidak punya izin!** Pastikan token memiliki scope 'delete_repo'"
                )
        elif response.status_code == 404:
            await processing.edit_text("❌ **Repository tidak ditemukan!**")
        else:
            await processing.edit_text(f"❌ **Gagal:** {response.json().get('message', 'Error')}")
            
    except Exception as e:
        await processing.edit_text(f"❌ **Error:** `{str(e)}`")


@PY.UBOT("cd|algit")
@PY.TOP_CMD
async def show_github_data(client, message):
    token, username = await get_github_config(client.me.id)
    if not token and not username:
        return await message.reply("📭 **Data GitHub tidak ditemukan di Database.**")
    
    processing = await message.reply("🔄 **Sinkronisasi data GitHub...**")
    hidden_token = f"<code>{token[:4]}</code>****<code>{token[-4:]}</code>" if token and len(token) > 8 else "<code>Belum diatur</code>"
    profile_info = "❌ Gagal memuat detail profil"
    stats_info = ""
    
    try:
        headers = get_headers(token) if token else {}
        user_resp = requests.get("https://api.github.com/user", headers=headers)
        if user_resp.status_code == 200:
            user_data = user_resp.json()
            profile_info = f"👤 **Nama:** `{user_data.get('name') or 'No Name'}`\n📝 **Bio:** `{user_data.get('bio') or '-'}`"
            stats_info = (f"📊 **Statistik:**\n"
                          f"   ├ 📦 Repo: `{user_data.get('public_repos', 0)}`\n"
                          f"   ├ 👥 Followers: `{user_data.get('followers', 0)}`\n"
                          f"   └ 🤝 Following: `{user_data.get('following', 0)}`")
        else:
            profile_info = "⚠️ **Profil:** (Token tidak valid/terbatas)"
    except Exception:
        profile_info = "⚠️ **Profil:** (Gagal terhubung ke API)"

    msg = (f"<b>───「 CONFIG GITHUB 」───</b>\n\n"
           f"👤 **Username:** <code>{username or 'Tidak ada'}</code>\n"
           f"🔑 **Token:** {hidden_token}\n\n"
           f"<b>───「 PROFILE INFO 」───</b>\n{profile_info}\n\n"
           f"{stats_info}\n\n"
           f"📍 **Database:** <code>MongoDB Connected</code>\n"
           f"📅 **Dicek pada:** <code>{datetime.now().strftime('%H:%M:%S')}</code>")
    await processing.edit_text(msg)


@PY.UBOT("sr")
@PY.TOP_CMD
async def github_search(client, message):
    """Mencari repository di GitHub"""
    token, username = await get_github_config(client.me.id)
    
    if not token or not username:
        await message.reply("❌ **Token/username belum diset di database!**")
        return
    
    if len(message.command) < 2:
        await message.reply(
            "❌ **Masukkan kata kunci pencarian!**\n\n"
            "**Format:** `.sr [query]`\n"
            "**Contoh:** `.sr userbot pyrogram`"
        )
        return
    
    query = " ".join(message.command[1:])
    processing = await message.reply(f"🔍 **Mencari `{query}`...**")
    
    try:
        headers = get_headers(token)
        url = "https://api.github.com/search/repositories"
        params = {"q": query, "sort": "stars", "order": "desc", "per_page": 10}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            error_text = response.json().get('message', 'Error')
            await processing.edit_text(f"❌ **Gagal:** {error_text}")
            return
        
        data = response.json()
        total = data.get('total_count', 0)
        items = data.get('items', [])
        
        if not items:
            await processing.edit_text(f"📭 **Tidak ada hasil untuk:** `{query}`")
            return
        
        remaining, _ = check_rate_limit(response.headers)
        
        msg = f"🔍 **GITHUB SEARCH RESULTS**\n"
        msg += f"━━━━━━━━━━━━━━━━━━━\n"
        msg += f"📌 **Query:** `{query}`\n"
        msg += f"📊 **Total:** `{total}`\n"
        msg += f"⏳ **Limit:** `{remaining}`\n"
        msg += f"━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, repo in enumerate(items[:10], 1):
            name = repo['full_name']
            stars = repo['stargazers_count']
            forks = repo['forks_count']
            desc = repo['description'] or "No description"
            link = repo['html_url']
            
            # Membatasi panjang deskripsi agar rapi
            if len(desc) > 60:
                desc = desc[:60] + "..."
            
            msg += f"{i}. **{name}** ⭐{stars} 🍴{forks}\n"
            msg += f"   📝 `{desc}`\n"
            msg += f"   🔗 **Link Repo:** [Click Here]({link})\n\n"        
        if total > 10:
            msg += f"━━━━━━━━━━━━━━━━━━━\n"
            msg += f"💡 **Total 10 dari {total} hasil.**\n"
            msg += f"💡`.srcrepo [nama]` *untuk detail.*"
        
        await processing.edit_text(msg, disable_web_page_preview=True)
        
    except Exception as e:
        await processing.edit_text(f"❌ **Error:** `{str(e)}`")

@PY.UBOT("src")
@PY.TOP_CMD
async def github_search_code(client, message):
    """Mencari potongan kode di GitHub"""
    token, username = await get_github_config(client.me.id)
    
    if not token or not username:
        await message.reply("❌ **Token/username belum diset di database!**")
        return
    
    if len(message.command) < 2:
        await message.reply(
            "❌ **Masukkan kata kunci!**\n"
            "**Gunakan:** `.src [query]`\n"
            "**Contoh:** `.src import pyrogram`"
        )
        return
    
    query = " ".join(message.command[1:])
    processing = await message.reply(f"🔍 **Mencari kode untuk:** `{query}`...")
    
    try:
        headers = get_headers(token)
        url = "https://api.github.com/search/code"
        # Kita batasi 5-7 hasil saja agar chat tidak terlalu panjang
        params = {"q": query, "per_page": 7}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            error_msg = response.json().get('message', 'Error')
            await processing.edit_text(f"❌ **GitHub Error:** `{error_msg}`")
            return
        
        data = response.json()
        total = data.get('total_count', 0)
        items = data.get('items', [])
        
        if not items:
            await processing.edit_text(f"📭 **Kode tidak ditemukan untuk:** `{query}`")
            return
        
        remaining, _ = check_rate_limit(response.headers)
        
        msg = f"💻 **GITHUB CODE SEARCH**\n"
        msg += f"━━━━━━━━━━━━━━━━━━━\n"
        msg += f"🔍 **Query:** `{query}`\n"
        msg += f"📊 **Ditemukan:** `{total}`\n"
        msg += f"⏳ **Limit:** `{remaining}`\n"
        msg += f"━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, item in enumerate(items, 1):
            file_name = item['name']
            repo_full = item['repository']['full_name']
            file_path = item['path']
            code_url = item['html_url']
            
            # Mempersingkat path jika terlalu panjang agar tidak merusak UX
            if len(file_path) > 40:
                display_path = "..." + file_path[-37:]
            else:
                display_path = file_path

            msg += f"{i}. 📄 **{file_name}**\n"
            msg += f"   ├ 📦 `{repo_full}`\n"
            msg += f"   ├ 📂 **Path:** `{display_path}`\n"
            msg += f"   └ 🔗 **Link:** [View Code]({code_url})\n\n"
        
        if total > 7:
            msg += f"━━━━━━━━━━━━━━━━━━━\n"
            msg += f"**Menampilkan 7 hasil teratas.**"
        
        await processing.edit_text(msg, disable_web_page_preview=True)
        
    except Exception as e:
        await processing.edit_text(f"❌ **Error:** `{str(e)}`")
            
@PY.UBOT("upgit")
@PY.TOP_CMD
async def upload_file(client, message):
    # Mengambil data dari Database (MongoDB)
    token = await get_vars(client.me.id, "GIT_TOKEN")
    username = await get_vars(client.me.id, "GIT_USERNAME")
    
    if not token or not username:
        await message.reply("❌ **Token/username belum diset di database!**")
        return
    
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply("❌ **Reply ke file yang mau diupload!**")
        return

    if message.reply_to_message.document.file_size > 25 * 1024 * 1024:
        await message.reply("❌ **File terlalu besar!** Maksimal 25MB.")
        return
    
    if len(message.command) < 2:
        await message.reply(
            "❌ **Format Salah!**\n"
            "**Gunakan:** `.upgit [nama_repo] [mode] [pesan]`\n"
            "**Contoh:** `.upgit MyProject /public Update v1`"
        )
        return
    
    repo_name = message.command[1]
    is_private = False
    commit_msg_start = 2
    
    if len(message.command) >= 3 and message.command[2].startswith('/'):
        mode = message.command[2].lower()
        is_private = True if mode == '/private' else False
        commit_msg_start = 3
    
    commit_msg = " ".join(message.command[commit_msg_start:]) if len(message.command) > commit_msg_start else "Upload via Userbot"
    
    mode_text = "🔒 Private" if is_private else "🌐 Public"
    processing = await message.reply("⚡ **Mempersiapkan pengunggahan...**")
    
    file = None 
    try:
        file = await message.reply_to_message.download()
        file_name = message.reply_to_message.document.file_name
        
        with open(file, 'rb') as f:
            file_content = f.read()
        
        headers = get_headers(token)
        repo_url = f"https://api.github.com/repos/{username}/{repo_name}"
        check_repo = requests.get(repo_url, headers=headers)
        
        if check_repo.status_code == 404:
            await processing.edit_text(f"🛠 **Membuat repository baru:** `{repo_name}`...")
            create_url = "https://api.github.com/user/repos"
            data = {"name": repo_name, "private": is_private, "auto_init": False}
            requests.post(create_url, headers=headers, json=data)
        
        branch_name = get_default_branch(username, repo_name, headers)
        
        # --- LOGIKA ZIP DENGAN LIVE PROGRESS ---
        if file_name.endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(file_content)) as zip_file:
                file_list = [f for f in zip_file.namelist() if not f.endswith('/')]
                total_files = len(file_list)
                success_count, fail_count = 0, 0
                results = []
                
                for index, file_path in enumerate(file_list, 1):
                    # Update Progress Bar setiap file
                    percent = index * 100 // total_files
                    progress = "▰" * (percent // 10) + "▱" * (10 - (percent // 10))
                    await processing.edit_text(
                        f"📤 **Proses Unggah ZIP**\n"
                        f"📦 **Repo:** `{repo_name}`\n"
                        f"📂 **File:** `{file_path}`\n"
                        f"📊 **Progress:** `{progress}` {percent}%\n"
                        f"⏳ **Status:** `{index}/{total_files}` file"
                    )

                    with zip_file.open(file_path) as f:
                        content = f.read()
                    
                    upload_url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{file_path}"
                    encoded = base64.b64encode(content).decode('utf-8')
                    
                    check_f = requests.get(upload_url, headers=headers)
                    sha_f = check_f.json().get('sha') if check_f.status_code == 200 else None
                    
                    upload_data = {"message": f"{commit_msg} - {file_path}", "content": encoded, "branch": branch_name}
                    if sha_f: upload_data["sha"] = sha_f
                    
                    upload_resp = requests.put(upload_url, headers=headers, json=upload_data)
                    if upload_resp.status_code in [200, 201]:
                        success_count += 1
                        results.append(f"✅ `{file_path}`")
                    else:
                        fail_count += 1
                        results.append(f"❌ `{file_path}`")
                    
                    # Delay kecil agar tidak spamming API berlebihan
                    time.sleep(2.0)

                test_resp = requests.get("https://api.github.com/rate_limit", headers=headers)
                remaining, _ = check_rate_limit(test_resp.headers)
                
                # TAMPILAN AKHIR ZIP PROFESSIONAL
                report = (
                    f"✨ **GitHub Upload Success!**\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"📝 **Name:** `{repo_name}`\n"
                    f"🔐 **Mode:** `{mode_text}`\n"
                    f"📊 **Statistik:**\n"
                    f"   • Total: `{total_files}` file\n"
                    f"   • Berhasil: `{success_count}`\n"
                    f"   • Gagal: `{fail_count}`\n"
                    f"⏳ **Sisa Limit:** `{remaining}`\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🔗 **Link Repo Anda:**: [click hare](https://github.com/{username}/{repo_name})"
                )                
                await processing.edit_text(report, disable_web_page_preview=True)
            
        # --- LOGIKA SINGLE FILE ---
        else:
            await processing.edit_text(f"📤 **Mengunggah file tunggal:** `{file_name}`...")
            upload_url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{file_name}"
            encoded = base64.b64encode(file_content).decode('utf-8')
            
            check_file = requests.get(upload_url, headers=headers)
            sha = check_file.json().get('sha') if check_file.status_code == 200 else None
            
            upload_data = {"message": commit_msg, "content": encoded, "branch": branch_name}
            if sha: upload_data["sha"] = sha
            
            upload_resp = requests.put(upload_url, headers=headers, json=upload_data)
            
            if upload_resp.status_code in [200, 201]:
                remaining, _ = check_rate_limit(upload_resp.headers)
                res_text = (
                    f"✨ **File Upload Success!**\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"📄 **File:** `{file_name}`\n"
                    f"📝 **Repo:** `{username}/{repo_name}`\n"
                    f"🔐 **Mode:** `{mode_text}`\n"
                    f"⏳ **Sisa Limit:** `{remaining}`\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🔗 **Link Repo Anda:** [Click Hare](https://github.com/{username}/{repo_name}/blob/{branch_name}/{file_name})"
                )
                await processing.edit_text(res_text, disable_web_page_preview=True)
            else:
                await processing.edit_text(f"❌ **Gagal Upload:** `{upload_resp.json().get('message', 'Error')}`")    
    except Exception as e:
        await processing.edit_text(f"❌ **Error Terjadi:**\n`{str(e)}`")
    finally:
        if file and os.path.exists(file):
            os.remove(file)