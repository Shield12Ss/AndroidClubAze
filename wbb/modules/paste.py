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
import os
import re

import aiofiles
from pyrogram import filters
from pyrogram.types import Message

from wbb import SUDOERS, USERBOT_PREFIX, app, app2, eor
from wbb.core.decorators.errors import capture_err
from wbb.core.keyboard import ikb
from wbb.utils.pastebin import paste

__MODULE__ = "Rahat Paylaşım üçün"
__HELP__ = "/paste - Cavab Verilmiş Mətni Və ya Sənədi Pastebinə Yapışdırmaq üçün"
pattern = re.compile(r"^text/|json$|yaml$|xml$|toml$|x-sh$|x-shellscript$")


@app2.on_message(filters.command("paste", prefixes=USERBOT_PREFIX) & SUDOERS)
@app.on_message(filters.command("paste") & ~filters.edited)
@capture_err
async def paste_func(_, message: Message):
    if not message.reply_to_message:
        return await eor(message, text="Bu əmr ilə Mesaja Cavab Verin /paste")
    r = message.reply_to_message

    if not r.text and not r.document:
        return await eor(
            message, text="Yalnız mətn və sənədlər dəstəklənir📝."
        )

    m = await eor(message, text="Hazırlanır♻️...")

    if r.text:
        content = str(r.text)
    elif r.document:
        if r.document.file_size > 40000:
            return await m.edit("Siz yalnız 40KB-dan kiçik faylları yapışdıra bilərsiniz.")

        if not pattern.search(r.document.mime_type):
            return await m.edit("Yalnız mətn faylları yapışdırıla bilər.")

        doc = await message.reply_to_message.download()

        async with aiofiles.open(doc, mode="r") as f:
            content = await f.read()

        os.remove(doc)

    link = await paste(content)
    kb = ikb({"Paste Link": link})
    try:
        if m.from_user.is_bot:
            await message.reply_photo(
                photo=link,
                quote=False,
                reply_markup=kb,
            )
        else:
            await message.reply_photo(
                photo=link,
                quote=False,
                caption=f"**Hazır link üçün:** [Bura tıklayın]({link})",
            )
        await m.delete()
    except Exception:
        await m.edit("Buradadır", reply_markup=kb)
