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
import imghdr
import os
from asyncio import gather
from traceback import format_exc

from pyrogram import filters
from pyrogram.errors import (
    PeerIdInvalid,
    ShortnameOccupyFailed,
    StickerEmojiInvalid,
    StickerPngDimensions,
    StickerPngNopng,
    UserIsBlocked,
)
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from wbb import BOT_USERNAME, SUDOERS, USERBOT_PREFIX, app, app2, eor
from wbb.core.decorators.errors import capture_err
from wbb.utils.files import (
    get_document_from_file_id,
    resize_file_to_sticker_size,
    upload_document,
)
from wbb.utils.stickerset import (
    add_sticker_to_set,
    create_sticker,
    create_sticker_set,
    get_sticker_set_by_name,
)

__MODULE__ = "Stickerlər"
__HELP__ = """
/sticker_id
    Sticker id görmək.
/get_sticker
    Şəkili sticker etmək.
/kang
    Stiker və ya Şəkil çəkmək üçün."""

MAX_STICKERS = (
    120  # would be better if we could fetch this limit directly from telegram
)
SUPPORTED_TYPES = ["jpeg", "png", "webp"]


@app.on_message(filters.command("sticker_id") & ~filters.edited)
@capture_err
async def sticker_id(_, message: Message):
    reply = message.reply_to_message

    if not reply:
        return await message.reply("Cavabla yaz.")

    if not reply.sticker:
        return await message.reply("Cavabla yaz ki, heç birimizə əlavə əziyyət olmasın.")

    await message.reply_text(f"`{reply.sticker.file_id}`")


@app.on_message(filters.command("get_sticker") & ~filters.edited)
@capture_err
async def sticker_image(_, message: Message):
    r = message.reply_to_message

    if not r:
        return await message.reply("Cavabla yaz ki, heç birimizə əlavə əziyyət olmasın.")

    if not r.sticker:
        return await message.reply("Cavabla yaz ki, heç birimizə əlavə əziyyət olmasın.")

    m = await message.reply("Göndərilir...")
    f = await r.download(f"{r.sticker.file_unique_id}.png")

    await gather(
        *[
            message.reply_photo(f),
            message.reply_document(f),
        ]
    )

    await m.delete()
    os.remove(f)


@app2.on_message(
    filters.command("kang", prefixes=USERBOT_PREFIX) & SUDOERS,
)
async def userbot_kang(_, message: Message):
    reply = message.reply_to_message

    if not reply:
        return await message.reply_text("Stickeri və ya şəkli cavabla yaz.")

    sticker_m = await reply.forward(BOT_USERNAME)

    # Send /kang message to bot and listen to his reply concurrently
    bot_reply, kang_m_bot = await gather(
        app2.listen(BOT_USERNAME, filters=~filters.me),
        sticker_m.reply(message.text.replace(USERBOT_PREFIX, "/")),
    )

    # Edit init message of ubot with the reply of
    # bot we got in the previous block
    bot_reply, ub_m = await gather(
        app2.listen(BOT_USERNAME, filters=~filters.me),
        eor(message, text=bot_reply.text.markdown),
    )

    # Edit the main userbot message with bot's final edit
    await ub_m.edit(bot_reply.text.markdown)

    # Delete all extra messages.
    for m in [bot_reply, kang_m_bot, sticker_m]:
        await m.delete()


@app.on_message(filters.command("kang") & ~filters.edited)
@capture_err
async def kang(client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Stickeri və ya şəkli cavabla yaz.")
    if not message.from_user:
        return await message.reply_text(
            "Sən pm dan yaz."
        )
    msg = await message.reply_text("Kanglanır Sticker..")

    # Find the proper emoji
    args = message.text.split()
    if len(args) > 1:
        sticker_emoji = str(args[1])
    elif (
            message.reply_to_message.sticker
            and message.reply_to_message.sticker.emoji
    ):
        sticker_emoji = message.reply_to_message.sticker.emoji
    else:
        sticker_emoji = "🤔"

    # Get the corresponding fileid, resize the file if necessary
    doc = message.reply_to_message.photo or message.reply_to_message.document
    try:
        if message.reply_to_message.sticker:
            sticker = await create_sticker(
                await get_document_from_file_id(
                    message.reply_to_message.sticker.file_id
                ),
                sticker_emoji,
            )
        elif doc:
            if doc.file_size > 10000000:
                return await msg.edit("Həcmi böyükdür.")

            temp_file_path = await app.download_media(doc)
            image_type = imghdr.what(temp_file_path)
            if image_type not in SUPPORTED_TYPES:
                return await msg.edit(
                    "Format dəstəklənmir! ({})".format(image_type)
                )
            try:
                temp_file_path = await resize_file_to_sticker_size(
                    temp_file_path
                )
            except OSError as e:
                await msg.edit_text("Xata Var. Problem səndədi.")
                raise Exception(
                    f"Xata Var (at {temp_file_path}); {e}"
                )
            sticker = await create_sticker(
                await upload_document(client, temp_file_path, message.chat.id),
                sticker_emoji,
            )
            if os.path.isfile(temp_file_path):
                os.remove(temp_file_path)
        else:
            return await msg.edit("Alınmadı.")
    except ShortnameOccupyFailed:
        await message.reply_text("Adını və ya username-ni dəyiş.")
        return

    except Exception as e:
        await message.reply_text(str(e))
        e = format_exc()
        return print(e)

    # Find an available pack & add the sticker to the pack; create a new pack if needed
    # Would be a good idea to cache the number instead of searching it every single time...
    packnum = 0
    packname = "f" + str(message.from_user.id) + "_by_" + BOT_USERNAME
    limit = 0
    try:
        while True:
            # Prevent infinite rules
            if limit >= 50:
                return await msg.delete()

            stickerset = await get_sticker_set_by_name(client, packname)
            if not stickerset:
                stickerset = await create_sticker_set(
                    client,
                    message.from_user.id,
                    f"{message.from_user.first_name[:32]}'s kang pack",
                    packname,
                    [sticker],
                )
            elif stickerset.set.count >= MAX_STICKERS:
                packnum += 1
                packname = (
                        "f"
                        + str(packnum)
                        + "_"
                        + str(message.from_user.id)
                        + "_by_"
                        + BOT_USERNAME
                )
                limit += 1
                continue
            else:
                try:
                    await add_sticker_to_set(client, stickerset, sticker)
                except StickerEmojiInvalid:
                    return await msg.edit("[ERROR]: INVALID_EMOJI_IN_ARGUMENT")
            limit += 1
            break

        await msg.edit(
            "Sticker Kanged To [Pack](t.me/addstickers/{})\nEmoji: {}".format(
                packname, sticker_emoji
            )
        )
    except (PeerIdInvalid, UserIsBlocked):
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Start", url=f"t.me/{BOT_USERNAME}")]]
        )
        await msg.edit(
            "You Need To Start A Private Chat With Me.",
            reply_markup=keyboard,
        )
    except StickerPngNopng:
        await message.reply_text(
            "Stikerlər png faylları olmalıdır, lakin təqdim edilən şəkil png deyil"
        )
    except StickerPngDimensions:
        await message.reply_text("Bu o deyil, düzgün olanını göndər.")
