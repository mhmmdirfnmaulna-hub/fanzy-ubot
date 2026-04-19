import os
import zipfile
from datetime import datetime
from fanzy import PY

__MODULE__ = "backup"
__HELP__ = """
<b>📂 BACKUP TOOLS</b>
├ <code>{0}bckup</code> - Backup all file bot
╰ <b>Status:</b> Khusus Owner
"""

OWNER_ID = 1322982688  # ID Owner
UBOT_DIR = "/root/fanzy/fanzy"  # Folder yang mau di-backup

@PY.UBOT("bckup")
async def backup_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("<b>❌ Akses Ditolak:</b> Khusus Owner!")    
    msg = await message.reply("<b>⏳ Prosess Backup.....")    
    if not os.path.exists(UBOT_DIR):
        return await msg.edit(f"<b>❌ Gagal:</b>\n<code>Path {UBOT_DIR} tidak ditemukan!</code>")    
    total_files = 0
    total_size = 0    
    for foldername, subfolders, filenames in os.walk(UBOT_DIR):
        for filename in filenames:
            file_path = os.path.join(foldername, filename)
            total_files += 1
            total_size += os.path.getsize(file_path)    
    if total_files == 0:
        return await msg.edit("<b>❌ Gagal:</b>\n<code>Tidak ada file untuk di-backup!</code>")    
    await msg.edit("<b>📦 Compressing...")
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    display_time = now.strftime("%d/%m/%Y %H:%M")
    zip_name = f"fanzy_backup.zip"
    zip_path = os.path.join("/tmp", zip_name)    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
            for foldername, subfolders, filenames in os.walk(UBOT_DIR):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    if filename.endswith(('.pyc', '.log', '.session')):
                        continue
                    try:
                        arcname = os.path.relpath(file_path, UBOT_DIR)
                        backup_zip.write(file_path, arcname)
                    except Exception as e:
                        print(f"Error adding {file_path}: {e}")        
        zip_size = os.path.getsize(zip_path)
        size_mb = zip_size / 1024 / 1024        
        if zip_size < 1000:
            return await msg.edit("<b>❌ Gagal:</b>\n<code>Ukuran backup terlalu kecil/kosong.</code>")        
        caption = f"""
<b>✅ SUCCESFULLY BACKUP FILE</b>

<b>📂 Files:</b> <code>{total_files} items</code>
<b>💾 Size:</b> <code>{size_mb:.2f} MB</code>
<b>📅 Date:</b> <code>{display_time}</code>
"""        
        await client.send_document(
            chat_id=OWNER_ID,
            document=zip_path,
            caption=caption
        )        
        await msg.edit(f"<b>✅ Succesfully Backup File!</b>\nSilakan cek pesan tersimpan.")
    except Exception as e:
        await msg.edit(f"<b>❌ Error:</b>\n<code>{str(e)}</code>")
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)
