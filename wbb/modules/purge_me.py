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

from wbb import USERBOT_ID, USERBOT_PREFIX, app2, eor, log, telegraph

__MODULE__ = "Userbot"
TEXT = """
<code>alive</code>  →  Alive sorğusu göndər.<br>

<code>create (b|s|c) Başlıq</code>  →  Yaratmaq [basic|super]qrup & kanal<br>

<code>chatbot [ENABLE|DISABLE]</code>  →  Söhbətdə chatbot-u aktivləşdirin.<br>

<code>autocorrect [ENABLE|DISABLE]</code>  →  Bu, mesajlarınızı avtomatik düzəldəcək on the go.<br>

<code>purgeme [Mesaj sayı]</code>  →  Öz mesajlarınızı təmizləyin.<br>

<code>eval [Kod sətri]</code>  →  Python kodunu icra edin.<br>

<code>lsTasks</code>  →  Çalışan vəzifələrin siyahısı (eval)<br>

<code>sh [Bəzi shell kodları]</code>  →  Shell kodunu icra edin.<br>

<code>approve</code>  →  Sizə PM göndərmək üçün istifadəçini təsdiqləyin.<br>

<code>disapprove</code>  →  Sizə PM göndərən istifadəçini rədd edin.<br>

<code>block</code>  →  İstifadəçini bloklayın.<br>

<code>unblock</code>  →  İstifadəçini blokdan çıxarın.<br>

<code>anonymize</code>  →  Adı/PFP-ni təsadüfi olaraq dəyişdirin.<br>

<code>impersonate [User_ID|Username|cavab]</code> → İstifadəçinin profilini klonlayın.<br>

<code>useradd</code>  →  Sudoers-də istifadəçi əlavə etmək üçün. [TƏHLÜKƏLİ]<br>

<code>userdel</code>  → İstifadəçini sudoers-dən silmək üçün.<br>

<code>sudoers</code>  →  Sudo istifadəçilərini siyahıya almaq üçün.<br>

<code>download [URL və ya fayla cavab]</code>  →  Link atın faylı yükləsin<br>

<code>upload [URL və ya Fayl yolu]</code>  →  local və ya URL-dən fayl yükləyin<br>

<code>parse_preview [Mesaj yanıtlanmalıdır]</code>  →  web_page(link) önizləməsini təhlil edin<br>

<code>id</code>  →  /id ilə eyni, lakin Ubot üçün<br>

<code>paste</code> → batbin üzərinə yapışdırın.<br>

<code>help</code> → Bu səhifəyə keçid əldə edin.<br>

<code>kang</code> → Kang stikerləri.<br>

<code>dice</code> → Zər atmaq.<br>
"""
log.info("Pasting userbot commands on telegraph")

__HELP__ = f"""**Commands:** {telegraph.create_page(
    "Userbot Əmrləri",
    html_content=TEXT,
)['url']}"""

log.info("Done pasting userbot commands on telegraph")


@app2.on_message(
    filters.command("help", prefixes=USERBOT_PREFIX) & filters.user(USERBOT_ID)
)
async def get_help(_, message: Message):
    await eor(
        message,
        text=__HELP__,
        disable_web_page_preview=True,
    )


@app2.on_message(
    filters.command(["purgeme", "purge_me"], prefixes=USERBOT_PREFIX)
    & filters.user(USERBOT_ID)
)
async def purge_me_func(_, message: Message):
    if len(message.command) != 2:
        return await message.delete()

    n = message.text.split(None, 1)[1].strip()
    if not n.isnumeric():
        return await eor(message, text="Naməlum")

    n = int(n)

    if n < 1:
        return await eor(message, text="Nömrə lazmdır >=1")

    chat_id = message.chat.id

    message_ids = [
        m.message_id
        async for m in app2.search_messages(
            chat_id,
            from_user=int(USERBOT_ID),
            limit=n,
        )
    ]

    if not message_ids:
        return await eor(message, text="Tapılmadı.")

    # A list containing lists of 100 message chunks
    # because we can't delete more than 100 messages at once,
    # we have to do it in chunks of 100, i'll choose 99 just
    # to be safe.
    to_delete = [
        message_ids[i: i + 99] for i in range(0, len(message_ids), 99)
    ]

    for hundred_messages_or_less in to_delete:
        await app2.delete_messages(
            chat_id=chat_id,
            message_ids=hundred_messages_or_less,
            revoke=True,
        )
