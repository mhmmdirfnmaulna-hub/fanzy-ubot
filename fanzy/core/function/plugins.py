import importlib
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from fanzy import bot, ubot
from fanzy.core.helpers import PY
from fanzy.modules import loadModule
from fanzy.core.database import *
from fanzy.config import OWNER_ID
from platform import python_version
from pyrogram import __version__

HELP_COMMANDS = {}

# ============================================
# FUNGSI PEMBANTU FORMAT
# ============================================

def fmt_bot():
    """Format mention bot"""
    return f"<a href=tg://user?id={bot.me.id}>{bot.me.first_name}</a>"

# ============================================
# LOAD PLUGINS
# ============================================

async def loadPlugins():
    modules = loadModule()
    for mod in modules:
        imported_module = importlib.import_module(f"fanzy.modules.{mod}")
        module_name = getattr(imported_module, "__MODULE__", "").replace(" ", "_").lower()
        if module_name:
            HELP_COMMANDS[module_name] = imported_module
    
    print(f"[✅ @{bot.me.username}] [ONLINE]")
    
    # Kirim notifikasi ke owner
    await bot.send_message(
        OWNER_ID,
        f"""
<blockquote>
╭ 🤖 <b>USERBOT DIAKTIFKAN!</b>
├ 📁 <b>Modules :</b> {len(HELP_COMMANDS)}
├ 🐍 <b>Versi Python :</b> {python_version()}
├ ✈️ <b>Versi Pyrogram :</b> {__version__}
╰ 👤 <b>Total Userbot :</b> {len(ubot._ubot)}
</blockquote>
""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 List Userbot", callback_data="cek_ubot")],
        ]),
    )

# ============================================
# CLOSE CALLBACK
# ============================================

@PY.CALLBACK("0_cls")
async def _(client, callback_query):
    await callback_query.message.delete()