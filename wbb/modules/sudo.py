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
from pyrogram import filters
from pyrogram.types import Message

from wbb import BOT_ID, SUDOERS, USERBOT_PREFIX, app2, eor
from wbb.core.decorators.errors import capture_err
from wbb.utils.dbfunctions import add_sudo, get_sudoers, remove_sudo
from wbb.utils.functions import restart

__MODULE__ = "Sudo"
__HELP__ = """
**Sahibdən yetki istə versin sonra işlət bunu**

.useradd - Sudoers-də istifadəçi əlavə etmək üçün.
.userdel - Sudoers-də istifadəçi silmək üçün.
.sudoers - siyahı.

**qeyd:**

Tanımırsansa etmə.
"""


@app2.on_message(filters.command("useradd", prefixes=USERBOT_PREFIX) & SUDOERS)
@capture_err
async def useradd(_, message: Message):
    if not message.reply_to_message:
        return await eor(
            message,
            text="Sudoerlərə əlavə etmək üçün kiminsə mesajına cavab verin.",
        )
    user_id = message.reply_to_message.from_user.id
    umention = (await app2.get_users(user_id)).mention
    sudoers = await get_sudoers()

    if user_id in sudoers:
        return await eor(message, text=f"{umention} eləmişəm.")
    if user_id == BOT_ID:
        return await eor(
            message, text="Zarafatın Yeri Deyil."
        )

    await add_sudo(user_id)

    if user_id not in SUDOERS:
        SUDOERS.add(user_id)

    await eor(
        message,
        text=f"Elədim {umention} Gözləyin.",
    )


@app2.on_message(filters.command("userdel", prefixes=USERBOT_PREFIX) & SUDOERS)
@capture_err
async def userdel(_, message: Message):
    if not message.reply_to_message:
        return await eor(
            message,
            text="Kiminsə mesajını cavablayın ki, onu sudoerlərə göndərin.",
        )
    user_id = message.reply_to_message.from_user.id
    umention = (await app2.get_users(user_id)).mention

    if user_id not in await get_sudoers():
        return await eor(message, text=f"{umention} iıhıh getdə.")

    await remove_sudo(user_id)

    if user_id in SUDOERS:
        SUDOERS.remove(user_id)

    await eor(
        message,
        text=f"Sildim {umention} getdi.",
    )


@app2.on_message(filters.command("sudoers", prefixes=USERBOT_PREFIX) & SUDOERS)
@capture_err
async def sudoers_list(_, message: Message):
    sudoers = await get_sudoers()
    text = ""
    j = 0
    for user_id in sudoers:
        try:
            user = await app2.get_users(user_id)
            user = user.first_name if not user.mention else user.mention
            j += 1
        except Exception:
            continue
        text += f"{j}. {user}\n"
    if text == "":
        return await eor(message, text="Yoxdu.")
    await eor(message, text=text)
