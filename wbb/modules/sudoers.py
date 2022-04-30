"""
MIT License

Copyright (c) 2021 TheHamkerCat

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import asyncio
import os
import subprocess
import time

import psutil
from pyrogram import filters
from pyrogram.errors import FloodWait

from wbb import (
    BOT_ID,
    GBAN_LOG_GROUP_ID,
    SUDOERS,
    USERBOT_USERNAME,
    app,
    bot_start_time,
)
from wbb.core.decorators.errors import capture_err
from wbb.utils import formatter
from wbb.utils.dbfunctions import (
    add_gban_user,
    get_served_chats,
    is_gbanned_user,
    remove_gban_user,
)
from wbb.utils.functions import extract_user, extract_user_and_reason, restart

__MODULE__ = "Sudoers"
__HELP__ = """
/stats - sistem statusu.

/gstats - bot statusu.

/gban - İstifadəçini olduğum qruplardan rədd etmək.

/clean_db - db təmizləmək.

/broadcast - yayım.

/update - Botu restart et

/eval - py kodu işə sal

/sh - shell kodu işə sal
"""


# Stats Module


async def bot_sys_stats():
    bot_uptime = int(time.time() - bot_start_time)
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    process = psutil.Process(os.getpid())
    stats = f"""
{USERBOT_USERNAME}@William
------------------
UPTIME: {formatter.get_readable_time(bot_uptime)}
BOT: {round(process.memory_info()[0] / 1024 ** 2)} MB
CPU: {cpu}%
RAM: {mem}%
DISK: {disk}%
"""
    return stats


# Gban


@app.on_message(filters.command("gban") & SUDOERS & ~filters.edited)
@capture_err
async def ban_globally(_, message):
    user_id, reason = await extract_user_and_reason(message)
    user = await app.get_users(user_id)
    from_user = message.from_user

    if not user_id:
        return await message.reply_text("Tapa bilmədim.")
    if not reason:
        return await message.reply("Səbəb yoxdur, Səbəb ver.")

    if user_id in [from_user.id, BOT_ID] or user_id in SUDOERS:
        return await message.reply_text("Gedə bilərsiniz.")

    served_chats = await get_served_chats()
    m = await message.reply_text(
        f"**Dünya çapında ban {user.mention} edirəm!**"
        + f" **Bu əməliyyət bu qədər vaxta ediləcək {len(served_chats)} saniyə.**"
    )
    await add_gban_user(user_id)
    number_of_chats = 0
    for served_chat in served_chats:
        try:
            await app.ban_chat_member(served_chat["chat_id"], user.id)
            number_of_chats += 1
            await asyncio.sleep(1)
        except FloodWait as e:
            await asyncio.sleep(int(e.x))
        except Exception:
            pass
    try:
        await app.send_message(
            user.id,
            f"Salam, Siz qlobal şəkildə qadağan olunmusunuz tərəfindən {from_user.mention},"
            + " Onunla danışaraq bu qadağa üçün müraciət edə bilərsiniz.",
        )
    except Exception:
        pass
    await m.edit(f"Rədd elədim bunu {user.mention} olduğum qruplardan!")
    ban_text = f"""
__**yeni Global Ban**__
**Origin:** {message.chat.title} [`{message.chat.id}`]
**Admin:** {from_user.mention}
**Ban edən User:** {user.mention}
**Banlanan User ID:** `{user_id}`
**səbəb:** __{reason}__
**qrup sayı:** `{number_of_chats}`"""
    try:
        m2 = await app.send_message(
            GBAN_LOG_GROUP_ID,
            text=ban_text,
            disable_web_page_preview=True,
        )
        await m.edit(
            f"Rədd elədim bunu {user.mention} olduğum qruplardan!\nDeha bura bax: {m2.link}",
            disable_web_page_preview=True,
        )
    except Exception:
        await message.reply_text(
            "İstifadəçi Gban Edildi, Amma Bu Gban Fəaliyyəti Daxil Olmadı, Məni Bot-a əlavə et GBAN_LOG_GROUP"
        )


# Ungban


@app.on_message(filters.command("ungban") & SUDOERS & ~filters.edited)
@capture_err
async def unban_globally(_, message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text("I can't find that user.")
    user = await app.get_users(user_id)

    is_gbanned = await is_gbanned_user(user.id)
    if not is_gbanned:
        await message.reply_text("Bunu gban etməmişəm, etmişəmsə də yadımda deyil.")
    else:
        await remove_gban_user(user.id)
        await message.reply_text(f"Siyahı {user.mention}'s Global Ban.'")


# Broadcast


@app.on_message(filters.command("broadcast") & SUDOERS & ~filters.edited)
@capture_err
async def broadcast_message(_, message):
    if len(message.command) < 2:
        return await message.reply_text("**İstifadə**:\n/broadcast [MESSAGE]")
    sleep_time = 0.1
    text = message.text.split(None, 1)[1]
    sent = 0
    schats = await get_served_chats()
    chats = [int(chat["chat_id"]) for chat in schats]
    m = await message.reply_text(
        f"Broadcast in progress, will take {len(chats) * sleep_time} seconds."
    )
    for i in chats:
        try:
            await app.send_message(i, text=text)
            await asyncio.sleep(sleep_time)
            sent += 1
        except FloodWait as e:
            await asyncio.sleep(int(e.x))
        except Exception:
            pass
    await m.edit(f"**Broadcasted Message In {sent} Chats.**")


# Update


@app.on_message(filters.command("update") & SUDOERS & ~filters.edited)
async def update_restart(_, message):
    try:
        out = subprocess.check_output(["git", "pull"]).decode("UTF-8")
        if "Already up to date." in str(out):
            return await message.reply_text("Its already up-to date!")
        await message.reply_text(f"```{out}```")
    except Exception as e:
        return await message.reply_text(str(e))
    m = await message.reply_text(
        "**Updated with default branch, restarting now.**"
    )
    await restart(m)
