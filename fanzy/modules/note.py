import re
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from pyrogram.types import *
from fanzy import *

__MODULE__ = "Note"
__HELP__ = """
<b>📁 NOTE TOOLS</b>

<b>🔧 Commands:</b>
├ <code>{0}addnote</code> - Add note
├ <code>{0}addcb</code> - Add callback note
├ <code>{0}get</code> - Get note
├ <code>{0}delnote</code> - Delete note
├ <code>{0}delcb</code> - Delete callback
├ <code>{0}listnote</code> - List all notes
└ <code>{0}listcb</code> - List all callbacks
"""

def create_inline_keyboard(text, callback_prefix="note"):
    buttons = []
    lines = text.split('\n')
    clean_lines = []    
    pattern = r'\|\s*([^|]+?)\s*-\s*([^|]+?)\s*\|'    
    for line in lines:
        matches = re.findall(pattern, line)        
        if matches:
            row = []
            for btn_text, btn_data in matches:
                btn_text = btn_text.strip()
                btn_data = btn_data.strip()                
                if btn_data.startswith(("http://", "https://", "t.me/")):
                    row.append(InlineKeyboardButton(btn_text, url=btn_data))
                else:
                    if not btn_data.startswith(callback_prefix):
                        btn_data = f"{callback_prefix}_{btn_data}"
                    row.append(InlineKeyboardButton(btn_text, callback_data=btn_data))            
            if row:
                buttons.append(row)            
            clean_line = re.sub(pattern, '', line).strip()
            if clean_line:
                clean_lines.append(clean_line)
        else:
            clean_lines.append(line)   
    clean_text = '\n'.join(clean_lines).strip()
    if not clean_text:
        clean_text = "📋 Pilih menu:"    
    if buttons:
        return InlineKeyboardMarkup(buttons), clean_text    
    return None, text

@PY.UBOT("addnote|addcb")
@PY.TOP_CMD
async def _(client, message):
    brhsl = await EMO.BERHASIL(client)
    ggl = await EMO.GAGAL(client)
    
    if len(message.command) != 2:
        return await message.reply(
            f"<b>❌ Usage Error!</b>\n\n"
            f"<b>📌 Format:</b> <code>{message.text.split()[0]} [name]</code>\n"
            f"<b>📝 Example:</b> <code>{message.text.split()[0]} mynote</code>\n"
        )
    
    args = get_arg(message)
    reply = message.reply_to_message
    query = "notes_cb" if message.command[0] == "addcb" else "notes"

    if not args or not reply:
        return await message.reply(
            f"<b>❌ Missing Parameters!</b>\n\n"
            f"<b>╰📌 Format:</b> <code>{message.text.split()[0]} [name]</code>\n"
        )

    vars_data = await get_vars(client.me.id, args, query)

    if vars_data:
        return await message.reply(
            f"<b>❌ Note Already Exists!</b>\n\n"
            f"<b>╰📌 Name:</b> <code>{args}</code>\n"
            f"<blockquote>⚡ Power By Fanzy Userbot</blockquote>"
        )

    value = None
    type_mapping = {
        "text": reply.text,
        "photo": reply.photo,
        "voice": reply.voice,
        "audio": reply.audio,
        "video": reply.video,
        "animation": reply.animation,
        "sticker": reply.sticker,
    }

    for media_type, media in type_mapping.items():
        if media:
            send = await reply.copy(client.me.id)
            value = {
                "type": media_type,
                "message_id": send.id,
            }
            break

    if value:
        await set_vars(client.me.id, args, value, query)
        await message.reply(
            f"<b>✅ Succesfully Add catatan</b>\n\n"
            f"<b>├📌 Name:</b> <code>{args}</code>\n"
            f"<b>╰📝 Type:</b><code>{media_type}</code>\n"
            f"<blockquote>⚡ Power By Fanzy Userbot</blockquote>"
        )
    else:
        await message.reply(
            f"<b>❌ Failed to Save!</b>\n\n"
            f"<b>├📌 Format:</b> <code>{message.text.split()[0]} [name]</code>\n"
            f"<b>╰📌 Reply:</b> Reply to a message\n"
            f"<blockquote>⚡ Power By Fanzy Userbot</blockquote>"
        )

@PY.UBOT("delnote|delcb")
@PY.TOP_CMD
async def _(client, message):
    brhsl = await EMO.BERHASIL(client)
    ggl = await EMO.GAGAL(client)
    args = get_arg(message)
    if not args:
        return await message.reply(
            f"<b>❌ Usage Error!</b>\n\n"
            f"<b>📌 Format:</b> <code>{message.text.split()[0]} [name]</code>\n"
            f"<b>📝 Example:</b> <code>{message.text.split()[0]} mynote</code>\n"
            f"<blockquote>⚡ Power By Fanzy Userbot</blockquote>"
        )
    query = "notes_cb" if message.command[0] == "delcb" else "notes"
    vars_data = await get_vars(client.me.id, args, query)
    if not vars_data:
        return await message.reply(
            f"<b>❌ Catatan Not Found!</b>\n\n"
            f"<b>╰📌 Name:</b> <code>{args}</code>\n"
            f"<blockquote>⚡ Power By Fanzy Userbot</blockquote>"
        )
    await remove_vars(client.me.id, args, query)
    await client.delete_messages(client.me.id, int(vars_data["message_id"]))    
    await message.reply(
        f"<b>✅ Succesfuly delete Catatan</b>\n\n"
        f"<b>╰📌 Name:</b> <code>{args}</code>\n"
        f"<blockquote>⚡ Power By Fanzy Userbot</blockquote>"
    )

@PY.UBOT("get")
@PY.TOP_CMD
async def _(client, message):
    ggl = await EMO.GAGAL(client)
    msg = message.reply_to_message or message
    args = get_arg(message)
    if not args:
        return await message.reply(
            f"<b>❌ Usage Error!</b>\n\n"
            f"<b>📌 Format:</b> <code>get [name]</code>"
        )
    data = await get_vars(client.me.id, args, "notes")
    if not data:
        return await message.reply(f"<b>❌ Note Not Found!</b>")
    m = await client.get_messages(client.me.id, int(data["message_id"]))
    if data["type"] == "text":
        if re.search(r"\|\s*([^|]+?)\s*-\s*([^|]+?)\s*\|", m.text):
            try:
                x = await client.get_inline_bot_results(
                    bot.me.username, f"get_notes {client.me.id} {args}"
                )
                return await client.send_inline_bot_result(
                    message.chat.id,
                    x.query_id,
                    x.results[0].id,
                    reply_to_message_id=msg.id,
                )
            except Exception as error:
                await message.reply(f"❌ Error Inline: {error}")
        else:
            return await m.copy(message.chat.id, reply_to_message_id=msg.id)
    else:
        return await m.copy(message.chat.id, reply_to_message_id=msg.id)
            
@PY.UBOT("listnote|listcb")
@PY.TOP_CMD
async def _(client, message):
    query = "notes_cb" if message.command[0] == "listcb" else "notes"    
    vars_data = await all_vars(client.me.id, query)    
    title = "CALLBACK LIST" if query == "notes_cb" else "NOTE LIST"
    text = f"<b>📋 {title}</b>\n\n"    
    if vars_data:
        for name, data in vars_data.items():
            text += f"├ <code>{name}</code> │ {data.get('type', 'unknown')}\n"        
        text += f"\n<b>📊 Total:</b> <code>{len(vars_data)}</code>\n"
    else:
        text += f"╰ <b>You have no records!</b>\n"    
    text += f"━━━━━━━━━━━━━━━━━━❍\n"
    text += f"<blockquote>⚡ Power By Fanzy Userbot</blockquote>"
    await message.reply(text, quote=True)

@PY.INLINE("^get_notes")
async def _(client, inline_query):
    query = inline_query.query.split()
    user_id = int(query[1])
    note_name = query[2]    
    data = await get_vars(user_id, note_name, "notes")    
    item = [x for x in ubot._ubot if user_id == x.me.id]
    for me in item:
        m = await me.get_messages(me.me.id, int(data["message_id"]))        
        buttons, text = create_inline_keyboard(m.text, "note")        
        return await client.answer_inline_query(
            inline_query.id,
            cache_time=0,
            results=[
                InlineQueryResultArticle(
                    title="Get Notes!",
                    reply_markup=buttons,
                    input_message_content=InputTextMessageContent(text),
                )
            ],
        )
        
@PY.CALLBACK("_gtnote")
async def _(client, callback_query):
    _, user_id, *query = callback_query.data.split()
    data_key = "notes_cb" if bool(query) else "notes"
    query_split = query[0] if bool(query) else user_id.split("_")[1]
    data = await get_vars(int(user_id.split("_")[0]), query_split, data_key)
    item = [x for x in ubot._ubot if int(user_id.split("_")[0]) == x.me.id]
    for me in item:
        try:
            m = await me.get_messages(int(me.me.id), int(data["message_id"]))
            buttons, text = create_inline_keyboard(
                m.text, f"{int(user_id.split('_')[0])}_{user_id.split('_')[1]}", bool(query)
            )
            await callback_query.edit_message_text(text, reply_markup=buttons)
        except TypeError:
            await callback_query.answer("❌ Something went wrong!", show_alert=True)

@PY.CALLBACK("^note_")
async def universal_callback_handler(client, callback_query):
    data = callback_query.data
    callback_id = data.replace("note_", "")
    note_data = await get_vars(client.me.id, callback_id, "notes")    
    if note_data:
        m = await client.get_messages(client.me.id, int(note_data["message_id"]))
        await callback_query.edit_message_text(m.text)
        await callback_query.answer(f"✅ Menampilkan: {callback_id}")
    else:
        await callback_query.answer(f"{callback_id}", show_alert=True)
