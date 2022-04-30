from pyrogram import filters
from pyrogram.types import Message

from wbb import SUDOERS, app
from wbb.core.decorators.errors import capture_err
from wbb.utils.dbfunctions import (
    blacklist_chat,
    blacklisted_chats,
    whitelist_chat,
)

__MODULE__ = "Qara siyahı söhbəti"
__HELP__ = """
**BU MODUL YALNIZ BOT SAHİBİ ÜÇÜNDÜR**

Botun bəzi qrupları tərk etməsi üçün bu moduldan istifadə edin
 içində olmasını istəmədiyiniz.

/blacklist_chat [CHAT_ID] - Söhbəti qara siyahıya salır.
/whitelist_chat [CHAT_ID] - Söhbəti ağ siyahıya salır.
/blacklisted - Qara siyahıya salınmış söhbətləri göstərir.
"""


@app.on_message(
    filters.command("blacklist_chat")
    & SUDOERS
    & ~filters.edited
)
@capture_err
async def blacklist_chat_func(_, message: Message):
    if len(message.command) != 2:
        return await message.reply_text(
            "**İstifadə:**\n/blacklist_chat [CHAT_ID]"
        )
    chat_id = int(message.text.strip().split()[1])
    if chat_id in await blacklisted_chats():
        return await message.reply_text("Çat artıq qara siyahıya salınıb.")
    blacklisted = await blacklist_chat(chat_id)
    if blacklisted:
        return await message.reply_text(
            "Chat uğurla qara siyahıya salındı"
        )
    await message.reply_text("Səhv bir şey oldu, log-u yoxlayın.")


@app.on_message(
    filters.command("whitelist_chat")
    & SUDOERS
    & ~filters.edited
)
@capture_err
async def whitelist_chat_func(_, message: Message):
    if len(message.command) != 2:
        return await message.reply_text(
            "**İstifadə:**\n/whitelist_chat [CHAT_ID]"
        )
    chat_id = int(message.text.strip().split()[1])
    if chat_id not in await blacklisted_chats():
        return await message.reply_text("Chat artıq ağ siyahıya salınıb.")
    whitelisted = await whitelist_chat(chat_id)
    if whitelisted:
        return await message.reply_text(
            "Chat uğurla ağ siyahıya salındı"
        )
    await message.reply_text("Səhv bir şey oldu, log-u yoxlayın.")


@app.on_message(
    filters.command("blacklisted_chats")
    & SUDOERS
    & ~filters.edited
)
@capture_err
async def blacklisted_chats_func(_, message: Message):
    text = ""
    for count, chat_id in enumerate(await blacklisted_chats(), 1):
        try:
            title = (await app.get_chat(chat_id)).title
        except Exception:
            title = "Private"
        text += f"**{count}. {title}** [`{chat_id}`]\n"
    if text == "":
        return await message.reply_text("Qara siyahıya salınmış söhbətlər tapılmadı.")
    await message.reply_text(text)
