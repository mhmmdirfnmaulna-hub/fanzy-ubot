from platform import python_version
from pyrogram import __version__
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from fanzy import OWNER_ID, OWNER_NAME, OWNER_USERNAME, OWNER_LINK, bot, ubot, get_expired_date

# ============================================
# FUNGSI PEMBANTU FORMAT
# ============================================

def fmt_user(user):
    if user.username:
        return f"@{user.username}"
    else:
        name = f"{user.first_name} {user.last_name or ''}".strip()
        if len(name) > 15:
            name = name[:12] + "..."
        return name

def fmt_id(user):
    return f"<a href=tg://user?id={user.id}>{fmt_user(user)}</a>"

def fmt_bot():
    return f"<a href=tg://user?id={bot.me.id}>{bot.me.first_name}</a>"

# ============================================
# CLASS MSG
# ============================================

class MSG:
    
    # ========== EXPIRED MSG ==========
    def EXP_MSG_UBOT(X):
        return f"""
<blockquote>
⚠️ <b>USERBOT EXPIRED</b>

👤 {fmt_id(X.me)}
🆔 <code>{X.me.id}</code>

Masa aktif telah habis
━━━━━━━━━━━━━━━━━━━━━❍</blockquote>
"""

    # ========== START MSG ==========
    def START(message):
        user = message.from_user
        return f"""
<blockquote>
👋 <b>OLA {fmt_id(user)}</b>

@{bot.me.username} adalah bot pembuat userbot mudah, cepat, dan efisien

╭──<b>INFORMASI</b>
├ 👑 Owner: {OWNER_USERNAME}
├ 📘 Python: {python_version()}
├ 📙 Pyrogram: {__version__}
╰ 👤 Userbot: {len(ubot._ubot)}

<b><i>--- ✨ Development By Fanzy ---</i></b>
</blockquote>
"""

    # ========== UBOT LIST ==========
    @staticmethod
    async def UBOT(count):
        if not ubot._ubot or len(ubot._ubot) <= int(count):
            return """
<blockquote>
🤖 <b>DAFTAR USERBOT</b>
└  Kosong
</blockquote>
"""
        ubot_data = ubot._ubot[int(count)]
        return f"""
<blockquote>
🤖 <b>DAFTAR USERBOT</b>

📌 <b>Account:</b> {fmt_id(ubot_data.me)}
🆔 <b>ID:</b> <code>{ubot_data.me.id}</code>
📊 <b>Ke:</b> {int(count) + 1}/{len(ubot._ubot)}
</blockquote>
"""

    # ========== POLICY MSG ==========
    def POLICY():
        return f"""
<blockquote>
⚠️ <b>BUTUH BANTUAN?</b>

Silakan Hubungi owner:
<a href=tg://openmessage?user_id={OWNER_ID}>👑 @fanysx</a>
━━━━━━━━━━━━━━━━━━━━━❍
</blockquote>
"""