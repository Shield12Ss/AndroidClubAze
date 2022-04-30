from pyrogram import filters

from wbb import app
from wbb.core.decorators.errors import capture_err
from wbb.core.keyboard import ikb
from wbb.core.sections import section
from wbb.utils.http import get

__MODULE__ = "Kripto"
__HELP__ = """
/crypto [valyuta]
        Verilən valyutadan Real zamanlı dəyərini əldə edir.
"""


@app.on_message(filters.command("crypto") & ~filters.edited)
@capture_err
async def crypto(_, message):
    if len(message.command) < 2:
        return await message.reply("/crypto [valyuta]")

    currency = message.text.split(None, 1)[1].lower()

    btn = ikb(
        {"Mövcud Valyutalar": "https://plotcryptoprice.herokuapp.com"},
    )

    m = await message.reply("`Emal edilir...`")

    try:
        r = await get(
            "https://x.wazirx.com/wazirx-falcon/api/v2.0/crypto_rates",
            timeout=5,
        )
    except Exception:
        return await m.edit("[ERROR]: Nəsə xəta baş verdi.")

    if currency not in r:
        return await m.edit(
            "[ERROR]: YANLIŞ VALYUTA",
            reply_markup=btn,
        )

    body = {i.upper(): j for i, j in r.get(currency).items()}

    text = section(
        "Üçün cari kriptovalyuta məzənnələri " + currency.upper(),
        body,
    )
    await m.edit(text, reply_markup=btn)
