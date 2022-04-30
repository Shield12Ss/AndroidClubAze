from pyrogram import filters
from pyrogram.types import Message

from wbb import app, telegraph
from wbb.core.decorators.errors import capture_err

__MODULE__ = "Telegrapha yüklə"
__HELP__ = "/telegraph [səhifə adı]: Məqaləni orda dərc edir."


@app.on_message(filters.command("telegraph") & ~filters.edited)
@capture_err
async def paste(_, message: Message):
    reply = message.reply_to_message

    if not reply or not reply.text:
        return await message.reply("Mesajı cavablayın.")

    if len(message.command) < 2:
        return await message.reply("**İstifadə:**\n /telegraph [Səhifə adı]")

    page_name = message.text.split(None, 1)[1]
    page = telegraph.create_page(
        page_name, html_content=reply.text.html.replace("\n", "<br>")
    )
    return await message.reply(
        f"**Paylaşdım:** {page['url']}",
        disable_web_page_preview=True,
    )
