# modules/alive_help.py
import struct
import random
import re
import os
import platform
import subprocess
import sys
import traceback
import asyncio
from datetime import datetime
from io import BytesIO, StringIO
from time import time
import psutil
from pyrogram.raw.functions import Ping
from pyrogram.types import *
from platform import python_version
from pyrogram import __version__
import time
from fanzy import *
from fanzy.config import OWNER_ID, OWNER_NAME, OWNER_LINK
start_time = time.time() 
# ============================================
# FUNGSI PEMBANTU
# ============================================

def fmt_user(user):
    try:
        if user.username:
            return f"@{user.username}"
        else:
            name = f"{user.first_name} {user.last_name or ''}".strip()
            if len(name) > 15:
                name = name[:12] + "..."
            return name
    except Exception:
        return "Unknown"

def fmt_id(user):
    try:
        return f"<a href=tg://user?id={user.id}>{fmt_user(user)}</a>"
    except Exception:
        return "User Error"
async def get_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "d"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and count == 1:
            return "0s"
        if result != 0:
            time_list.append(str(int(result)) + time_suffix_list[count - 1])
        seconds = int(remainder)
    for i in range(len(time_list)):
        up_time += time_list[len(time_list) - i - 1] + " "
    return up_time.strip()
            
# ============================================
# ALIVE
# ============================================

@PY.UBOT("alive")
@PY.TOP_CMD
async def _(client, message):
    try:
        x = await client.get_inline_bot_results(
            bot.me.username, f"alive {message.id} {client.me.id}"
        )
        await message.reply_inline_bot_result(x.query_id, x.results[0].id, quote=True)
    except Exception as error:
        try:
            await message.reply(f"❌ Error Alive: {error}")
        except:
            pass


@PY.INLINE("^alive")
async def _(client, inline_query):
    try:
        get_id = inline_query.query.split()
        for my in ubot._ubot:
            if int(get_id[2]) == my.me.id:
                try:
                    peer = my._get_my_peer[my.me.id]
                    users = len(peer["pm"])
                    group = len(peer["gc"])
                except Exception:
                    try:
                        users = await my.get_dialogs_count()
                        group = random.randrange(users) # fallback random
                    except:
                        users, group = 0, 0
                
                try:
                    get_exp = await get_expired_date(my.me.id)
                    exp = get_exp.strftime("%d-%m-%Y") if get_exp else "None"
                except:
                    exp = "Error"
                
                try:
                    if my.me.id in await get_list_from_vars(client.me.id, "ULTRA_PREM"):
                        status = "ULTRA"
                    else:
                        status = "PREMIUM"
                except:
                    status = "MEMBER"
                
                button = BTN.ALIVE(get_id)
                
                start = datetime.now()
                try:
                    await my.invoke(Ping(ping_id=0))
                    ping = (datetime.now() - start).microseconds / 1000
                except:
                    ping = "N/A"

                try:
                    uptime = await get_time(int(time.time() - start_time))
                except:
                    uptime = "N/A"
                
                msg = f"""
<blockquote>
🤖 <b>USERBOT STATUS</b>
━━━━━━━━━━━━━━━━━❍

📊 Status: {status}
⏰ Expired: {exp}
🌐 DC: {my.me.dc_id}
⚡ Ping: {ping} ms
👥 Users: {users}
👥 Groups: {group}
⏱️ Uptime: {uptime}
</blockquote>
"""
                await client.answer_inline_query(
                    inline_query.id,
                    cache_time=1,
                    results=[
                        InlineQueryResultArticle(
                            title="💬 Status Bot",
                            reply_markup=InlineKeyboardMarkup(button),
                            input_message_content=InputTextMessageContent(msg),
                        )
                    ],
                )
    except Exception as e:
        print(f"Inline Alive Error: {e}")


@PY.CALLBACK("alv_cls")
async def _(client, callback_query):
    try:
        get_id = callback_query.data.split()
        if not callback_query.from_user.id == int(get_id[2]):
            return await callback_query.answer("❌ Lu siapa?", True)
        
        unPacked = unpackInlineMessage(callback_query.inline_message_id)
        for my in ubot._ubot:
            if callback_query.from_user.id == int(my.me.id):
                await my.delete_messages(
                    unPacked.chat_id, [int(get_id[1]), unPacked.message_id]
                )
    except Exception as e:
        await callback_query.answer(f"Gagal hapus: {e}", True)


# ============================================
# BOT HELP
# ============================================
@PY.BOT("anu")
@PY.ADMIN
async def _(client, message):
    try:
        buttons = BTN.BOT_HELP(message)
        await message.reply("📋 HELP MENU", reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        await message.reply(f"Error: {e}")


@PY.CALLBACK("balik")
async def _(client, callback_query):
    try:
        buttons = BTN.BOT_HELP(callback_query)
        await callback_query.message.edit("📋 HELP MENU", reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        await callback_query.answer(f"Error: {e}", True)


@PY.CALLBACK("reboot")
async def _(client, callback_query):
    try:
        user_id = callback_query.from_user.id
        if user_id not in await get_list_from_vars(client.me.id, "ADMIN_USERS"):
            return await callback_query.answer("❌ Bukan untukmu!", True)
        
        await callback_query.answer("✅ System restart...", True)
        subprocess.call(["bash", "start.sh"])
    except Exception as e:
        await callback_query.answer(f"Gagal Reboot: {e}", True)


@PY.CALLBACK("update")
async def _(client, callback_query):
    try:
        user_id = callback_query.from_user.id
        if user_id != OWNER_ID:
            return await callback_query.answer("❌ Bukan untukmu!", True)
        
        try:
            out = subprocess.check_output(["git", "pull"]).decode("UTF-8")
        except Exception as e:
            return await callback_query.answer(f"Git Pull Error: {e}", True)

        if "Already up to date." in str(out):
            return await callback_query.answer("✅ Sudah terupdate", True)
        else:
            await callback_query.answer("🔄 Update...", True)
            os.execl(sys.executable, sys.executable, "-m", "fanzy")
    except Exception as e:
        await callback_query.answer(f"Update Error: {e}", True)


# ============================================
# USER HELP
# ============================================
@PY.UBOT("help")
async def user_help(client, message):
    try:
        if not get_arg(message):
            try:
                x = await client.get_inline_bot_results(bot.me.username, "user_help")
                await message.reply_inline_bot_result(x.query_id, x.results[0].id)
            except Exception as error:
                await message.reply(f"Inline Help Error: {error}")
        else:
            module = get_arg(message)
            if module in HELP_COMMANDS:
                prefix = await ubot.get_prefix(client.me.id)
                await message.reply(
                    HELP_COMMANDS[module].__HELP__.format(next((p) for p in prefix)),
                    quote=True,
                )
            else:
                await message.reply(f"❌ Module <code>{module}</code> tidak ditemukan")
    except Exception as e:
        await message.reply(f"Help Error: {e}")


@PY.INLINE("^user_help")
async def user_help_inline(client, inline_query):
    try:
        SH = await ubot.get_prefix(inline_query.from_user.id)
        photo_url = "https://files.catbox.moe/y5yesx.jpg"        
        start = datetime.now()
        await client.invoke(Ping(ping_id=0))
        speed = (datetime.now() - start).microseconds / 1000        
        try:
            uptime = await get_time(int(time.time() - start_time))
        except:
            uptime = "N/A"
        
        caption = f"""
💠 <b>—FANZY USERBOT PREM</b>
  • <b>Total module :</b> {len(HELP_COMMANDS)}
  • <b>Prefixes ubot :</b> [ {' '.join(SH)} ]
  • <b>Uptime :</b> {uptime}
  • <b>Speed :</b> {speed} ms
  • <b>Versi python :</b> {python_version()}
  • <b>Versi pyrogram :</b> {__version__}
  • <b>Owner userbot :</b> <a href="tg://user?id={OWNER_ID}">fanzyん.</a>
<blockquote><b><i>—Power By Fanzy Userbot—</i></b></blockquote>
"""
        results = [
            InlineQueryResultPhoto(
                photo_url=photo_url,
                thumb_url=photo_url,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELP_COMMANDS, "help")
                ),
            )
        ]
        await client.answer_inline_query(inline_query.id, cache_time=60, results=results)
    except Exception as e:
        print(f"Inline Help Error: {e}")


@PY.CALLBACK("^close_user")
async def close_usernya(client, callback_query):
    try:
        inline_id = callback_query.inline_message_id
        if not inline_id:
            return await callback_query.message.delete()        
        unPacked = unpackInlineMessage(inline_id)
        for x in ubot._ubot:
            if callback_query.from_user.id == int(x.me.id):
                try:
                    await x.delete_messages(unPacked.chat_id, unPacked.message_id)
                except:
                    pass
    except (struct.error, Exception):
        try:
            await callback_query.message.delete()
        except:
            await callback_query.answer("❌ Gagal!", show_alert=False)


@PY.CALLBACK("help_(.*?)")
async def help_callback(client, callback_query):
    try:
        mod_match = re.match(r"help_module\((.+?)\)", callback_query.data)
        prev_match = re.match(r"help_prev\((.+?)\)", callback_query.data)
        next_match = re.match(r"help_next\((.+?)\)", callback_query.data)
        back_match = re.match(r"help_back", callback_query.data)
        empty_module_match = re.match(r"help_empty", callback_query.data)                
        SH = await ubot.get_prefix(callback_query.from_user.id)        
        start = datetime.now()
        await client.invoke(Ping(ping_id=0))
        speed = (datetime.now() - start).microseconds / 1000
        try:
            uptime = await get_time(int(time.time() - start_time))
        except:
            uptime = "N/A"

        top_text = f"""
💠 <b>—FANZY USERBOT PREM</b>
  • <b>Total module :</b> {len(HELP_COMMANDS)}
  • <b>Prefixes ubot :</b> [ {' '.join(SH)} ]
  • <b>Uptime :</b> {uptime}
  • <b>Speed :</b> {speed} ms
  • <b>Versi python :</b> {python_version()}
  • <b>Versi pyrogram :</b> {__version__}
  • <b>Owner userbot :</b> <a href="tg://user?id={OWNER_ID}">fanzyん.</a>
<blockquote><b><i>—Power By Fanzy Userbot—</i></b></blockquote>
"""
        if mod_match:
            module_name = mod_match.group(1).replace(" ", "_")
            text = HELP_COMMANDS[module_name].__HELP__.format(next((p) for p in SH))
            button = [[InlineKeyboardButton("🔙 Back", callback_data="help_back")]]
            await callback_query.edit_message_caption(
                caption=text + f'\n<blockquote><b>ᖫ fanzy userbot-premium ᖭ</b></blockquote>',
                reply_markup=InlineKeyboardMarkup(button),
            )
        elif prev_match:
            curr_page = int(prev_match.group(1))
            await callback_query.edit_message_caption(
                caption=top_text,
                reply_markup=InlineKeyboardMarkup(paginate_modules(curr_page - 1, HELP_COMMANDS, "help")),
            )
        elif next_match:
            next_page = int(next_match.group(1))
            await callback_query.edit_message_caption(
                caption=top_text,
                reply_markup=InlineKeyboardMarkup(paginate_modules(next_page + 1, HELP_COMMANDS, "help")),
            )
        elif empty_module_match:
            await callback_query.answer("❌ Modul kosong!", show_alert=True)
        elif back_match:
            keyboard = paginate_modules(0, HELP_COMMANDS, "help")
            await callback_query.edit_message_caption(
                caption=top_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
    except Exception as e:
        await callback_query.answer(f"Callback Help Error: {e}", True)



# ============================================
# RESTART
# ============================================
@PY.UBOT("restart")
@PY.TOP_CMD
async def _(client, message):
    try:
        prs = await EMO.PROSES(client)
        msg = await message.reply(f"{prs} Restart...")
        await asyncio.sleep(1)
        os.execl(sys.executable, sys.executable, "-m", "fanzy")
    except Exception as e:
        await message.reply(f"❌ Gagal Restart: {e}")


# ============================================
# UPDATE
# ============================================
@PY.UBOT("update")
@PY.TOP_CMD
async def _(client, message):
    try:
        prs = await EMO.PROSES(client)
        msg = await message.reply(f"{prs} Memeriksa update...")        
        try:
            out = subprocess.check_output(["git", "pull"]).decode("UTF-8")
        except Exception as e:
            return await msg.edit(f"❌ Git Error: {e}")
        if "Already up to date." in str(out):
            await msg.edit("✅ <b>Sudah menggunakan versi terbaru!</b>")
        else:
            await msg.edit("🔄 <b>Update ditemukan! Menarik data dan merestart...</b>")
            await asyncio.sleep(2)
            os.execl(sys.executable, sys.executable, "-m", "fanzy")
    except Exception as e:
        try:
            await message.reply(f"❌ Gagal Update: {e}")
        except:
            pass