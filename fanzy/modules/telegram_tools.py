import asyncio
import os
from gc import get_objects
import gtts
from gpytranslate import Translator
from pykeyboard import InlineKeyboard
from pyrogram import Client, filters
from pyrogram.enums import ChatType, ChatMemberStatus, UserStatus
from pyrogram.errors import (
    UsernameNotOccupied,
    UserNotParticipant,
    PeerIdInvalid
)
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors.exceptions.not_acceptable_406 import ChannelPrivate
from pyrogram.types import Message
from fanzy import *
from fanzy.core.helpers.tools import get_data_id

__MODULE__ = "Telegram Tools"
__HELP__ = """
📁 <b>TELEGRAM TOOLS</b>
├ <code>{0}arch</code> - Archive chats
├ <code>{0}unarch</code> - Unarchive chats
├ <code>{0}creat</code> - Create group/ch
├ <code>{0}creatbot</code> - Create bot tele
├ <code>{0}invit</code> - Invit user ke group
├ <code>{0}join</code> - Join chat by link
├ <code>{0}kickme</code> - Keluar dari group
├ <code>{0}leaveallgc</code> - Out all group
├ <code>{0}leaveallch</code> - Out all ch
├ <code>{0}outmute</code> - out all gb mute
├ <code>{0}clone</code> - Clone user profile
├ <code>{0}getpp</code> - Get profile picture
├ <code>{0}tr</code> - Translate text
├ <code>{0}tts</code> - Text to speech
╰ <code>{0}lang</code> - mengubah bahasa
"""


# ============================================
# VARIABEL GLOBAL
# ============================================
STORAGE = {}


# ============================================
# ARCHIVE & UNARCHIVE
# ============================================
@PY.UBOT("arch")
@PY.TOP_CMD
async def archive_user(client, message):
    if len(message.command) < 2:
        return await message.reply("<b>❌ Usage:</b> <code>arch [all/users/group]</code>")
    
    msg = await message.reply("<b>⏳ Processing...</b>")
    target = message.command[1]
    chats = await get_data_id(client, target)
    
    total = len(chats)
    done = 0
    failed = 0
    
    for chat in chats:
        try:
            await client.archive_chats(chat)
            done += 1
        except:
            failed += 1
    
    await msg.edit(
        f"<b>✅ Succesfuly Archive</b>\n"
        f"├  <b>Target:</b> <code>{target}</code>\n"
        f"├  <b>Total:</b> <code>{total}</code>\n"
        f"├  <b>Success:</b> <code>{done}</code>\n"
        f"╰  <b>Failed:</b> <code>{failed}</code>\n"
        f"<blockquote>✨ Power By Fanzy Userbot</blockquote>"
    )


@PY.UBOT("unarch")
@PY.TOP_CMD
async def unarchive_user(client, message):
    if len(message.command) < 2:
        return await message.reply("<b>❌ Usage:</b> <code>unarch [all/users/group]</code>")
    
    msg = await message.reply("<b>⏳ Processing...</b>")
    target = message.command[1]
    chats = await get_data_id(client, target)
    
    total = len(chats)
    done = 0
    failed = 0
    
    for chat in chats:
        try:
            await client.unarchive_chats(chat)
            done += 1
        except:
            failed += 1
    
    await msg.edit(
        f"<b>✅ Succesfuly Unarchive</b>\n"
        f"├  <b>Target:</b> <code>{target}</code>\n"
        f"├  <b>Total:</b> <code>{total}</code>\n"
        f"├  <b>Success:</b> <code>{done}</code>\n"
        f"╰  <b>Failed:</b> <code>{failed}</code>\n"
        f"<blockquote>✨ Power By Fanzy Userbot</blockquote>"
    )


# ============================================
# CREATE GROUP/CHANNEL
# ============================================
@PY.UBOT("creat")
@PY.TOP_CMD
async def create_group_channel(client, message):
    if len(message.command) < 3:
        return await message.reply("<b>❌ Usage:</b> <code>creat [group/channel] [name]</code>")
    
    msg = await message.reply("<b>⏳ Creating...</b>")
    chat_type = message.command[1]
    chat_name = " ".join(message.command[2:])
    desc = f"Welcome to {chat_name}"
    
    if chat_type in ["group", "gc"]:
        chat = await client.create_supergroup(chat_name, desc)
        link = await client.get_chat(chat.id)
        await msg.edit(
            f"<b>✅ Succesfully Create Group</b>\n\n"
            f"<b>📎 Link Group:</b> <a href='{link.invite_link}'>[ klik link ini ]</a>\n"
            f"<b><blockquote>✨ Power By Fanzy Userbot</b></blockquote>",
            disable_web_page_preview=True
        )
    elif chat_type in ["channel", "ch"]:
        chat = await client.create_channel(chat_name, desc)
        link = await client.get_chat(chat.id)
        await msg.edit(
            f"<b>✅ Succesfully Create Channel</b>\n\n"
            f"<b>📎 Link Channel:</b> <a href='{link.invite_link}'>[ klik link ini ]</a>\n"
            f"<b><blockquote>✨ Power By Fanzy Userbot</b></blockquote>",
            disable_web_page_preview=True
        )
    else:
        await msg.edit("<b>❌ Type must be 'group' or 'channel'</b>")


# ============================================
# CREATE BOT VIA BOTFATHER
# ============================================
@PY.UBOT("creatbot")
@PY.TOP_CMD
async def create_bot_command(client, message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        return await message.reply(
            "<b>❌ Usage:</b> <code>creatbot [name] [username]</code>\n\n"
            "<b>Example:</b> <code>.creatbot MyBot MyNew_Bot</code>\n\n"
            "<b>📌 Note:</b> Username must end with 'Bot'"
        )
    
    bot_name = args[1]
    bot_username = args[2]
    
    # Validasi username harus diakhiri 'Bot'
    if not bot_username.endswith("Bot"):
        return await message.reply(
            "<b>❌ Invalid Username!</b>\n\n"
            "<b>📌 Username must end with 'Bot'</b>\n\n"
            "<b>Example:</b> <code>MyBot</code> or <code>ExampleBot</code>"
        )
    
    # Validasi panjang username (5-32 karakter)
    if len(bot_username) < 5 or len(bot_username) > 32:
        return await message.reply(
            "<b>❌ Invalid Username!</b>\n\n"
            "<b>📌 Username length must be 5-32 characters</b>"
        )
    
    msg = await message.reply("<b>⏳ Creating bot...</b>")
    
    try:
        botfather = "@BotFather"
        
        # Kirim perintah /newbot
        await client.send_message(botfather, "/newbot")
        await asyncio.sleep(2)
        
        # Kirim nama bot
        await client.send_message(botfather, bot_name)
        await asyncio.sleep(2)
        
        # Kirim username bot
        await client.send_message(botfather, bot_username)
        await asyncio.sleep(4)
        
        # Ambil response dari BotFather (cara yang kompatibel)
        response = None
        async for msg_bot in client.get_chat_history(botfather, limit=1):
            response = msg_bot
            break
        
        if response and response.text:
            response_text = response.text
            
            # Cek apakah username sudah dipakai
            if "already taken" in response_text.lower() or "already occupied" in response_text.lower():
                return await msg.edit(
                    f"<b>❌ Username Sudah Tersedia</b>\n\n"
                    f"<b>🔗 Username:</b> @{bot_username}\n\n"
                    f"<b>📌 silakan coba username lain</b>\n"
                    f"<blockquote>✨ Power By Fanzy Userbot</blockquote>"
                )
            
            # Cek apakah ada error lain
            if "sorry" in response_text.lower() or "error" in response_text.lower():
                return await msg.edit(
                    f"<b>❌ Failed Create Bot</b>\n\n"
                    f"<b>📌 Error:</b> <code>{response_text[:100]}</code>\n"
                    f"<blockquote>✨ Power By Fanzy Userbot</blockquote>"
                )
            
            # Cari token dari response
            import re
            token_match = re.search(r"(?:token|Token)[:\s]*([0-9]+:[a-zA-Z0-9_-]+)", response_text)
            bot_token = token_match.group(1) if token_match else "Check @BotFather"
            
            await msg.edit(
                f"<b>✅ Succesfuly Create Bot</b>\n\n"
                f"<b>🤖 Name:</b> <code>{bot_name}</code>\n"
                f"<b>🔗 Usrname:</b> @{bot_username}\n"
                f"<b>🔑 Token:</b> <code>{bot_token}</code>\n"
                f"<blockquote>✨ Power By Fanzy Userbot</blockquote>"
            )
        else:
            await msg.edit(
                f"<b>✅ Bot Create Successfuly</b>\n\n"
                f"<b>🤖 Name:</b> <code>{bot_name}</code>\n"
                f"<b>🔗 Usrname:</b> @{bot_username}\n\n"
                f"<blockquote>✨ Power By Fanzy Userbot</blockquote>"
            )
            
    except Exception as e:
        error_msg = str(e)
        
        # Handle error jika username sudah dipakai
        if "USERNAME_NOT_OCCUPIED" in error_msg:
            await msg.edit(
                f"<b>❌ Username Not Available!</b>\n\n"
                f"<b>🔗 @{bot_username}</b>\n\n"
                f"<b>📌 silakan coba username lain</b>\n"
                f"<blockquote>✨ Power By Fanzy Userbot</blockquote>"
            )
        else:
            await msg.edit(
                f"<b>❌ Failed to Create Bot!</b>\n\n"
                f"<b>📌 Error:</b> <code>{error_msg[:100]}</code>\n"
                f"<blockquote>✨ Power By Fanzy Userbot</blockquote>"
            )


# ============================================
# INVITE USER TO GROUP
# ============================================
@PY.UBOT("invit")
@PY.TOP_CMD
@PY.GROUP
async def invite_user(client, message):
    if len(message.command) < 2:
        return await message.reply("<b>❌ Usage:</b> <code>invite [username]</code>")
    
    msg = await message.reply("<b>⏳ Adding user...</b>")
    users = message.text.split(" ", 1)[1].split(" ")
    
    try:
        await client.add_chat_members(message.chat.id, users, forward_limit=100)
        await msg.edit(f"<b>✅ Succes Added {len(users)} user !")
    except Exception as e:
        await msg.edit(f"<b>❌ Error:</b> <code>{str(e)}</code>")


# ============================================
# JOIN & LEAVE
# ============================================
@PY.UBOT("kickme")
@PY.TOP_CMD
@PY.GROUP
async def kickme_group(client, message):
    msg = await message.reply("<b>⏳ Processing...</b>")
    
    if message.chat.id in BLACKLIST_CHAT:
        return await msg.edit("<b>❌ Command not allowed in this group!</b>")
    
    try:
        await msg.edit(f"<b>✅ {client.me.first_name} has left this group!</b>")
        await client.leave_chat(message.chat.id)
    except Exception as e:
        await msg.edit(f"<b>❌ Error:</b> <code>{str(e)}</code>")


@PY.UBOT("join")
@PY.TOP_CMD
async def join_chat(client, message):
    if len(message.command) < 2:
        return await message.reply("<b>❌ Usage:</b> <code>join [link/username]</code>")
    
    msg = await message.reply("<b>⏳ Joining...</b>")
    target = message.command[1]
    
    try:
        await client.join_chat(target)
        await msg.edit(
            f"<b>✅ Success Join groupt</b>\n"
            f"└  <code>{target}</code>\n"
            f"<b><blockquote>✨ Power By Fanzy Userbot</b></blockquote>"
        )
    except Exception as e:
        await msg.edit(
            f"<b>❌ Failed Join Chat</b>\n"
            f"└  <code>{str(e)[:50]}</code>\n"
            f"<b><blockquote>✨ Power By Fanzy Userbot</b></blockquote>"
        )


@PY.UBOT("leaveallgc")
@PY.TOP_CMD
async def leave_all_group(client, message):
    msg = await message.reply("<b>⏳ Leaving all groups...</b>")
    done = 0
    error = 0
    skipped = 0
    
    # Proses batch
    tasks = []
    async for dialog in client.get_dialogs():
        if dialog.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
            chat_id = dialog.chat.id
            
            if chat_id in BLACKLIST_CHAT:
                skipped += 1
                continue
            
            tasks.append(client.leave_chat(chat_id))
    
    # Eksekusi semua task concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, Exception):
            error += 1
        else:
            done += 1
    
    await msg.edit(
        f"<b>✅ Leave All Groups</b>\n"
        f"├ <b>Success:</b> <code>{done}</code>\n"
        f"├ <b>Failed:</b> <code>{error}</code>\n"
        f"╰ <b>Skipped:</b> <code>{skipped}</code>\n"
        f"<b><blockquote>✨ Power By Fanzy Userbot</b></blockquote>"
    )

@PY.UBOT("outmute")
@PY.TOP_CMD
async def leave_all_channel(client, message):
    msg = await message.reply("<b>⏳ Leaving all channels...</b>")
    
    # Kumpulkan semua channel
    channels = []
    async for dialog in client.get_dialogs():
        if dialog.chat.type == ChatType.CHANNEL:
            if dialog.chat.id not in BLACKLIST_CHAT:
                channels.append(dialog.chat.id)
    
    total = len(channels)
    
    if total == 0:
        return await msg.edit(
            f"<b>✅ No channels to leave</b>"
        )
    
    # Proses 10 channel sekaligus (batch)
    batch_size = 10
    done = 0
    error = 0
    
    for i in range(0, total, batch_size):
        batch = channels[i:i+batch_size]
        tasks = [client.leave_chat(chat_id) for chat_id in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                error += 1
            else:
                done += 1
        
        # Update progress
        await msg.edit(f"<b>⏳ Progress:</b> <code>{done}/{total} channels left...</code>")
        
        # Delay antar batch
        await asyncio.sleep(1)
    
    await msg.edit(
        f"<b>✅ Leave All Channels</b>\n"
        f"├ <b>Success:</b> <code>{done}</code>\n"
        f"╰<b>Failed:</b> <code>{error}</code>\n"
        f"<b><blockquote>✨ Power By Fanzy Userbot</b></blockquote>"
    )


# ============================================
# CLONE PROFILE
# ============================================
@PY.UBOT("clone")
async def clone_profile(client: Client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    
    msg = await message.edit("<b>⏳ Processing...</b>")
    
    # Ambil info user yang menjalankan perintah
    pelaku = await client.get_chat(user_id)
    pelaku_name = f"@{pelaku.username}" if pelaku.username else pelaku.first_name
    
    if "restore" in args:
        if user_id not in STORAGE:
            return await msg.edit("<b>❌ You haven't cloned anyone yet!</b>")
        
        await update_profile(client, STORAGE[user_id], restore=True)
        del STORAGE[user_id]
        
        return await msg.edit(
            f"<b>✅ Succesfuly restore user!</b>"
        )
    
    # Ambil target
    if args:
        try:
            user = await client.get_users(args)
        except:
            return await msg.edit("<b>❌ Invalid username/ID!</b>")
        target = await client.get_chat(user.id)
    elif message.reply_to_message:
        reply_user = message.reply_to_message.from_user
        if not reply_user:
            return await msg.edit("<b>❌ Cannot clone anonymous admin!</b>")
        target = await client.get_chat(reply_user.id)
    else:
        return await msg.edit("<b>❌ Usage:</b> <code>clone @username</code> or reply to user")
    
    # Nama target
    target_name = f"@{target.username}" if target.username else target.first_name
    
    # Simpan profil asli
    if user_id not in STORAGE:
        my_profile = await client.get_chat("me")
        my_photos = [p async for p in client.get_chat_photos("me")]
        STORAGE[user_id] = {"profile": my_profile, "photos": my_photos}
    
    await msg.edit("<b>⏳ Cloning profile...</b>")
    await update_profile(client, target)
    
    await msg.edit(
        f"<b>✅ Succesfuly cloning user!</b>\n"
        f"├  <b>Pelaku:</b> {pelaku_name}\n"
        f"╰  <b>Target:</b> {target_name}\n"
        f"<b><blockquote>✨ Power By Fanzy Userbot</b></blockquote>"
    )


async def update_profile(client: Client, target, restore=False):
    if restore:
        profile = target["profile"]
        photos = target["photos"]
        await client.update_profile(
            first_name=profile.first_name or "Deleted Account",
            last_name=profile.last_name or "",
            bio=profile.bio or ""
        )
        if photos:
            try:
                pfp = await client.download_media(photos[0].file_id)
                await client.set_profile_photo(photo=pfp)
            except:
                pass
        return
    
    first_name = target.first_name or "Deleted Account"
    last_name = target.last_name or ""
    user_info = await client.get_users(target.id)
    is_premium = user_info.is_premium if hasattr(user_info, "is_premium") else False
    bio = target.bio if is_premium else (target.bio[:70] if target.bio else "")
    
    try:
        photos = [p async for p in client.get_chat_photos(target.id)]
        if photos:
            pfp = await client.download_media(photos[0].file_id)
            await client.set_profile_photo(photo=pfp)
    except:
        pass
    
    await client.update_profile(first_name=first_name, last_name=last_name, bio=bio)


# ============================================
# GET PROFILE PICTURE
# ============================================
@PY.UBOT("getpp")
@PY.UBOT("getprofile")
@PY.TOP_CMD
async def get_profile_pic(client, message):
    if message.reply_to_message:
        target = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        target = message.command[1]
    else:
        target = message.chat.id
    
    if not target:
        return await message.reply("<b>❌ Usage:</b> <code>getpp @username</code> or reply to user")
    
    try:
        async for photo in client.get_chat_photos(target, limit=1):
            await client.send_photo(message.chat.id, photo=photo.file_id, caption="<b>✅ Succesfuly Picture Send!</b>")
            return
        await message.reply("<b>❌ No profile picture found!</b>")
    except (UsernameNotOccupied, UserNotParticipant, PeerIdInvalid):
        await message.reply("<b>❌ User or chat not found!</b>")
    except Exception as e:
        await message.reply(f"<b>❌ Error:</b> <code>{str(e)}</code>")


# ============================================
# TRANSLATE & TEXT TO SPEECH
# ============================================
@PY.UBOT("tts")
@PY.TOP_CMD
async def text_to_speech(client, message):
    msg = await message.reply("<b>⏳ Processing...</b>")
    
    if message.reply_to_message:
        language = client._translate[client.me.id]
        words = message.reply_to_message.text or message.reply_to_message.caption
    else:
        if len(message.command) < 2:
            return await msg.edit(f"<b>❌ Usage:</b> <code>tts [text]</code> or reply to message")
        language = client._translate[client.me.id]
        words = message.text.split(None, 1)[1]
    
    speech = gtts.gTTS(words, lang=language)
    speech.save("tts_voice.oog")
    
    try:
        await client.send_voice(chat_id=message.chat.id, voice="tts_voice.oog", reply_to_message_id=message.reply_to_message.id if message.reply_to_message else message.id)
        await msg.delete()
    except Exception as e:
        await msg.edit(f"<b>❌ Error:</b> <code>{str(e)}</code>")
    try:
        os.remove("tts_voice.oog")
    except:
        pass


@PY.UBOT("tr")
@PY.TOP_CMD
async def translate_text(client, message):
    trans = Translator()
    msg = await message.reply("<b>⏳ Translating...</b>")
    
    if message.reply_to_message:
        dest = client._translate[client.me.id]
        text = message.reply_to_message.text or message.reply_to_message.caption
        source = await trans.detect(text)
    else:
        if len(message.command) < 2:
            return await msg.edit(f"<b>❌ Usage:</b> <code>tr [text]</code> or reply to message")
        dest = client._translate[client.me.id]
        text = message.text.split(None, 1)[1]
        source = await trans.detect(text)
    
    result = await trans(text, sourcelang=source, targetlang=dest)
    await msg.edit(f"<b>✅ Translation:</b>\n\n{result.text}")


@PY.UBOT("lang")
@PY.TOP_CMD
async def set_language(client, message):
    query = id(message)
    try:
        x = await client.get_inline_bot_results(bot.me.username, f"set_lang {query}")
        await message.reply_inline_bot_result(x.query_id, x.results[0].id)
    except Exception as e:
        await message.reply(f"<b>❌ Error:</b> <code>{str(e)}</code>")


@PY.INLINE("^set_lang")
async def set_lang_inline(client, inline_query):
    buttons = InlineKeyboard(row_width=3)
    keyboard = []
    for code in lang_code_translate:
        keyboard.append(InlineKeyboardButton(Fonts.smallcap(code.lower()), callback_data=f"set_lang_cb {int(inline_query.query.split()[1])} {code}"))
    buttons.add(*keyboard)
    
    await client.answer_inline_query(
        inline_query.id,
        cache_time=0,
        results=[InlineQueryResultArticle(
            title="Select Language",
            reply_markup=buttons,
            input_message_content=InputTextMessageContent("<b>🌐 Select your translation language:</b>")
        )]
    )


@PY.CALLBACK("^set_lang_cb")
async def set_lang_callback(client, callback_query):
    data = callback_query.data.split()
    try:
        msg = [obj for obj in get_objects() if id(obj) == int(data[1])][0]
        msg._client._translate[msg._client.me.id] = lang_code_translate[data[2]]
        await callback_query.edit_message_text(f"<b>✅ Language changed to: {Fonts.smallcap(data[2].lower())}")
    except Exception as e:
        await callback_query.edit_message_text(f"<b>❌ Error:</b> <code>{str(e)}</code>")