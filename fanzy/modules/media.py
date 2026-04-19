import asyncio
import os
import random
import cv2
from PIL import Image
from pyrogram.types import Message
from fanzy import *
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from pyrogram.enums import MessagesFilter, ParseMode, MessageMediaType
from pyrogram.errors import StickersetInvalid, YouBlockedUser, UsernameNotOccupied, UserNotParticipant, PeerIdInvalid
from pyrogram.raw.functions.messages import DeleteHistory, GetStickerSet
from pyrogram.raw.types import InputStickerSetShortName
from pyrogram.types import InputMediaPhoto
from fanzy import *

__MODULE__ = "Media"
__HELP__ = """
📁 <b>MEDIA TOOLS</b>

🔧 <b>Commands:</b>
├ <b><code>{0}asupan</b></code> - Random Asupan
├ <b><code>{0}cewek</b></code> - Search girl video
├ <b><code>{0}cowok</b></code> - Search boy video
├ <b><code>{0}kang</b></code> - Add sticker to pack
├ <b><code>{0}q</b></code> - Create sticker
├ <b><code>{0}tiny</b></code> - ubah stiker jadi kecil
├ <b><code>{0}toimg</b></code> - Sticker/GIF ke foto
├ <b><code>{0}tostick</b></code> - Photo to sticker
├ <b><code>{0}togif</b></code> - Sticker to GIF
├ <b><code>{0}clg</b></code> - Ambil media 1x lihat
╰ <b><code>{0}nulis</b></code> - Write on paper

"""


# ============================================
# KONFIGURASI
# ============================================
nomber_stiker = "0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 28 27 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67".split()


# ============================================
# FUNGSI HELPER
# ============================================
async def safe_delete_messages(client, chat_id, message_ids):
    try:
        if isinstance(message_ids, int):
            if message_ids > 2**31:
                return False
            message_ids = [message_ids]
        valid_ids = []
        for msg_id in message_ids:
            if isinstance(msg_id, int) and msg_id <= 2**31:
                valid_ids.append(msg_id)
        if valid_ids:
            await client.delete_messages(chat_id, valid_ids)
            return True
        return False
    except Exception:
        return False


async def get_response(client, chat_id):
    return [x async for x in client.get_chat_history(chat_id, limit=1)][0].text


def text_set(text):
    lines = []
    if len(text) <= 55:
        lines.append(text)
    else:
        all_lines = text.split("\n")
        for line in all_lines:
            if len(line) <= 55:
                lines.append(line)
            else:
                k = len(line) // 55
                for z in range(1, k + 2):
                    lines.append(line[((z - 1) * 55): (z * 55)])
    return lines[:25]
        
# ============================================
# FUNGSI RESIZE MEDIA
# ============================================
async def resize_media(media_path, is_video=False, ff_vid=False):
    """
    Resize media untuk sticker
    - Untuk gambar: resize ke 512x512
    - Untuk video: resize dengan ffmpeg (opsional)
    """
    if is_video or ff_vid:
        # Untuk video, return path asli (atau implement resize dengan ffmpeg)
        return media_path
    
    try:
        # Resize gambar dengan PIL
        img = Image.open(media_path)
        
        # Konversi ke RGB jika perlu (untuk PNG transparan)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGBA')
        else:
            img = img.convert('RGB')
        
        # Resize ke 512x512
        size = max(img.size)
        new_img = Image.new('RGBA' if img.mode == 'RGBA' else 'RGB', (512, 512), (0, 0, 0, 0))
        
        # Posisikan di tengah
        x = (512 - img.width) // 2
        y = (512 - img.height) // 2
        new_img.paste(img, (x, y))
        
        # Simpan
        new_path = media_path.replace('.', '_resized.')
        new_img.save(new_path)
        
        # Hapus file lama
        os.remove(media_path)
        
        return new_path
        
    except Exception as e:
        print(f"Resize error: {e}")
        return media_path
# ============================================
# ASPAN (Video Asupan Random)
# ============================================
@PY.UBOT("asupan")
@PY.TOP_CMD
async def video_asupan(client, message):
    prs = await EMO.PROSES(client)
    y = await message.reply_text(f"{prs}mencari video asupan...")
    try:
        asupannya = []
        async for asupan in client.search_messages("@AsupanNyaSaiki", filter=MessagesFilter.VIDEO):
            asupannya.append(asupan)
        video = random.choice(asupannya)
        await video.copy(message.chat.id, reply_to_message_id=message.id)
        await y.delete()
    except Exception as error:
        await y.edit(error)


@PY.UBOT("cewek")
@PY.TOP_CMD
async def photo_cewek(client, message):
    prs = await EMO.PROSES(client)
    y = await message.reply_text(f"{prs}mencari ayang...")
    try:
        ayangnya = []
        async for ayang in client.search_messages("@AyangSaiki", filter=MessagesFilter.PHOTO):
            ayangnya.append(ayang)
        photo = random.choice(ayangnya)
        await photo.copy(message.chat.id, reply_to_message_id=message.id)
        await y.delete()
    except Exception as error:
        await y.edit(error)


@PY.UBOT("cowok")
@PY.TOP_CMD
async def photo_cowok(client, message):
    prs = await EMO.PROSES(client)
    y = await message.reply_text(f"{prs}mencari cowok...")
    try:
        ayang2nya = []
        async for ayang2 in client.search_messages("@ayang2Saiki", filter=MessagesFilter.PHOTO):
            ayang2nya.append(ayang2)
        photo = random.choice(ayang2nya)
        await photo.copy(message.chat.id, reply_to_message_id=message.id)
        await y.delete()
    except Exception as error:
        await y.edit(error)


# ============================================
# STIKER - Q
# ============================================
@PY.UBOT("q")
@PY.TOP_CMD
async def q_sticker(client, message):
    prs = await EMO.PROSES(client)
    brhsl = await EMO.BERHASIL(client)
    ggl = await EMO.GAGAL(client)
    info = await message.reply(f"{prs}proceꜱꜱing...", quote=True)
    await client.unblock_user("@QuotLyBot")
    if message.reply_to_message:
        if len(message.command) < 2:
            msg = [message.reply_to_message]
        else:
            try:
                count = int(message.command[1])
            except Exception as error:
                await info.edit(error)
            msg = [i for i in await client.get_messages(
                chat_id=message.chat.id,
                message_ids=range(message.reply_to_message.id, message.reply_to_message.id + count),
                replies=-1,
            )]
        try:
            for x in msg:
                await x.forward("@QuotLyBot")
        except Exception:
            pass
        await asyncio.sleep(9)
        await info.delete()
        async for quotly in client.get_chat_history("@QuotLyBot", limit=1):
            if not quotly.sticker:
                await message.reply(f"@QuotLyBot {ggl}tidak dapat merespon permintaan", quote=True)
            else:
                sticker = await client.download_media(quotly)
                await message.reply_sticker(sticker, quote=True)
                os.remove(sticker)
    else:
        if len(message.command) < 2:
            return await info.edit(f"{ggl}reply to text/media")
        else:
            msg = await client.send_message("@QuotLyBot", f"/qcolor {message.command[1]}")
            await asyncio.sleep(1)
            get = await client.get_messages("@QuotLyBot", msg.id + 1)
            await info.edit(f"{brhsl}warna latar belakang kutipan disetel ke: {get.text.split(':')[1]}")
    
    user_info = await client.resolve_peer("@QuotLyBot")
    await client.invoke(DeleteHistory(peer=user_info, max_id=0, revoke=True))


# ============================================
# STIKER - KANG
# ============================================
@PY.UBOT("kang")
@PY.TOP_CMD
async def kang_sticker(client, message):
    user = message.from_user
    replied = message.reply_to_message
    
    if not replied or not replied.media:
        return await message.reply(
            "<b>❌ Format:</b> <code>kang [reply to sticker/photo/video]</code>"
        )
    
    msg = await message.reply("<b>⏳ Processing sticker...</b>")
    await client.unblock_user("stickers")
    
    # Variables
    media = None
    emoji = None
    is_anim = False
    is_video = False
    resize = False
    pack_num = 1
    
    # Get media and properties
    if replied.photo:
        resize = True
        media = await client.download_media(replied)
    elif replied.document:
        mime = replied.document.mime_type
        if "image" in mime:
            resize = True
            media = await client.download_media(replied)
        elif "tgsticker" in mime:
            is_anim = True
            media = await client.download_media(replied)
        elif "video" in mime:
            resize = True
            is_video = True
            media = await client.download_media(replied)
        else:
            return await msg.edit("<b>❌ Unsupported file type!</b>")
    elif replied.animation or replied.video:
        resize = True
        is_video = True
        media = await client.download_media(replied)
    elif replied.sticker:
        if not replied.sticker.file_name:
            return await msg.edit("<b>❌ Sticker has no name!</b>")
        emoji = replied.sticker.emoji
        is_anim = replied.sticker.is_animated
        is_video = replied.sticker.is_video
        media = await client.download_media(replied)
        if not (replied.sticker.file_name.endswith(".tgs") or replied.sticker.file_name.endswith(".webm")):
            resize = True
    else:
        return await msg.edit("<b>❌ Unsupported media type!</b>")
    
    # Get arguments
    args = message.text.split()
    if len(args) > 1:
        if args[1].isdigit():
            pack_num = int(args[1])
        else:
            emoji = args[1]
    
    if len(args) > 2:
        if args[2].isdigit():
            pack_num = int(args[2])
        else:
            emoji = args[2]
    
    if not emoji:
        emoji = "✨"
    
    # Pack name
    username = user.username or user.first_name or str(user.id)
    username = f"@{username}" if user.username else username
    pack_name = f"Sticker_{user.id}_v{pack_num}"
    pack_title = f"{username} Pack Vol.{pack_num}"
    
    if is_anim:
        pack_name += "_animated"
        pack_title += " (Animated)"
        cmd = "/newanimated"
    elif is_video:
        pack_name += "_video"
        pack_title += " (Video)"
        cmd = "/newvideo"
    else:
        cmd = "/newpack"
    
    # Check if pack exists
    exists = False
    try:
        await client.invoke(GetStickerSet(stickerset=InputStickerSetShortName(short_name=pack_name), hash=0))
        exists = True
    except:
        exists = False
    
    if exists:
        await msg.edit(f"<b>✅ Adding to existing pack...</b>\n╰ Vol.{pack_num}")
        await asyncio.sleep(1)
    else:
        # Create new pack
        await client.send_message("stickers", cmd)
        await asyncio.sleep(2)
        await client.send_message("stickers", pack_title)
        await asyncio.sleep(2)
    
    # Send sticker to BotFather
    await client.send_document("stickers", media)
    await asyncio.sleep(2)
    
    # Send emoji
    await client.send_message("stickers", emoji)
    await asyncio.sleep(2)
    
    # Publish
    if not exists:
        await client.send_message("stickers", "/publish")
        await asyncio.sleep(2)
        await client.send_message("stickers", pack_name)
        await asyncio.sleep(2)
    
    await client.send_message("stickers", "/done")
    await asyncio.sleep(1)
    
    # Cleanup
    if media and os.path.exists(media):
        os.remove(media)
    
    # Delete messages from BotFather
    async for m in client.get_chat_history("stickers", limit=5):
        await client.delete_messages("stickers", m.id)
    
    await msg.edit(
        f"<b>✅ Sticker Added!</b>\n\n"
        f"<b>📦 Pack:</b> Vol.{pack_num}\n"
        f"<b>🔗 Link:</b> <a href='https://t.me/addstickers/{pack_name}'>Click Here</a>\n"
        "<b>⚡ Power By Fanzy Userbot</b>"
    )


# ============================================
# STIKER - TINY
# ============================================
@PY.UBOT("tiny")
@PY.TOP_CMD
async def tiny_sticker(client, message):
    reply = message.reply_to_message
    if not (reply and (reply.media)):
        return await message.reply("silahkan balas ke pesan sticker!")
    Tm = await message.reply("processing...")
    ik = await client.download_media(reply)
    im1 = Image.open("storage/TM_BLACK.png")
    
    if ik.endswith(".tgs"):
        await client.download_media(reply, "Tm.tgs")
        await bash("lottie_convert.py man.tgs json.json")
        json = open("json.json", "r")
        jsn = json.read()
        jsn = jsn.replace("512", "2000")
        open("json.json", "w").write(jsn)
        await bash("lottie_convert.py json.json Tm.tgs")
        file = "man.tgs"
        os.remove("json.json")
    elif ik.endswith((".gif", ".mp4")):
        iik = cv2.VideoCapture(ik)
        busy = iik.read()
        cv2.imwrite("i.png", busy)
        fil = "i.png"
        im = Image.open(fil)
        z, d = im.size
        if z == d:
            xxx, yyy = 200, 200
        else:
            t = z + d
            a = z / t
            b = d / t
            aa = (a * 100) - 50
            bb = (b * 100) - 50
            xxx = 200 + 5 * aa
            yyy = 200 + 5 * bb
        k = im.resize((int(xxx), int(yyy)))
        k.save("k.png", format="PNG", optimize=True)
        im2 = Image.open("k.png")
        back_im = im1.copy()
        back_im.paste(im2, (150, 0))
        back_im.save("o.webp", "WEBP", quality=95)
        file = "o.webp"
        os.remove(fil)
        os.remove("k.png")
    else:
        im = Image.open(ik)
        z, d = im.size
        if z == d:
            xxx, yyy = 200, 200
        else:
            t = z + d
            a = z / t
            b = d / t
            aa = (a * 100) - 50
            bb = (b * 100) - 50
            xxx = 200 + 5 * aa
            yyy = 200 + 5 * bb
        k = im.resize((int(xxx), int(yyy)))
        k.save("k.png", format="PNG", optimize=True)
        im2 = Image.open("k.png")
        back_im = im1.copy()
        back_im.paste(im2, (150, 0))
        back_im.save("o.webp", "WEBP", quality=95)
        file = "o.webp"
        os.remove("k.png")
    
    await asyncio.gather(
        Tm.delete(),
        client.send_sticker(message.chat.id, sticker=file, reply_to_message_id=message.id),
    )
    os.remove(file)
    os.remove(ik)


# ============================================
# STIKER - MMF
# ============================================
@PY.UBOT("mmf")
@PY.TOP_CMD
async def mmf_sticker(client, message):
    if not message.reply_to_message:
        return await message.reply("balas ke pesan foto atau sticker!")
    reply_message = message.reply_to_message
    if not reply_message.media:
        return await message.reply("balas ke pesan foto atau sticker")
    file = await client.download_media(reply_message)
    Tm = await message.reply("processing...")
    text = get_arg(message)
    if len(text) < 1:
        return await Tm.edit(f"harap ketik: mmf - [text]")
    meme = await add_text_img(file, text)
    await asyncio.gather(
        Tm.delete(),
        client.send_sticker(message.chat.id, sticker=meme, reply_to_message_id=message.id),
    )
    os.remove(meme)


# ============================================
# CONVERT - TOIMG
# ============================================
@PY.UBOT("toimg")
@PY.TOP_CMD
async def toimg_cmd(client, message):
    prs = await EMO.PROSES(client)
    _msg = f"{prs}proceꜱꜱing..."
    Tm = await message.reply(_msg)
    try:
        file_io = await dl_pic(client, message.reply_to_message)
        file_io.name = "sticker.png"
        await client.send_photo(message.chat.id, file_io, reply_to_message_id=message.id)
        await Tm.delete()
    except Exception as e:
        await Tm.delete()
        return await client.send_message(message.chat.id, e, reply_to_message_id=message.id)


# ============================================
# CONVERT - TOSTICKER
# ============================================
@PY.UBOT("tostick")
@PY.TOP_CMD
async def tosticker_cmd(client, message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply_text("reply ke foto untuk mengubah ke sticker")
    sticker = await client.download_media(message.reply_to_message.photo.file_id, f"sticker_{message.from_user.id}.webp")
    await message.reply_sticker(sticker)
    os.remove(sticker)


# ============================================
# CONVERT - TOGIF
# ============================================
@PY.UBOT("togif")
@PY.TOP_CMD
async def togif_cmd(client, message):
    prs = await EMO.PROSES(client)
    ggl = await EMO.GAGAL(client)
    TM = await message.reply(f"{prs}proceꜱꜱing...")
    if not message.reply_to_message.sticker:
        return await TM.edit(f"{ggl}balas ke stiker...")
    await TM.edit(f"{prs}downloading sticker. . .")
    file = await client.download_media(message.reply_to_message, f"Gift_{message.from_user.id}.mp4")
    try:
        await client.send_animation(message.chat.id, file, reply_to_message_id=message.id)
        os.remove(file)
        await TM.delete()
    except Exception as error:
        await TM.edit(error)


# ============================================
# CONVERT - TOANIME
# ============================================
@PY.UBOT("toanime")
@PY.TOP_CMD
async def toanime_cmd(client, message):
    prs = await EMO.PROSES(client)
    brhsl = await EMO.BERHASIL(client)
    ggl = await EMO.GAGAL(client)
    Tm = await message.reply(f"{prs}tunggu sebentar...")
    
    if message.reply_to_message:
        if len(message.command) < 2:
            if message.reply_to_message.photo:
                file = "foto"
                get_photo = message.reply_to_message.photo.file_id
            elif message.reply_to_message.sticker:
                file = "sticker"
                get_photo = await dl_pic(client, message.reply_to_message)
            elif message.reply_to_message.animation:
                file = "gift"
                get_photo = await dl_pic(client, message.reply_to_message)
            else:
                return await Tm.edit(f"{ggl}mohon balas ke photo/striker/git")
        else:
            if message.command[1] in ["foto", "profil", "photo"]:
                chat = message.reply_to_message.from_user or message.reply_to_message.sender_chat
                file = "foto profil"
                get = await client.get_chat(chat.id)
                photo = get.photo.big_file_id
                get_photo = await dl_pic(client, photo)
    else:
        if len(message.command) < 2:
            return await Tm.edit(f"{ggl}balas ke foto dan saya akan merubah foto anda menjadi anime")
        else:
            try:
                file = "foto"
                get = await client.get_chat(message.command[1])
                photo = get.photo.big_file_id
                get_photo = await dl_pic(client, photo)
            except Exception as error:
                return await Tm.edit(error)
    
    await Tm.edit("proceꜱꜱing...")
    await client.unblock_user("@qq_neural_anime_bot")
    send_photo = await client.send_photo("@qq_neural_anime_bot", get_photo)
    await asyncio.sleep(30)
    await send_photo.delete()
    await Tm.delete()
    info = await client.resolve_peer("@qq_neural_anime_bot")
    anime_photo = []
    async for anime in client.search_messages("@qq_neural_anime_bot", filter=MessagesFilter.PHOTO):
        anime_photo.append(InputMediaPhoto(anime.photo.file_id, caption=f"{brhsl}powered by: {bot.me.mention}"))
    
    if anime_photo:
        await client.send_media_group(message.chat.id, anime_photo, reply_to_message_id=message.id)
        return await client.invoke(DeleteHistory(peer=info, max_id=0, revoke=True))
    else:
        await client.send_message(message.chat.id, f"{ggl}gagal merubah {file} menjadi gambar anime", reply_to_message_id=message.id)
        return await client.invoke(DeleteHistory(peer=info, max_id=0, revoke=True))


# ============================================
# COLONG MEDIA
# ============================================
@PY.UBOT("clg")
@PY.TOP_CMD
async def colong_media(client, message):
    prs = await EMO.PROSES(client)
    ggl = await EMO.GAGAL(client)
    ktrng = await EMO.BL_KETERANGAN(client)
    dia = message.reply_to_message
    if not dia:
        return await message.reply(f"{ggl}mohon balas ke media")
    anjing = dia.caption or ""
    Tm = await message.reply(f"{prs}processing...")
    
    if dia.photo:
        if message.reply_to_message.photo.file_size > 10000000:
            return await Tm.edit(f"{ktrng}file di atas 10mb tidak di izinkan")
        anu = await client.download_media(dia)
        await client.send_photo(client.me.id, anu, anjing)
        os.remove(anu)
        await message.delete()
        return await Tm.delete()
    if dia.video:
        if message.reply_to_message.video.file_size > 10000000:
            return await Tm.edit(f"{ktrng}file di atas 10mb tidak di izinkan")
        anu = await client.download_media(dia)
        await client.send_video(client.me.id, anu, anjing)
        os.remove(anu)
        await message.delete()
        return await Tm.delete()
    if dia.audio:
        if message.reply_to_message.audio.file_size > 10000000:
            return await Tm.edit(f"{ktrng}file di atas 10mb tidak di izinkan")
        anu = await client.download_media(dia)
        await client.send_audio(client.me.id, anu, anjing)
        os.remove(anu)
        await message.delete()
        return await Tm.delete()
    if dia.voice:
        if message.reply_to_message.voice.file_size > 10000000:
            return await Tm.edit(f"{ktrng}file di atas 10mb tidak di izinkan")
        anu = await client.download_media(dia)
        await client.send_voice(client.me.id, anu, anjing)
        os.remove(anu)
        await message.delete()
        return await Tm.delete()
    if dia.document:
        if message.reply_to_message.document.file_size > 10000000:
            return await Tm.edit(f"{ktrng}file di atas 10mb tidak di izinkan")
        anu = await client.download_media(dia)
        await client.send_document(client.me.id, anu, anjing)
        os.remove(anu)
        await message.delete()
        return await Tm.delete()
    else:
        return await Tm.reply(f"{ggl}sepertinya terjadi kesalahan")


# ============================================
# NULIS
# ============================================
@PY.UBOT("nulis")
@PY.TOP_CMD
async def nulis_cmd(client, message):
    if message.reply_to_message:
        reply = message.reply_to_message
        if reply.text or reply.caption:
            text = reply.text or reply.caption
        else:
            return await message.reply("replay ke teks atau caption media")
    else:
        if len(message.command) < 2:
            return await message.reply(f"<code>{message.text}</code> [ʀᴇᴘʟʏ/ᴛᴇxᴛ]")
        else:
            text = message.text.split(None, 1)[1]
    try:
        img = Image.open("storage/template.jpg")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("storage/assfont.ttf", 30)
        x, y = 150, 140
        lines = text_set(text)
        line_height = font.getsize("hg")[1]
        for line in lines:
            draw.text((x, y), line, fill=(1, 22, 55), font=font)
            y = y + line_height - 5
        file = "ult.jpg"
        img.save(file)
        await message.reply_photo(photo=file)
        os.remove(file)
    except Exception as error:
        return await message.reply(error)