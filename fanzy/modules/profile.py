import asyncio
import os
import random
from asyncio import sleep, gather
from datetime import datetime
from random import shuffle
from time import time

from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import FloodWait, RPCError
from pyrogram.raw.functions.contacts import AddContact, DeleteContacts
from pyrogram.raw.functions.messages import DeleteHistory
from pyrogram.raw.types import InputUser
from pyrogram.types import Message

from fanzy import *

__MODULE__ = "Profile"
__HELP__ = """
<b>📁 PROFILE TOOLS</b>

<b>🔧 Commands:</code>
├ <code>{0}setbio</code> - Change bio
├ <code>{0}setname</code> - Change name
├ <code>{0}clone</code> - Clone profile
├ <code>{0}restore</code> - Restore profile
├ <code>{0}info</code> - User info
├ <code>{0}cinfo</code> - Chat info
├ <code>{0}id</code> - Get ID
├ <code>{0}idm</code> - Message ID
├ <code>{0}sg</code> - Sangmata
├ <code>{0}block</code> - Block user
├ <code>{0}unblock</code> - Unblock user
├ <code>{0}tagall</code> - Tag all members
├ <code>{0}batal</code> - Cancel tagall
├ <code>{0}spam</code> - Spam message
├ <code>{0}setdelay</code> - Set spam delay
├ <code>{0}stopspam</code> - Stop spam
├ <code>{0}sev</code> - Save contact
╰ <code>{0}del</code> - Delete contact
"""


# ============================================
# VARIABEL GLOBAL
# ============================================
tagallgcid = []
spam_progress = []


# ============================================
# EMOJI RANDOM UNTUK TAGALL
# ============================================
emoji_categories = {
    "smileys": ["😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😍", "🥰", "😘", "😎", "🥳", "😇", "🙃", "😋", "😛", "🤪"],
    "animals": ["🐶", "🐱", "🐰", "🐻", "🐼", "🦁", "🐸", "🦊", "🦔", "🦄", "🐢", "🐠", "🐦", "🦜", "🦢", "🦚", "🦓", "🐅", "🦔"],
    "food": ["🍎", "🍕", "🍔", "🍟", "🍩", "🍦", "🍓", "🥪", "🍣", "🍔", "🍕", "🍝", "🍤", "🥗", "🥐", "🍪", "🍰", "🍫", "🥤"],
    "nature": ["🌲", "🌺", "🌞", "🌈", "🌊", "🌍", "🍁", "🌻", "🌸", "🌴", "🌵", "🍃", "🍂", "🌼", "🌱", "🌾", "🍄", "🌿", "🌳"],
    "travel": ["✈️", "🚀", "🚲", "🚗", "⛵", "🏔️", "🚁", "🚂", "🏍️", "🚢", "🚆", "🛴", "🛸", "🛶", "🚟", "🚈", "🛵", "🛎️", "🚔"],
    "sports": ["⚽", "🏀", "🎾", "🏈", "🎱", "🏓", "🥊", "⛳", "🏋️", "🏄", "🤸", "🏹", "🥋", "🛹", "🥏", "🎯", "🥇", "🏆", "🥅"],
    "music": ["🎵", "🎶", "🎤", "🎧", "🎼", "🎸", "🥁", "🎷", "🎺", "🎻", "🪕", "🎹", "🔊"],
    "celebration": ["🎉", "🎊", "🥳", "🎈", "🎁", "🍰", "🧁", "🥂", "🍾", "🎆", "🎇"],
    "work": ["💼", "👔", "👓", "📚", "✏️", "📆", "🖥️", "🖊️", "📂", "📌", "📎"],
    "emotions": ["❤️", "💔", "😢", "😭", "😠", "😡", "😊", "😃", "🙄", "😳", "😇", "😍"],
}


def emoji_random():
    random_category = random.choice(tuple(emoji_categories.keys()))
    return random.choice(emoji_categories[random_category])


# ============================================
# FUNGSI HELPER
# ============================================
async def SpamMsg(client, message, send):
    delay = await get_vars(client.me.id, "SPAM") or 0
    await asyncio.sleep(int(delay))
    if message.reply_to_message:
        await send.copy(message.chat.id)
    else:
        await client.send_message(message.chat.id, send)


def get_file_id(message):
    if message.photo:
        return message.photo
    elif message.video:
        return message.video
    elif message.audio:
        return message.audio
    elif message.document:
        return message.document
    elif message.sticker:
        return message.sticker
    elif message.animation:
        return message.animation
    elif message.voice:
        return message.voice
    elif message.video_note:
        return message.video_note
    return None


# ============================================
# SANGMATA (SG)
# ============================================
@PY.UBOT("sg")
@PY.TOP_CMD
async def sg_cmd(client, message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply("<b>❌ Usage:</b> <code>sg [username/id/reply]</code>")
    
    msg = await message.reply("<b>⏳ Processing...</b>")
    
    try:
        user = await client.get_users(user_id)
        bot = random.choice(["@Sangmata_bot", "@SangMata_beta_bot"])
        
        await client.unblock_user(bot)
        txt = await client.send_message(bot, user.id)
        await asyncio.sleep(4)
        await txt.delete()
        await msg.delete()
        
        async for name in client.get_chat_history(bot, limit=2):
            if name.text:
                await message.reply(name.text, quote=True)
                break
        
        await client.invoke(DeleteHistory(peer=await client.resolve_peer(bot), max_id=0, revoke=True))
        
    except Exception as e:
        await msg.edit(f"<b>❌ Error:</b> <code>{str(e)[:100]}</code>")


# ============================================
# INFO USER
# ============================================
@PY.UBOT("info")
@PY.TOP_CMD
async def info_cmd(client, message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply("<b>❌ Usage:</b> <code>info [username/id/reply]</code>")
    
    msg = await message.reply("<b>⏳ Processing...</b>")
    
    try:
        user = await client.get_users(user_id)
        chat = await client.get_chat(user.id)
        
        first_name = user.first_name or "-"
        last_name = user.last_name or "-"
        username = f"@{user.username}" if user.username else "-"
        bio = chat.bio or "-"
        dc_id = user.dc_id or "-"
        common = len(await client.get_common_chats(user.id))
        status = str(user.status).replace("UserStatus.", "").capitalize() if user.status else "-"
        
        badges = []
        if user.is_verified:
            badges.append("✅ Verified")
        if user.is_premium:
            badges.append("⭐ Premium")
        if user.is_bot:
            badges.append("🤖 Bot")
        badge_text = " │ ".join(badges) if badges else "Normal"
        
        text = f"""
<b>📊 USER INFORMASI</b>

<b>👤 Name:</b> {first_name} {last_name}
<b>🔗 Username:</b> {username}
<b>🆔 ID:</b> <code>{user.id}</code>
<b>📛 Status:</b> {badge_text}

<b>📝 Bio:</b> {bio}
<b>📡 DC:</b> {dc_id}
<b>👥 Common:</b> {common}
<b>⏱️ Last:</b> {status}

<blockquote>⚡ Power By Fanzy Userbot</blockquote>
"""
        await msg.edit(text, disable_web_page_preview=True)
        
    except Exception as e:
        await msg.edit(f"<b>❌ Error:</b> <code>{str(e)[:100]}</code>")


# ============================================
# INFO CHAT
# ============================================
@PY.UBOT("cinfo")
@PY.TOP_CMD
async def cinfo_cmd(client, message):
    msg = await message.reply("<b>⏳ Processing...</b>")
    
    try:
        if len(message.command) > 1:
            chat = await client.get_chat(message.command[1])
        else:
            if message.chat.type == ChatType.PRIVATE:
                return await msg.edit("<b>❌ Use in group or add chat ID/username</b>")
            chat = await client.get_chat(message.chat.id)
        
        chat_type = str(chat.type).replace("ChatType.", "").capitalize()
        username = f"@{chat.username}" if chat.username else "-"
        
        badges = []
        if chat.is_verified:
            badges.append("✅ Verified")
        if chat.is_scam:
            badges.append("⚠️ Scam")
        badge_text = " │ ".join(badges) if badges else "Normal"
        
        text = f"""
<b>📊 CHAT INFORMASI</b>

<b>📛 Title:</b> {chat.title}
<b>🔗 Username:</b> {username}
<b>🆔 ID:</b> <code>{chat.id}</code>
<b>📋 Type:</b> {chat_type}
<b>📛 Badge:</b> {badge_text}

<b>👥 Members:</b> {chat.members_count or '-'}
<b>📡 DC Id:</b> {chat.dc_id or '-'}

<blockquote>⚡ Power By Fanzy Userbot</blockquote>
"""
        await msg.edit(text, disable_web_page_preview=True)
        
    except Exception as e:
        await msg.edit(f"<b>❌ Error:</b> <code>{str(e)[:100]}</code>")


# ============================================
# ID
# ============================================
@PY.UBOT("id")
@PY.TOP_CMD
async def id_cmd(client, message):
    text = f"<b>📊 ID INFO</b>\n\n"
    text += f"├ <b>Message ID:</b> <code>{message.id}</code>\n"
    
    if message.chat.type == ChatType.CHANNEL:
        text += f"├ <b>Chat ID:</b> <code>{message.sender_chat.id}</code>\n"
    else:
        text += f"├ <b>Your ID:</b> <code>{message.from_user.id}</code>\n"
        
        if len(message.command) > 1:
            try:
                user = await client.get_chat(message.command[1])
                text += f"├ <b>User ID:</b> <code>{user.id}</code>\n"
            except:
                pass
        
        text += f"╰ <b>Chat ID:</b> <code>{message.chat.id}</code>\n"
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id if message.reply_to_message.from_user else message.reply_to_message.sender_chat.id
        text += f"\n<b>📎 Reply:</b>\n"
        text += f"├ <b>Msg ID:</b> <code>{message.reply_to_message.id}</code>\n"
        text += f"╰ <b>User ID:</b> <code>{user_id}</code>\n"
    
    text += f"\n<blockquote>⚡ Power By Fanzy Userbot</blockquote>"
    await message.reply(text, disable_web_page_preview=True)


@PY.UBOT("idm")
@PY.TOP_CMD
async def idm_cmd(client, message):
    if not message.reply_to_message or not message.reply_to_message.entities:
        return await message.reply("<b>❌ Reply to a message with custom emoji</b>")
    
    emoji_id = message.reply_to_message.entities[0].custom_emoji_id
    await message.reply(f"<b>📊 EMOJI ID</b>\n╰ <code>{emoji_id}</code>\n<blockquote>⚡ Power By Fanzy Userbot</blockquote>")


# ============================================
# SET BIO
# ============================================
@PY.UBOT("setbio")
@PY.TOP_CMD
async def setbio_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply(
            "<b>❌ Usage Error!</b>\n\n"
            "<b>📌 Format:</b> <code>setbio [text]</code>\n"
            "<b>📝 Example:</b> <code>setbio example 12345</code>\n"
            "<blockquote>⚡ Power By Fanzy Userbot</blockquote>"
        )
    
    msg = await message.reply("<b>⏳ Processing...</b>")
    bio = message.text.split(None, 1)[1]
    
    if len(bio) > 70:
        return await msg.edit(
            "<b>❌ Bio Limit Exceeded!</b>\n\n"
            f"<b>📌 Your bio length:</b> <code>{len(bio)} karakter</code>\n"
            f"<b>📌 Max allowed:</b> <code>70 karakter</code>\n"
            "<b>💡 Tips:</b> peringkat bio anda!\n"
            "<blockquote>⚡ Power By Fanzy Userbot</blockquote>"
        )
    
    try:
        old_bio = (await client.get_chat("me")).bio or "Empty"
        await client.update_profile(bio=bio)
        
        await msg.edit(
            f"<b>✅ Successfuly Update Bio!</b>"
        )
    except FloodWait as e:
        await msg.edit(
            f"<b>❌ Rate Limited!</b>\n\n"
            f"<b>📌 Wait:</b> <code>{e.value} seconds</code> before trying again\n"
            "<blockquote>⚡ Power By Fanzy Userbot</blockquote>"
        )
    except Exception as e:
        await msg.edit(
            f"<b>❌ Update Failed!</b>\n\n"
            f"<b>📌 Error:</b> <code>{str(e)[:100]}</code>\n"
            "━━━━━━━━━━━━━━━━━━❍\n"
            "<blockquote>⚡ Power By Fanzy Userbot</blockquote>"
        )


# ============================================
# SET NAME
# ============================================
@PY.UBOT("setname")
@PY.TOP_CMD
async def setname_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply(
            "<b>❌ Usage Error!</b>\n\n"
            "<b>📌 Format:</b> <code>setname firstname,lastname</code>\n"
            "<b>📝 Example:</b> <code>setname John Doe</code>\n"
            "<blockquote>⚡ Power By Fanzy Userbot</blockquote>"
        )
    
    msg = await message.reply("<b>⏳ Processing...</b>")
    args = message.text.split(None, 1)[1].split()
    
    first_name = args[0]
    last_name = " ".join(args[1:]) if len(args) > 1 else ""
    
    try:
        me = await client.get_chat("me")
        old_first = me.first_name or "-"
        old_last = me.last_name or "-"
        
        await client.update_profile(first_name=first_name, last_name=last_name)
        
        await msg.edit(
            f"<b>✅ Successfuly Update Name</b>"
        )
    except Exception as e:
        await msg.edit(
            f"<b>❌ Update Failed!</b>\n\n"
            f"<b>📌 Error:</b> <code>{str(e)[:100]}</code>\n"
            f"<blockquote>⚡ Power By Fanzy Userbot</blockquote>"
        )


# ============================================
# BLOCK & UNBLOCK
# ============================================
@PY.UBOT("block")
@PY.TOP_CMD
async def block_cmd(client, message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply(
            "<b>❌ Usage Error!</b>\n\n"
            "<b>📌 Format:</b> <code>block [username/id/reply]</code>\n"
            "<b>📝 Example:</b> <code>block @username</code>\n"
           "<blockquote>⚡ Power By Fanzy Userbot</blockquote>"
        )
    
    if user_id == client.me.id:
        return await message.reply(
            "<b>❌ Cannot Block Yourself!</b>"
        )
    
    msg = await message.reply("<b>⏳ Processing...</b>")
    
    try:
        await client.block_user(user_id)
        user = await client.get_users(user_id)
        
        username = f"@{user.username}" if user.username else "No username"
        fullname = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
        
        await msg.edit(
            f"<b>✅ User Blocked!</b>\n\n"
            f"<b>🔗 Username:</b> {username}\n"
            f"<b>🆔 User ID:</b> <code>{user.id}</code>\n"
           "<blockquote>⚡ Power By Fanzy Userbot</blockquote>"
        )
    except Exception as e:
        await msg.edit(f"<b>❌ Block Failed!</b>\n\n<code>{str(e)[:80]}</code>")


@PY.UBOT("unblock")
@PY.TOP_CMD
async def unblock_cmd(client, message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply(
            "<b>❌ Usage Error!</b>\n\n"
            "<b>📌 Format:</b> <code>unblock [username/id/reply]</code>"
        )
    
    msg = await message.reply("<b>⏳ Processing...</b>")
    
    try:
        await client.unblock_user(user_id)
        user = await client.get_users(user_id)
        
        username = f"@{user.username}" if user.username else "No username"
        fullname = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
        
        await msg.edit(
            f"<b>✅ User Unblocked!</b>\n\n"
            f"<b>🔗 Username:</b> {username}\n"
            f"<b>🆔 User ID:</b> <code>{user.id}</code>\n"
           "<blockquote>⚡ Power By Fanzy Userbot</blockquote>"
        )
    except Exception as e:
        await msg.edit(f"<b>❌ Unblock Failed!</b>\n\n<code>{str(e)[:80]}</code>")


# ============================================
# STAFF
# ============================================
@PY.UBOT("staff")
@PY.TOP_CMD
async def staff_cmd(client, message):
    msg = await message.reply("<b>⏳ Processing...</b>")
    chat = message.chat
    chat_title = chat.title
    
    creator = []
    co_founder = []
    admin = []
    
    async for member in chat.get_members():
        mention = f"<a href=tg://user?id={member.user.id}>{member.user.first_name}</a>"
        status = member.status.value
        
        if status == "owner":
            creator.append(f"└ {mention}")
        elif status == "administrator":
            if member.privileges and member.privileges.can_promote_members:
                co_founder.append(f"├ {mention}")
            else:
                admin.append(f"├ {mention}")
    
    # Format output
    result = f"<b>📊 STAFF {chat_title}</b>\n\n"
    
    if creator:
        result += f"<b>👑 Owner:</b>\n{creator[0]}\n\n"
    if co_founder:
        co_founder[-1] = co_founder[-1].replace("├", "└")
        result += f"<b>👮 Co-Founder:</b>\n" + "\n".join(co_founder) + "\n\n"
    if admin:
        admin[-1] = admin[-1].replace("├", "└")
        result += f"<b>🛡️ Admin:</b>\n" + "\n".join(admin)
    
    result += f"\n━━━━━━━━━━━━━━━━━━❍\n<blockquote>⚡ Power By Fanzy Userbot</blockquote>"
    await msg.edit(result)


# ============================================
# TAGALL
# ============================================
@PY.UBOT("tagall")
@PY.TOP_CMD
@PY.GROUP
async def tagall_cmd(client, message):
    if message.chat.id in tagallgcid:
        return await message.reply("<b>⏳ TagAll already running!</b>")
    
    tagallgcid.append(message.chat.id)
    text = message.text.split(None, 1)[1] if len(message.command) > 1 else ""
    
    users = []
    async for member in message.chat.get_members():
        if not (member.user.is_bot or member.user.is_deleted):
            users.append(f"<a href=tg://user?id={member.user.id}>{emoji_random()}</a>")
    
    shuffle(users)
    m = message.reply_to_message or message
    
    for batch in [users[i:i+5] for i in range(0, len(users), 5)]:
        if message.chat.id not in tagallgcid:
            break
        await m.reply_text(f"{text}\n\n{' '.join(batch)}")
        await asyncio.sleep(2)
    
    tagallgcid.remove(message.chat.id)


@PY.UBOT("batal")
@PY.TOP_CMD
@PY.GROUP
async def batal_tagall_cmd(client, message):
    if message.chat.id not in tagallgcid:
        return await message.reply("<b>❌ No active TagAll!</b>")
    
    tagallgcid.remove(message.chat.id)
    await message.reply("<b>✅ TagAll cancelled!")


# ============================================
# SPAM
# ============================================
@PY.UBOT("spam")
@PY.TOP_CMD
async def spam_cmd(client, message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("<b>❌ Usage:</b> <code>spam [count] [text/reply]</code>")
    
    try:
        count = int(args[1])
    except:
        return await message.reply("<b>❌ Count must be number!</b>")
    
    msg_text = " ".join(args[2:]) if len(args) > 2 else None
    
    if not msg_text and not message.reply_to_message:
        return await message.reply("<b>❌ Provide text or reply to message!</b>")
    
    msg = await message.reply("<b>⏳ Processing...</b>")
    spam_progress.append(client.me.id)
    
    for i in range(count):
        if client.me.id not in spam_progress:
            await msg.edit("<b>✅ Spam stopped!</b>")
            return
        
        if message.reply_to_message:
            await message.reply_to_message.copy(message.chat.id)
        else:
            await client.send_message(message.chat.id, msg_text)
        
        delay = await get_vars(client.me.id, "SPAM") or 0
        if delay > 0:
            await asyncio.sleep(delay)
    
    spam_progress.remove(client.me.id)
    await msg.edit(f"<b>✅ Spam completed!</b>\n╰ <code>{count}</code> messages sent\n<blockquote>⚡ Power By Fanzy Userbot</blockquote>")


@PY.UBOT("setdelay")
@PY.TOP_CMD
async def setdelay_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply("<b>❌ Usage:</b> <code>setdelay [seconds]</code>")
    
    try:
        delay = int(message.command[1])
        await set_vars(client.me.id, "SPAM", delay)
        await message.reply(f"<b>✅ Spam delay set!</b>\n╰ <code>{delay}\nseconds</code\n<blockquote>⚡ Power By Fanzy Userbot</blockquote>")
    except:
        await message.reply("<b>❌ Invalid number!</b>")


@PY.UBOT("stopspam")
@PY.TOP_CMD
async def stopspam_cmd(client, message):
    if client.me.id in spam_progress:
        spam_progress.remove(client.me.id)
        await message.reply("<b>✅ Spam stopped!</b>")
    else:
        await message.reply("<b>❌ No active spam!</b>")


# ============================================
# SAVE & DELETE CONTACT
# ============================================
@PY.UBOT("sev")
@PY.TOP_CMD
async def save_contact_cmd(client, message):
    user_id = None
    custom_name = ""
    
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
        custom_name = message.text.split(maxsplit=1)[1] if len(message.command) > 1 else ""
    elif len(message.command) >= 3:
        user_id = message.command[1]
        custom_name = message.command[2]
    else:
        return await message.reply("<b>❌ Usage:</b> <code>sev [user] [name]</code> or reply to user")
    
    if not custom_name:
        return await message.reply("<b>❌ Name cannot be empty!</b>")
    
    msg = await message.reply("<b>⏳ Processing...</b>")
    
    try:
        user = await client.get_users(user_id)
        peer = await client.resolve_peer(user.id)
        
        await client.invoke(AddContact(id=peer, first_name=custom_name, last_name="", phone=""))
        await msg.edit(f"<b>✅ Succesfuly Save kontak</b>\n╰ {custom_name} (@{user.username or user.id})\n<blockquote>⚡ Power By Fanzy Userbot</blockquote>")
    except Exception as e:
        await msg.edit(f"<b>❌ Error:</b> <code>{str(e)[:100]}</code>")


@PY.UBOT("del")
@PY.TOP_CMD
async def delete_contact_cmd(client, message):
    user_id = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    elif len(message.command) >= 2:
        user_id = message.command[1]
    else:
        return await message.reply("<b>❌ Usage:</b> <code>del [user]</code> or reply to user")
    
    msg = await message.reply("<b>⏳ Processing...</b>")
    
    try:
        user = await client.get_users(user_id)
        await client.delete_contacts([user.id])
        await msg.edit(f"<b>✅ Succesfuly delete kontak</b>\n╰ @{user.username or user.id}\n<blockquote>⚡ Power By Fanzy Userbot</blockquote>")
    except Exception as e:
        await msg.edit(f"<b>❌ Error:</b> <code>{str(e)[:100]}</code>")