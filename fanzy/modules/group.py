import asyncio
from pyrogram.enums import ChatMembersFilter
from pyrogram import Client, filters
from pyrogram.enums import ChatType, ChatMemberStatus, MessageEntityType
from pyrogram import *
from pyrogram.enums import *
from pyrogram.errors import *
from pyrogram.types import *
from fanzy import *

__MODULE__ = "Group"
__HELP__ = """
<b>📋 DAFTAR PERINTAH</b>

╭ <b><code>{0}kick</b></code> - Kick member
├ <b><code>{0}ban</b></code> - Banned member
├ <b><code>{0}mute</b></code> - Mute member
╰ <b><code>{0}unban</b></code> - Unban member

╭ <b><code>{0}unmute</b></code> - Unmute member
├ <b><code>{0}atmin</b></code> - Adminkan member
├ <b><code>{0}ceo</b></code> - Adminkan member
╰ <b><code>{0}demote</b></code> - Unadmin member

╭ <b><code>{0}getlink</b></code> - Ambil link group
├ <b><code>{0}lock</b></code> - Lock group
├ <b><code>{0}unlock</b></code> - Unlock group
├ <b><code>{0}locks</b></code> - View current locks
╰ <b><code>{0}Kicx</b></code> - kick akun terhapus

╭ <b><code>{0}antilink</code> - on/off
├ <b><code>{0}antipromosi</code> - on/off
├ <b><code>{0}adkta</code> - add daftar kata
╰ <b><code>{0}antiforward</code> - on/off


<b>📝 Examples:</b>
├ <code>{0}lock msg</code> - Lock chat
├ <code>{0}lock media</code> - Lock media
├ <code>{0}unlock all</code> - Unlock all
╰ <code>{0}kicx</code> @user - Kick user
"""

incorrect_parameters = "<b>❌ Invalid parameter!\n\nExample: <code>lock msg</code>\nExample: <code>unlock all</code></b>"
ADDITIONAL_KEYWORDS = []
data = {
    "msg": "can_send_messages",
    "stickers": "can_send_other_messages",
    "gifs": "can_send_other_messages",
    "media": "can_send_media_messages",
    "games": "can_send_other_messages",
    "inline": "can_send_other_messages",
    "url": "can_add_web_page_previews",
    "polls": "can_send_polls",
    "info": "can_change_info",
    "invite": "can_invite_users",
    "pin": "can_pin_messages",
}


# ============================================
# HELPER FUNCTIONS
# ============================================
async def is_group(chat):
    """Check if chat is a group (not channel)"""
    return chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]


async def is_admin_bot(client, chat_id):
    """Check if bot is admin in group"""
    try:
        bot_member = await client.get_chat_member(chat_id, client.me.id)
        status = bot_member.status
        print(f"Bot status in {chat_id}: {status}")
        
        if status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True
        return False
    except Exception as e:
        print(f"Error checking bot admin: {e}")
        return False

async def list_admins(client, chat_id):
    """Get list of admin IDs in group"""
    admins = []
    try:
        async for member in client.get_chat_members(chat_id, filter="administrators"):
            admins.append(member.user.id)
    except Exception as e:
        try:
            async for member in client.get_chat_members(chat_id):
                if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                    admins.append(member.user.id)
        except Exception as e2:
            print(f"Error getting admins (fallback): {e2}")
    
    return admins

async def extract_user(message):
    """Extract user_id from message"""
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        try:
            return int(message.command[1])
        except ValueError:
            try:
                user = await message.client.get_users(message.command[1])
                return user.id
            except Exception:
                return None
    return None


async def extract_user_and_reason(message):
    args = message.text.split()
    user_id = None
    reason = "No reason provided"
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        if len(args) > 1:
            reason = " ".join(args[1:])           
    elif len(args) > 1:
        user_part = args[1]
        if user_part.isdigit():
            user_id = int(user_part)
        elif user_part.startswith("@"):
            user_id = user_part       
        if len(args) > 2:
            reason = " ".join(args[2:])
        else:
            reason = "No reason provided"            
    return user_id, reason


async def eor(message, text):
    """Edit or reply"""
    if message.from_user.is_self:
        return await message.edit(text)
    return await message.reply(text)


# ============================================
# LOCK / UNLOCK
# ============================================

async def current_chat_permissions(client, chat_id):
    perms = []
    perm = (await client.get_chat(chat_id)).permissions
    if perm.can_send_messages:
        perms.append("can_send_messages")
    if perm.can_send_media_messages:
        perms.append("can_send_media_messages")
    if perm.can_send_other_messages:
        perms.append("can_send_other_messages")
    if perm.can_add_web_page_previews:
        perms.append("can_add_web_page_previews")
    if perm.can_send_polls:
        perms.append("can_send_polls")
    if perm.can_change_info:
        perms.append("can_change_info")
    if perm.can_invite_users:
        perms.append("can_invite_users")
    if perm.can_pin_messages:
        perms.append("can_pin_messages")
    return perms


async def tg_lock(
    client,
    message,
    parameter,
    permissions: list,
    perm: str,
    lock: bool,
):
    if lock:
        if perm not in permissions:
            return await message.reply(f"<b>🔒 <code>{parameter}</code> is already locked!</b>")
        permissions.remove(perm)
    else:
        if perm in permissions:
            return await message.reply(f"<b>🔓 <code>{parameter}</code> is already unlocked!</b>")
        permissions.append(perm)
    permissions = {perm: True for perm in set(permissions)}
    try:
        await client.set_chat_permissions(
            message.chat.id, ChatPermissions(**permissions)
        )
    except ChatNotModified:
        return await message.reply(
            f"<b>❌ Failed to {message.text.split()[0]} [type]</b>"
        )
    except ChatAdminRequired:
        return await message.reply("<b>❌ Bot lacks admin privileges!</b>")
    await message.reply(
        f"<b>✅ Successfully {'locked' if lock else 'unlocked'}!</b>\n"
        f"<b>📌 Type:</b> <code>{parameter}</code>\n"
        f"<b>👥 Group:</b> {message.chat.title}"
    )



@PY.UBOT("adkta")
async def add_forbidden_word(client, message):
    args = get_arg(message)
    if not args:
        return await message.edit("<b>Gunakan format:</b> <code>.adkta [kata]</code>")
    
    word = args.lower()
    if word in ADDITIONAL_KEYWORDS:
        return await message.edit(f"Kata <code>{word}</code> sudah ada di daftar.")
    
    ADDITIONAL_KEYWORDS.append(word)
    await message.edit(f"✅ Berhasil menambahkan <code>{word}</code> ke daftar antipromosi.")

@PY.UBOT("listkata")
async def list_forbidden_word(client, message):
    if not ADDITIONAL_KEYWORDS:
        return await message.edit("Belum ada kata terlarang tambahan.")
    
    teks = "<b>📋 KATA TERLARANG CUSTOM:</b>\n"
    for i, word in enumerate(ADDITIONAL_KEYWORDS, 1):
        teks += f"{i}. <code>{word}</code>\n"
  
    await message.edit(teks)
            
            
@PY.UBOT("lock|unlock")
@PY.TOP_CMD
@PY.GROUP
async def lock_handler(client, message):
    if not await is_group(message.chat):
        return await message.reply("<b>❌ This command can only be used in groups!</b>")
    
    if len(message.command) != 2:
        return await message.reply(f"<b>❌ Usage:</b> <code>{message.text.split()[0]} [type]</code>")
    
    chat_id = message.chat.id
    parameter = message.text.strip().split(None, 1)[1].lower()
    state = message.command[0].lower()
    
    if parameter not in data and parameter != "all":
        return await message.reply(incorrect_parameters)
    
    permissions = await current_chat_permissions(client, chat_id)
    
    if parameter in data:
        await tg_lock(
            client,
            message,
            parameter,
            permissions,
            data[parameter],
            bool(state == "lock"),
        )
    elif parameter == "all" and state == "lock":
        try:
            await client.set_chat_permissions(chat_id, ChatPermissions())
            await message.reply(
                f"<b>✅ Succesfully lock all!</b>\n"
                f"<b>👥 Group:</b> {message.chat.title}"
            )
        except ChatAdminRequired:
            return await message.reply("<b>❌ Bot lacks admin privileges!</b>")
        except ChatNotModified:
            return await message.reply(
                f"<b>✅ Already locked!</b>\n"
                f"<b>👥 Group:</b> {message.chat.title}"
            )
    elif parameter == "all" and state == "unlock":
        try:
            await client.set_chat_permissions(
                chat_id,
                ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_send_polls=True,
                    can_change_info=False,
                    can_invite_users=True,
                    can_pin_messages=False,
                ),
            )
        except ChatAdminRequired:
            return await message.reply("<b>❌ Bot lacks admin privileges!</b>")
        await message.reply(
            f"<b>✅ Successfully unlocked all!</b>\n"
            f"<b>👥 Group:</b> {message.chat.title}"
        )


@PY.UBOT("locks")
@PY.TOP_CMD
@PY.GROUP
async def locks_handler(client, message):
    if not await is_group(message.chat):
        return await message.reply("<b>❌ This command can only be used in groups!</b>")
    
    permissions = await current_chat_permissions(client, message.chat.id)
    if not permissions:
        return await message.reply("<b>🔒 All permissions are locked!</b>")

    perms = "<b>🔒 Current Locks:</b>\n\n├ " + "\n├ ".join(permissions)
    await message.reply(perms)


# ============================================
# KICK, BAN, MUTE, UNMUTE, UNBAN
# ============================================

@PY.UBOT("kick|ban|mute|unmute|unban")
@PY.TOP_CMD
@PY.GROUP
async def admin_action_handler(client, message):
    if not await is_group(message.chat):
        return await message.reply("<b>❌ This command can only be used in groups!</b>")
    
    if not await is_admin_bot(client, message.chat.id):
        return await message.reply("<b>❌ Bot must be an admin first!</b>")
    
    cmd = message.command[0].lower()
    
    if cmd == "kick":
        user_id, reason = await extract_user_and_reason(message)
        if not user_id:
            return await message.reply(f"<b>❌ Usage:</b> <code>{cmd} [username/user_id/reply] [reason]</code>")
        if user_id == OWNER_ID:
            return await message.reply(f"<b>❌ Cannot kick bot owner!</b>")
        
        admins = await list_admins(client, message.chat.id)
        if user_id in admins:
            return await message.reply(f"<b>❌ Cannot kick an admin!</b>")
        
        try:
            user = await client.get_users(user_id)
            mention = user.mention
            username = f"@{user.username}" if user.username else "No username"
            user_id_display = user.id
        except Exception as error:
            return await message.reply(str(error))
        
        admin_user = await client.get_users(message.from_user.id)
        admin_username = f"@{admin_user.username}" if admin_user.username else message.from_user.mention
        
        msg = f"""
<b>🚫 SUCCESS KICKED MEMBER</b>
╰ {username}

<b>🆔 ID User:</b> <code>{user_id_display}</code>
<b>👮 Admin:</b> {admin_username}
<b>📝 Reason:</b> {reason}
━━━━━━━━━━━━━━━━━━❍
<b><blockquote>✨ Power By Fanzy Userbot</blockquote></b>
        """
        try:
            await message.chat.ban_member(user_id)
            await message.reply(msg)
            await asyncio.sleep(1)
            await message.chat.unban_member(user_id)
        except Exception as error:
            await message.reply(str(error))
            
    elif cmd == "ban":
        user_id, reason = await extract_user_and_reason(message)
        if not user_id:
            return await message.reply(f"<b>❌ Usage:</b> <code>{cmd} [username/user_id/reply] [reason]</code>")
        if user_id == OWNER_ID:
            return await message.reply(f"<b>❌ Cannot ban bot owner!</b>")
        
        admins = await list_admins(client, message.chat.id)
        if user_id in admins:
            return await message.reply(f"<b>❌ Cannot ban an admin!</b>")
        
        try:
            user = await client.get_users(user_id)
            mention = user.mention
            username = f"@{user.username}" if user.username else "No username"
            user_id_display = user.id
        except Exception as error:
            return await message.reply(str(error))
        
        admin_user = await client.get_users(message.from_user.id)
        admin_username = f"@{admin_user.username}" if admin_user.username else message.from_user.mention
        
        msg = f"""
<b>🚫 SUCCESS BANNED USERS</b>
╰ {username}

<b>🆔 ID User:</b> <code>{user_id_display}</code>
<b>👮 Admin:</b> {admin_username}
<b>📝 Reason:</b> {reason}
━━━━━━━━━━━━━━━━━━❍
<b><blockquote>✨ Power By Fanzy Userbot</blockquote></b>
        """
        try:
            await message.chat.ban_member(user_id)
            await message.reply(msg)
        except Exception as error:
            await message.reply(str(error))
            
    elif cmd == "mute":
        user_id, reason = await extract_user_and_reason(message)
        if not user_id:
            return await message.reply(f"<b>❌ Usage:</b> <code>{cmd} [username/user_id/reply] [reason]</code>")
        if user_id == OWNER_ID:
            return await message.reply(f"<b>❌ Cannot mute bot owner!</b>")
        
        admins = await list_admins(client, message.chat.id)
        if user_id in admins:
            return await message.reply(f"<b>❌ Cannot mute an admin!</b>")
        
        try:
            user = await client.get_users(user_id)
            mention = user.mention
            username = f"@{user.username}" if user.username else "No username"
            user_id_display = user.id
        except Exception as error:
            return await message.reply(str(error))
        
        admin_user = await client.get_users(message.from_user.id)
        admin_username = f"@{admin_user.username}" if admin_user.username else message.from_user.mention
        
        msg = f"""
<b>🚫 SUCCESS MUTE MEMBER</b>
╰ {username}

<b>🆔 ID User:</b> <code>{user_id_display}</code>
<b>👮 Admin:</b> {admin_username}
<b>📝 Reason:</b> {reason}
━━━━━━━━━━━━━━━━━━❍
<b><blockquote>✨ Power By Fanzy Userbot</blockquote></b>
        """
        try:
            await message.chat.restrict_member(user_id, ChatPermissions())
            await message.reply(msg)
        except Exception as error:
            await message.reply(str(error))
            
    elif cmd == "unmute":
        user_id, reason = await extract_user_and_reason(message)
        if not user_id:
            return await message.reply(f"<b>❌ Usage:</b> <code>{cmd} [username/user_id/reply] [reason]</code>")
        
        try:
            user = await client.get_users(user_id)
            username = f"@{user.username}" if user.username else "No username"
            user_id_display = user.id
        except Exception as error:
            return await message.reply(str(error))
        
        admin_user = await client.get_users(message.from_user.id)
        admin_username = f"@{admin_user.username}" if admin_user.username else message.from_user.mention
        
        reason = reason if reason else "No reason provided"
        
        msg = f"""
<b>✅ SUCCESS UNMUTE USERS</b>
╰ {username}

<b>🆔 ID User:</b> <code>{user_id_display}</code>
<b>👮 Admin:</b> {admin_username}
<b>📝 Reason:</b> {reason}
━━━━━━━━━━━━━━━━━━❍
<b><blockquote>✨ Power By Fanzy Userbot</blockquote></b>
        """
        try:
            await message.chat.unban_member(user_id)
            await message.reply(msg)
        except Exception as error:
            await message.reply(str(error))
            
    elif cmd == "unban":
        user_id, reason = await extract_user_and_reason(message)
        if not user_id:
            return await message.reply(f"<b>❌ Usage:</b> <code>{cmd} [username/user_id/reply] [reason]</code>")
        
        try:
            user = await client.get_users(user_id)
            username = f"@{user.username}" if user.username else "No username"
            user_id_display = user.id
        except Exception as error:
            return await message.reply(str(error))
        
        admin_user = await client.get_users(message.from_user.id)
        admin_username = f"@{admin_user.username}" if admin_user.username else message.from_user.mention
        
        reason = reason if reason else "No reason provided"
        
        msg = f"""
<b>✅ SUCCESS UNBAN MEMBER</b>
╰ {username}

<b>🆔 ID User:</b> <code>{user_id_display}</code>
<b>👮 Admin:</b> {admin_username}
<b>📝 Reason:</b> {reason}
━━━━━━━━━━━━━━━━━━❍
<b><blockquote>✨ Power By Fanzy Userbot</blockquote></b>
        """
        try:
            await message.chat.unban_member(user_id)
            await message.reply(msg)
        except Exception as error:
            await message.reply(str(error))


# ============================================
# ATMIN (PROMOTE)
# ============================================
@PY.UBOT("atmin")
@PY.TOP_CMD
async def atmin_handler(client: Client, message: Message):
    ggl = await EMO.GAGAL(client)
    sks = await EMO.BERHASIL(client)
    prs = await EMO.PROSES(client)
    
    if not await is_group(message.chat):
        return await message.reply(f"<b>❌ This command can only be used in groups!</b>")
    
    if not await is_admin_bot(client, message.chat.id):
        return await message.reply(f"<b>❌ Bot must be an admin first!</b>")
    
    user_id = await extract_user(message)
    anu = await eor(message, f"{prs} <b>Processing...</b>")
    
    if not user_id:
        return await anu.edit(f"<b>❌ User not found!</b>")
    
    try:
        await message.chat.promote_member(
            user_id,
            privileges=ChatPrivileges(
                can_manage_chat=True,
                can_delete_messages=True,
                can_manage_video_chats=True,
                can_restrict_members=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=True,
                can_promote_members=False,
            ),
        )
        await asyncio.sleep(1)
        umention = (await client.get_users(user_id)).mention
        return await anu.edit(f"<b>✅ Successfully promoted {umention} to admin!</b>")
    except ChatAdminRequired:
        await anu.edit(f"<b>❌ You are not an admin in this group!</b>")
    except Exception as error:
        await anu.edit(f"<b>❌ Error: {error}</b>")


# ============================================
# CEO (PROMOTE FULL)
# ============================================

@PY.UBOT("ceo")
@PY.TOP_CMD
async def ceo_handler(client: Client, message: Message):
    ggl = await EMO.GAGAL(client)
    sks = await EMO.BERHASIL(client)
    prs = await EMO.PROSES(client)
    
    if not await is_group(message.chat):
        return await message.reply(f"<b>❌ This command can only be used in groups!</b>")
    
    if not await is_admin_bot(client, message.chat.id):
        return await message.reply(f"<b>❌ Bot must be an admin first!</b>")
    
    user_id = await extract_user(message)
    anu = await eor(message, f"{prs} <b>Processing...</b>")
    
    if not user_id:
        return await anu.edit(f"<b>❌ User not found!</b>")
    
    try:
        await message.chat.promote_member(
            user_id,
            privileges=ChatPrivileges(
                can_manage_chat=True,
                can_delete_messages=True,
                can_manage_video_chats=True,
                can_restrict_members=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_promote_members=True,
            ),
        )
        await asyncio.sleep(1)
        umention = (await client.get_users(user_id)).mention
        return await anu.edit(f"<b>✅ Successfully promoted {umention} to co-admin!</b>")
    except ChatAdminRequired:
        await anu.edit(f"<b>❌ You are not an admin in this group!</b>")
    except Exception as error:
        await anu.edit(f"<b>❌ Error: {error}</b>")


# ============================================
# GET LINK
# ============================================

@PY.UBOT("getlink")
@PY.TOP_CMD
async def getlink_handler(client, message):
    ggl = await EMO.GAGAL(client)
    sks = await EMO.BERHASIL(client)
    
    if not await is_group(message.chat):
        return await message.reply(f"<b>❌ This command can only be used in groups!</b>")
    
    try:
        link = await client.export_chat_invite_link(message.chat.id)
        await message.reply(f"<b>🔗 Group Link:</b>\n<code>{link}</code>", disable_web_page_preview=True)
    except Exception as e:
        await message.reply(f"<b>❌ Error: {e}</b>")


# ============================================
# Kicx
# ============================================

@PY.UBOT("kicx")
@PY.TOP_CMD
@PY.GROUP
async def zombies_handler(client, message):
    if not await is_group(message.chat):
        return await message.reply("<b>❌ This command can only be used in groups!</b>")
    
    if not await is_admin_bot(client, message.chat.id):
        return await message.reply("<b>❌ Bot must be an admin first!</b>")    
    chat_id = message.chat.id
    deleted_users = []
    banned_users = 0
    Tm = await message.reply("<b>🔍 Checking for deleted accounts...</b>")    
    async for i in client.get_chat_members(chat_id):
        if i.user.is_deleted:
            deleted_users.append({
                'id': i.user.id,
                'first_name': i.user.first_name or "Unknown",
                'username': f"@{i.user.username}" if i.user.username else "No username"
            })  
    if len(deleted_users) > 0:
        admin_user = await client.get_users(message.from_user.id)
        admin_username = f"@{admin_user.username}" if admin_user.username else message.from_user.mention        
        for deleted_user in deleted_users:
            try:
                await message.chat.ban_member(deleted_user['id'])
                banned_users += 1
                await asyncio.sleep(0.5)
            except Exception:
                pass        
        deleted_list = "\n".join([f"╰ {user['username']}" for user in deleted_users[:20]])
        if len(deleted_users) > 10:
            deleted_list += f"\n╰ <i>and {len(deleted_users) - 10} more...</i>"
        
        msg = f"✅ berhasil mengelurkan {banned_users} akun terhapus dari group ini"
        await Tm.edit(msg)
    else:
        msg = f"❌ tidak ada akun terhapus! "
        await Tm.edit(msg)


# ============================================
# demote (DEMOTE)
# ============================================
@PY.UBOT("demote")
@PY.TOP_CMD
async def unatmin_handler(client: Client, message: Message):
    if not await is_group(message.chat):
        return await message.reply("<b>❌ This command can only be used in groups!</b>")    
    if not await is_admin_bot(client, message.chat.id):
        return await message.reply("<b>❌ Bot must be an admin first!</b>")    
    user_id = await extract_user(message)
    sempak = await eor(message, "<b>⏳ Processing...</b>")    
    if not user_id:
        return await sempak.edit("<b>❌ User not found!</b>")    
    if user_id == client.me.id:
        return await sempak.edit("<b>❌ Cannot demote myself!</b>")    
    if user_id == OWNER_ID:
        return await sempak.edit("<b>❌ Cannot demote bot owner!</b>")    
    try:
        target_member = await client.get_chat_member(message.chat.id, user_id)
        target_status = target_member.status        
        if target_status not in [ChatMemberStatus.ADMINISTRATOR]:
            return await sempak.edit("<b>❌ User is not an admin!</b>")        
    except Exception as e:
        return await sempak.edit(f"<b>❌ Error: {e}</b>")    
    try:
        user = await client.get_users(user_id)
        username = f"@{user.username}" if user.username else "No username"
        user_id_display = user.id        
        admin_user = await client.get_users(message.from_user.id)
        admin_username = f"@{admin_user.username}" if admin_user.username else message.from_user.mention        
        await message.chat.promote_member(
            user_id,
            privileges=ChatPrivileges(
                can_manage_chat=False,
                can_delete_messages=False,
                can_manage_video_chats=False,
                can_restrict_members=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
                can_promote_members=False,
            ),
        )
        await asyncio.sleep(1)
        
        msg = f"""
<b>📉 SUCCESS DEMOTED USER</b>
╰ {username}

<b>🆔 ID User:</b> <code>{user_id_display}</code>
<b>👮 Admin:</b> {admin_username}
━━━━━━━━━━━━━━━━━━❍
<b><blockquote>✨ Power By Fanzy Userbot</blockquote></b>
        """
        await sempak.edit(msg)
        
    except ChatAdminRequired:
        await sempak.edit("<b>❌ You are not an admin in this group!</b>")
    except Exception as error:
        await sempak.edit(f"<b>❌ Error: {error}</b>")

# ============================================
# KONFIGURASI & WHITELIST
# ============================================
WHITELIST_GROUPS = [
    -1001234567890, 
    -1009876543210
]

# ===========================================
# COMMAND CONTROL (ON/OFF)
# ============================================
@PY.UBOT("antilink|antipromosi|antiforward")
@PY.TOP_CMD
@PY.GROUP
async def anti_spams_toggle(client, message):
    if len(message.command) < 2:
        return await message.reply(f"<b>❌ Gunakan format:</b> <code>{message.command[0]} on/off</code>")    
    cmd = message.command[0].lower()
    state = message.command[1].lower().strip()
    chat_id = message.chat.id
    if state not in ["on", "off"]:
        return await message.reply("<b>❌ Gunakan 'on' atau 'off' saja, Puh!</b>")
    key = f"{cmd.upper()}_{chat_id}"
    await set_vars(client.me.id, key, state)
    text_ux = {
        "antilink": "Anti-Link",
        "antipromosi": "Anti-Promosi",
        "antiforward": "Anti-Forward"
    }
    await message.reply(f"<b>✅ Berhasil mengubah {text_ux.get(cmd)} menjadi {state.upper()} di grup ini!</b>")

# ============================================
# MAIN HANDLER (LISTENER)
# ============================================
@PY.UBOT(".*", filters.group & ~filters.me)
async def anti_all_handler(client, message):
    if not message or not message.from_user or message.from_user.is_self:
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    if chat_id in WHITELIST_GROUPS:
        return    
    is_admin = False
    if user_id == OWNER_ID:
        is_admin = True
    else:
        try:
            member = await client.get_chat_member(chat_id, user_id)
            if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                is_admin = True
        except Exception as e:
            is_admin = False
    if is_admin:
        return
    link_stat = await get_vars(client.me.id, f"ANTILINK_{chat_id}")
    promo_stat = await get_vars(client.me.id, f"ANTIPROMOSI_{chat_id}")
    forward_stat = await get_vars(client.me.id, f"ANTIFORWARD_{chat_id}")
    delete_msg = False
    reason = ""
    if str(forward_stat).lower() == "on":
        if message.forward_from or message.forward_from_chat or message.forward_sender_name:
            delete_msg = True
            reason = "Dilarang Forward!"
    if not delete_msg and str(link_stat).lower() == "on":
        if message.entities:
            for entity in message.entities:
                if entity.type in [MessageEntityType.URL, MessageEntityType.TEXT_LINK, MessageEntityType.MENTION]:
                    delete_msg = True
                    reason = "Dilarang Share Link!"
                    break
    if not delete_msg and str(promo_stat).lower() == "on":
        DEFAULT_KEYWORDS = ["sell", "vps", "SELL", "VPS", "list", "LIST", "panel", "PANEL", " OPEN OWN HARGA", "Open", "Pterodactyl", "halo kak", "lagi", "butuh", "Neet", "Vps Legal", "Spek", "Neet", "nokos wa dan telegram", "noktel", "nokwa", "nokos", "neet nokos", "buy", " channel", "dibayo", "bokep", "vip", "partner", "benefit", "keuntungan", "━━━━━━━", "1k", "000", "k", "IDR", "bot", " BOT", "ADA", "Yang", "Mau", "Jaseb", "Ubot Jaseb", "Testimoni", "Testi", "New", "Rilis", "Harga", "Free", " free", "Legal", "Ocean", "Vps", "Droplet", "Sloot", "Auto Sebar", "Like", "Suntik", "Sosmed", "Rm", "Gb", "C", "Penyetor", "Shop", "Shopp", "Storee", "Store", "Anggota", "Tawarin", "Sc", "SC", "Info", "INFO", "Informasi", "Harga Update", "Butuh", "Duit", "List Daftar", "List", "list", "L i s t", "Ready", "Pm", "Chip", "Role", "By", "Resseller", "Admin", "Owner", "Founder", "Reseller", "Sewa", "Mau", "Booking", "Vidio Pribadi", "🚀", "Vvip", " Murmer", "murmer", "unban", "WhatsApp", "wa", "whatsapp", "?", "!", "Butuh", "Duit", "Bingung Nyari Akun", "akun", "Akun", "Produxt", "All", "all", "ocill", "free", "di biyo", "dibiyo", "Rp", "rp", "Official", "OFFC", "OFFICIAL", "Murbug", "murbug", "@", "t.me//", "pv", "cpv", "P V", "p v", "c p v", "script", "keuntungan", "!!!", "!!", "/", ":", "base", "nya", "dari", "gue", "b.u.y. b.o.k.e.p. a.j.a.", "Buy Bokep Aja", "👋", "install", "full", "protect", "baru", "stok", "Ml", "ML", "mL", "ml", "ff", "free fire", "Ff", "Pubg", "pubg", "Jb", "jb", "game", "Game", "Unchek", "ft", "ke", "KE", "murah"]        
        FINAL_KEYWORDS = DEFAULT_KEYWORDS + ADDITIONAL_KEYWORDS
        content = (message.text or message.caption or "").lower()
        if any(word in content for word in FINAL_KEYWORDS):
            delete_msg = True
            reason = "Dilarang Promosi!"           
    if delete_msg:
        try:
            await message.delete()           
            warn_msg = f"""
<blockquote><b>⚠️ KEMAAN GROUP AKTIF</b></blockquote>          
<blockquote><b>📛 {reason}\n<b>👤 User:</b> {message.from_user.mention}</b></blockquote>
"""
            warn = await message.reply(warn_msg)
            await asyncio.sleep(8)
            await warn.delete()           
        except Exception as e:
            print(f"❌ Error Hapus: {e}")        