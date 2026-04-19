import asyncio

from pyrogram import Client, filters
from pyrogram.types import Message
from fanzy.core.helpers.msg_type import ReplyCheck
from fanzy import *

@ubot.on_message(filters.command("unprem") & filters.me)
async def jwbsalamlngkp(client: Client, message: Message):
    await asyncio.gather(
        message.delete(),
        client.send_message(
            message.chat.id,
            "<b>❌ Usage:</b> <code>unprem [username/user_id]</code>",
            reply_to_message_id=ReplyCheck(message),
        ),
    )

@PY.BOT("bc")
@PY.OWNER
async def broadcast_bot(client, message):
    msg = await message.reply("<b>⏳ Processing...</b>", quote=True)
    done = 0
    if not message.reply_to_message:
        return await msg.edit("<b>❌ Please reply to a message!</b>")
    for x in ubot._ubot:
        try:
            await x.unblock_user(bot.me.username)
            await message.reply_to_message.forward(x.me.id)
            done += 1
        except Exception:
            pass
    
    result_msg = f"""
<blockquote><b>📡 SUCCESFULLY GCAST BOT</b></blockquote>
✅ Berhasil kirim ke {done} pengguna
<blockquote><b>✨ Power By Fanzy Userbot</b></blockquote>
"""
    return await msg.edit(result_msg)