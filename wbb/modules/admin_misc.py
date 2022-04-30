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

from pyrogram import filters

from wbb import app
from wbb.core.decorators.permissions import adminsOnly

__MODULE__ = "Adminlər üçün digər əmrlər :"
__HELP__ = """
/set_chat_title - Qrupun/Kanalın Adını Dəyişin.
/set_chat_photo - Qrup/Kanalın təsvirini Dəyişin.
/set_user_title - Adminin Administrator Başlığını Dəyişin.
"""


@app.on_message(
    filters.command("set_chat_title")
    & ~filters.private
    & ~filters.edited
)
@adminsOnly("can_change_info")
async def set_chat_title(_, message):
    if len(message.command) < 2:
        return await message.reply_text("**İstifadə:**\n/set_chat_title yeni adı")
    old_title = message.chat.title
    new_title = message.text.split(None, 1)[1]
    await message.chat.set_title(new_title)
    await message.reply_text(
        f"Qrup Başlığı Uğurla Dəyişdirildi {old_title} ➡️ {new_title}"
    )


@app.on_message(
    filters.command("set_user_title")
    & ~filters.private
    & ~filters.edited
)
@adminsOnly("can_change_info")
async def set_user_title(_, message):
    if not message.reply_to_message:
        return await message.reply_text(
            "Admin başlığını təyin etmək üçün istifadəçinin mesajını cavablayın."
        )
    if not message.reply_to_message.from_user:
        return await message.reply_text(
            "Naməlum birinin admin adını dəyişə bilmirəm"
        )
    chat_id = message.chat.id
    from_user = message.reply_to_message.from_user
    if len(message.command) < 2:
        return await message.reply_text(
            "**İstifadə:**\n/set_user_title Yeni admin tağı"
        )
    title = message.text.split(None, 1)[1]
    await app.set_administrator_title(chat_id, from_user.id, title)
    await message.reply_text(
        f"Uğurla Dəyişdirildi {from_user.mention} admin başlığı {title}"
    )


@app.on_message(
    filters.command("set_chat_photo")
    & ~filters.private
    & ~filters.edited
)
@adminsOnly("can_change_info")
async def set_chat_photo(_, message):
    reply = message.reply_to_message

    if not reply:
        return await message.reply_text(
            "Şəkili chat_photo olaraq təyin etmək üçün ona cavab verin"
        )

    file = reply.document or reply.photo
    if not file:
        return await message.reply_text(
            "Şəkil və ya sənədi chat_photo olaraq təyin etmək üçün ona cavab verin"
        )

    if file.file_size > 5000000:
        return await message.reply("Fayl ölçüsü çox böyükdür.")

    photo = await reply.download()
    await message.chat.set_photo(photo)
    await message.reply_text("Qrup Şəkili Uğurla Dəyişdirildi.")
    os.remove(photo)
