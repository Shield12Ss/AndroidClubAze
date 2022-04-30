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
from time import time

from pyrogram import filters
from pyrogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    ChatPermissions,
    Message,
)

from wbb import BOT_ID, SUDOERS, app, log
from wbb.core.decorators.errors import capture_err
from wbb.core.keyboard import ikb
from wbb.utils.dbfunctions import (
    add_warn,
    get_warn,
    int_to_alpha,
    remove_warns,
    save_filter,
)
from wbb.utils.functions import (
    extract_user,
    extract_user_and_reason,
    time_converter,
)

__MODULE__ = "Qrup daxili admin əmrləri : "
__HELP__ = """/ban - İstifadəçini qrupdan kənarlaşdırır
/dban - Kənarlaşdırılmış istifadəyçiyə verilən qadağa mesajını silir
/tban - İstifadəçini Müəyyən Müddət Qadağan Edir
/unban - İstifadəçinin qadağasını ləğv edir
/warn - İstifadəçiyə xəbərdarlıq edir
/dwarn - Xəbərdarlıq edilmiş istifadəyçiyə verilən xəbərdarlıq mesajını silir
/rmwarns - İstifadəçinin bütün xəbərdarlıqlarını silir
/warns - İstifadəçinin Xəbərdarlığını Göstərir
/kick - İstifadəçini kənarlaşdırır
/dkick - Kənarlaşdırılmış istifadəyçiyə verilən qadağa mesajını silir
/purge - Mesajları Təmizləyir
/purge [n] - Cavab verilmiş mesajdan n sayda mesajı təmizləyir
/del - Cavab verilən mesajı silir
/promote - İstifadəçiyə admin statusu verir
/fullpromote - İstifadəçiyə admin statusu vermək və bütün icazələrini açır
/demote - İstifadəçinin admin statusunu ləğv edir
/pin - Mesajı sabitləyir
/mute - İstifadəçini susdurur
/tmute - Müəyyən vaxt müddətində istifadəçini susdurur
/unmute - Susdurulmanı ləğv edir
/ban_ghosts - Qrupdakı silinmiş hesabları qrupdan kənarlaşdırır
/report | @admins | @admin - Bir mesajı adminlərə bildirir
/admincache - Admin siyahısını yenidən yükləyir """


async def member_permissions(chat_id: int, user_id: int):
    perms = []
    try:
        member = await app.get_chat_member(chat_id, user_id)
    except Exception:
        return []
    if member.can_post_messages:
        perms.append("can_post_messages")
    if member.can_edit_messages:
        perms.append("can_edit_messages")
    if member.can_delete_messages:
        perms.append("can_delete_messages")
    if member.can_restrict_members:
        perms.append("can_restrict_members")
    if member.can_promote_members:
        perms.append("can_promote_members")
    if member.can_change_info:
        perms.append("can_change_info")
    if member.can_invite_users:
        perms.append("can_invite_users")
    if member.can_pin_messages:
        perms.append("can_pin_messages")
    if member.can_manage_voice_chats:
        perms.append("can_manage_voice_chats")
    return perms


from wbb.core.decorators.permissions import adminsOnly

admins_in_chat = {}


async def list_admins(chat_id: int):
    global admins_in_chat
    if chat_id in admins_in_chat:
        interval = time() - admins_in_chat[chat_id]["last_updated_at"]
        if interval < 3600:
            return admins_in_chat[chat_id]["data"]

    admins_in_chat[chat_id] = {
        "last_updated_at": time(),
        "data": [
            member.user.id
            async for member in app.iter_chat_members(
                chat_id, filter="administrators"
            )
        ],
    }
    return admins_in_chat[chat_id]["data"]


async def current_chat_permissions(chat_id):
    perms = []
    perm = (await app.get_chat(chat_id)).permissions
    if perm.can_send_messages:
        perms.append("can_send_messages")
    if perm.can_send_media_messages:
        perms.append("can_send_media_messages")
    if perm.can_send_other_messages:
        perms.append("can_send_other_messages")
    if perm.can_add_web_page_previews:
        perms.append("can_add_web_page_previews")
    if perm.can_send_polls:
        perms.append("can_send_polls")
    if perm.can_change_info:
        perms.append("can_change_info")
    if perm.can_invite_users:
        perms.append("can_invite_users")
    if perm.can_pin_messages:
        perms.append("can_pin_messages")

    return perms


# Admin cache reload


@app.on_chat_member_updated()
async def admin_cache_func(_, cmu: ChatMemberUpdated):
    if cmu.old_chat_member and cmu.old_chat_member.promoted_by:
        admins_in_chat[cmu.chat.id] = {
            "last_updated_at": time(),
            "data": [
                member.user.id
                async for member in app.iter_chat_members(
                    cmu.chat.id, filter="administrators"
                )
            ],
        }
        log.info(f"Adminlist yeniləndi {cmu.chat.id} [{cmu.chat.title}]")


# Purge Messages


@app.on_message(filters.command("purge") & ~filters.edited & ~filters.private)
@adminsOnly("can_delete_messages")
async def purgeFunc(_, message: Message):
    repliedmsg = message.reply_to_message
    await message.delete()

    if not repliedmsg:
        return await message.reply_text("Silmək üçün mesajı cavablayın.")

    cmd = message.command
    if len(cmd) > 1 and cmd[1].isdigit():
        purge_to = repliedmsg.message_id + int(cmd[1])
        if purge_to > message.message_id:
            purge_to = message.message_id
    else:
        purge_to = message.message_id   

    chat_id = message.chat.id
    message_ids = []

    for message_id in range(
            repliedmsg.message_id,
            purge_to,
    ):
        message_ids.append(message_id)

        # Max message deletion limit is 100
        if len(message_ids) == 100:
            await app.delete_messages(
                chat_id=chat_id,
                message_ids=message_ids,
                revoke=True,  # For both sides
            )

            # To delete more than 100 messages, start again
            message_ids = []

    # Delete if any messages left
    if len(message_ids) > 0:
        await app.delete_messages(
            chat_id=chat_id,
            message_ids=message_ids,
            revoke=True,
        )


# Kick members


@app.on_message(
    filters.command(["kick", "dkick"]) & ~filters.edited & ~filters.private
)
@adminsOnly("can_restrict_members")
async def kickFunc(_, message: Message):
    user_id, reason = await extract_user_and_reason(message)
    if not user_id:
        return await message.reply_text("Bu istifadəçini tapa bilmirəm.")
    if user_id == BOT_ID:
        return await message.reply_text(
            "Xata Var."
        )
    if user_id in SUDOERS:
        return await message.reply_text("Sənin bunu etmək ixtiyarın yoxdur.")
    if user_id in (await list_admins(message.chat.id)):
        return await message.reply_text(
            "Sənin bunu etmək ixtiyarın yoxdur."
        )
    mention = (await app.get_users(user_id)).mention
    msg = f"""
**Kenarlaşdırılan şəxs:** {mention}
**Kənarlaşdıran şəxs:** {message.from_user.mention if message.from_user else 'Anon'}
**Səbəb:** {reason or 'Səbəb göstərilmədi.'}"""
    if message.command[0][0] == "d":
        await message.reply_to_message.delete()
    await message.chat.ban_member(user_id)
    await message.reply_text(msg)
    await asyncio.sleep(1)
    await message.chat.unban_member(user_id)


# Ban members


@app.on_message(
    filters.command(["ban", "dban", "tban"])
    & ~filters.edited
    & ~filters.private
)
@adminsOnly("can_restrict_members")
async def banFunc(_, message: Message):
    user_id, reason = await extract_user_and_reason(message, sender_chat=True)

    if not user_id:
        return await message.reply_text("Bu istifadəçini tapa bilmirəm.")
    if user_id == BOT_ID:
        return await message.reply_text(
            "Sənin bunu etmək ixtiyarın yoxdur.."
        )
    if user_id in SUDOERS:
        return await message.reply_text(
            "Sənin bunu etmək ixtiyarın yoxdur!"
        )
    if user_id in (await list_admins(message.chat.id)):
        return await message.reply_text(
            "Sənin bunu etmək ixtiyarın yoxdur.."
        )

    try:
        mention = (await app.get_users(user_id)).mention
    except IndexError:
        mention = (
            message.reply_to_message.sender_chat.title
            if message.reply_to_message
            else "Anon"
        )

    msg = (
        f"**Ban edilən şəxs:** {mention}\n"
        f"**Ban edən şəxs:** {message.from_user.mention if message.from_user else 'Anon'}\n"
    )
    if message.command[0][0] == "d":
        await message.reply_to_message.delete()
    if message.command[0] == "tban":
        split = reason.split(None, 1)
        time_value = split[0]
        temp_reason = split[1] if len(split) > 1 else ""
        temp_ban = await time_converter(message, time_value)
        msg += f"**Banlandı:** {time_value}\n"
        if temp_reason:
            msg += f"**Səbəb:** {temp_reason}"
        try:
            if len(time_value[:-1]) < 3:
                await message.chat.ban_member(user_id, until_date=temp_ban)
                await message.reply_text(msg)
            else:
                await message.reply_text("99-dan çox istifadə edə bilməzsən.")
        except AttributeError:
            pass
        return
    if reason:
        msg += f"**Səbəb:** {reason}"
    await message.chat.ban_member(user_id)
    await message.reply_text(msg)


# Unban members


@app.on_message(filters.command("unban") & ~filters.edited & ~filters.private)
@adminsOnly("can_restrict_members")
async def unban_func(_, message: Message):
    # Bizə qadağanın aradan qaldırılması üçün səbəb lazım deyil, biz də
    # Bunu almaq lazım deyil "text_mention" çünki
    # istifadəçi əgər normal istifadəçilər text_mention almayacaq
    # Qrupda olmayanların banını çıxarmaq istəyirlər.
    reply = message.reply_to_message

    if reply and reply.sender_chat and reply.sender_chat != message.chat.id:
        return await message.reply_text("Kanaldı bu")

    if len(message.command) == 2:
        user = message.text.split(None, 1)[1]
    elif len(message.command) == 1 and reply:
        user = message.reply_to_message.from_user.id
    else:
        return await message.reply_text(
            "Qadağanı ləğv etmək üçün istifadəçi adı verin və ya istifadəçinin mesajını cavablayın."
        )
    await message.chat.unban_member(user)
    umention = (await app.get_users(user)).mention
    await message.reply_text(f"Unbanned! {umention}")


# Delete messages


@app.on_message(filters.command("del") & ~filters.edited & ~filters.private)
@adminsOnly("can_delete_messages")
async def deleteFunc(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Mesajı Silmək üçün Cavab Verin")
    await message.reply_to_message.delete()
    await message.delete()


# Promote Members


@app.on_message(
    filters.command(["promote", "fullpromote"])
    & ~filters.edited
    & ~filters.private
)
@adminsOnly("can_promote_members")
async def promoteFunc(_, message: Message):
    user_id = await extract_user(message)
    umention = (await app.get_users(user_id)).mention
    if not user_id:
        return await message.reply_text("Həmin istifadəçini tapa bilmirəm.")
    bot = await app.get_chat_member(message.chat.id, BOT_ID)
    if user_id == BOT_ID:
        return await message.reply_text("Sənin bunu etmək ixtiyarın yoxdur.")
    if not bot.can_promote_members:
        return await message.reply_text("Yetəri qədər yetkim yoxdur.")
    if message.command[0][0] == "f":
        await message.chat.promote_member(
            user_id=user_id,
            can_change_info=bot.can_change_info,
            can_invite_users=bot.can_invite_users,
            can_delete_messages=bot.can_delete_messages,
            can_restrict_members=bot.can_restrict_members,
            can_pin_messages=bot.can_pin_messages,
            can_promote_members=bot.can_promote_members,
            can_manage_chat=bot.can_manage_chat,
            can_manage_voice_chats=bot.can_manage_voice_chats,
        )
        return await message.reply_text(f"Tam admin edildi! {umention}")

    await message.chat.promote_member(
        user_id=user_id,
        can_change_info=False,
        can_invite_users=bot.can_invite_users,
        can_delete_messages=bot.can_delete_messages,
        can_restrict_members=False,
        can_pin_messages=False,
        can_promote_members=False,
        can_manage_chat=bot.can_manage_chat,
        can_manage_voice_chats=bot.can_manage_voice_chats,
    )
    await message.reply_text(f"Səlahiyyət verildi! {umention}")


# Demote Member


@app.on_message(filters.command("demote") & ~filters.edited & ~filters.private)
@adminsOnly("can_promote_members")
async def demote(_, message: Message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text("Bu istifadəçini tapa bilmirəm.")
    if user_id == BOT_ID:
        return await message.reply_text("Sənin bunu etmək ixtiyarın yoxdur.")
    if user_id in SUDOERS:
        return await message.reply_text(
            "Sənin bunu etmək ixtiyarın yoxdur!"
        )
    await message.chat.promote_member(
        user_id=user_id,
        can_change_info=False,
        can_invite_users=False,
        can_delete_messages=False,
        can_restrict_members=False,
        can_pin_messages=False,
        can_promote_members=False,
        can_manage_chat=False,
        can_manage_voice_chats=False,
    )
    umention = (await app.get_users(user_id)).mention
    await message.reply_text(f"Səlahiyyəti ləğv edildi! {umention}")


# Pin Messages


@app.on_message(
    filters.command(["pin", "unpin"]) & ~filters.edited & ~filters.private
)
@adminsOnly("can_pin_messages")
async def pin(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Mesajı sabitləmək/sabitdən qaldırmaq üçün onu cavablayın.")
    r = message.reply_to_message
    if message.command[0][0] == "u":
        await r.unpin()
        return await message.reply_text(
            f"**Ləğv edildi [this]({r.link}) message.**",
            disable_web_page_preview=True,
        )
    await r.pin(disable_notification=True)
    await message.reply(
        f"**Uğurla alındı [this]({r.link}) message.**",
        disable_web_page_preview=True,
    )
    msg = "Zəhmət olmasa sabitlənmiş mesajı yoxlayın: ~ " + f"[Check, {r.link}]"
    filter_ = dict(type="text", data=msg)
    await save_filter(message.chat.id, "~pinned", filter_)


# Mute members


@app.on_message(
    filters.command(["mute", "tmute"]) & ~filters.edited & ~filters.private
)
@adminsOnly("can_restrict_members")
async def mute(_, message: Message):
    user_id, reason = await extract_user_and_reason(message)
    if not user_id:
        return await message.reply_text("Bu istifadəçini tapa bilmirəm.")
    if user_id == BOT_ID:
        return await message.reply_text("Sənin bunu etmək ixtiyarın yoxdur.")
    if user_id in SUDOERS:
        return await message.reply_text(
            "Sənin bunu etmək ixtiyarın yoxdur!"
        )
    if user_id in (await list_admins(message.chat.id)):
        return await message.reply_text(
            "Sənin bunu etmək ixtiyarın yoxdur."
        )
    mention = (await app.get_users(user_id)).mention
    keyboard = ikb({"   Səsini açmaq   ": f"unmute_{user_id}"})
    msg = (
        f"**Səssizə alılan şəxs:** {mention}\n"
        f"**Səssizə alan şəxs:** {message.from_user.mention if message.from_user else 'Anon'}\n"
    )
    if message.command[0] == "tmute":
        split = reason.split(None, 1)
        time_value = split[0]
        temp_reason = split[1] if len(split) > 1 else ""
        temp_mute = await time_converter(message, time_value)
        msg += f"**Səssizə alındı :** {time_value}\n"
        if temp_reason:
            msg += f"**Səbəb:** {temp_reason}"
        try:
            if len(time_value[:-1]) < 3:
                await message.chat.restrict_member(
                    user_id,
                    permissions=ChatPermissions(),
                    until_date=temp_mute,
                )
                await message.reply_text(msg, reply_markup=keyboard)
            else:
                await message.reply_text("99-dan çox istifadə edə bilməzsən")
        except AttributeError:
            pass
        return
    if reason:
        msg += f"**Səbəb:** {reason}"
    await message.chat.restrict_member(user_id, permissions=ChatPermissions())
    await message.reply_text(msg, reply_markup=keyboard)


# Unmute members


@app.on_message(filters.command("unmute") & ~filters.edited & ~filters.private)
@adminsOnly("can_restrict_members")
async def unmute(_, message: Message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text("Həmin istifadəçini tapa bilmirəm.")
    await message.chat.unban_member(user_id)
    umention = (await app.get_users(user_id)).mention
    await message.reply_text(f"Səsi açıldı! {umention}")


# Ban deleted accounts


@app.on_message(
    filters.command("ban_ghosts")
    & ~filters.private
    & ~filters.edited
)
@adminsOnly("can_restrict_members")
async def ban_deleted_accounts(_, message: Message):
    chat_id = message.chat.id
    deleted_users = []
    banned_users = 0
    m = await message.reply("Silinmiş hesablar axtarılır...")

    async for i in app.iter_chat_members(chat_id):
        if i.user.is_deleted:
            deleted_users.append(i.user.id)
    if len(deleted_users) > 0:
        for deleted_user in deleted_users:
            try:
                await message.chat.ban_member(deleted_user)
            except Exception:
                pass
            banned_users += 1
        await m.edit(f"Silinmiş hesablar {banned_users} Kənarlaşdırıldı.")
    else:
        await m.edit("Bu qrupda silinmiş hesab yoxdur.")


@app.on_message(
    filters.command(["warn", "dwarn"]) & ~filters.edited & ~filters.private
)
@adminsOnly("can_restrict_members")
async def warn_user(_, message: Message):
    user_id, reason = await extract_user_and_reason(message)
    chat_id = message.chat.id
    if not user_id:
        return await message.reply_text("Bu istifadəçini tapa bilmirəm.")
    if user_id == BOT_ID:
        return await message.reply_text(
            "Sənin bunu etmək ixtiyarın yoxdu."
        )
    if user_id in SUDOERS:
        return await message.reply_text(
            "Sənin bunu etmək ixtiyarın yoxdu!"
        )
    if user_id in (await list_admins(chat_id)):
        return await message.reply_text(
            "Sənin bunu etmək ixtiyarın yoxdu."
        )
    user, warns = await asyncio.gather(
        app.get_users(user_id),
        get_warn(chat_id, await int_to_alpha(user_id)),
    )
    mention = user.mention
    keyboard = ikb({"  Xəbərdarlığı silin  ": f"unwarn_{user_id}"})
    if warns:
        warns = warns["warns"]
    else:
        warns = 0
    if message.command[0][0] == "d":
        await message.reply_to_message.delete()
    if warns >= 2:
        await message.chat.ban_member(user_id)
        await message.reply_text(
            f"Xəbərdarlıqların sayı {mention} keçdi, Kənarlaşdırıldı!"
        )
        await remove_warns(chat_id, await int_to_alpha(user_id))
    else:
        warn = {"warns": warns + 1}
        msg = f"""
**Xəbərdarlıq edilən şəxs:** {mention}
**Xəbərdarlıq edən şəxs:** {message.from_user.mention if message.from_user else 'Anon'}
**Səbəb:** {reason or 'Səbəb yoxdur.'}
**Xəbərdarlıqlar:** {warns + 1}/3"""
        await message.reply_text(msg, reply_markup=keyboard)
        await add_warn(chat_id, await int_to_alpha(user_id), warn)


@app.on_callback_query(filters.regex("unwarn_"))
async def remove_warning(_, cq: CallbackQuery):
    from_user = cq.from_user
    chat_id = cq.message.chat.id
    permissions = await member_permissions(chat_id, from_user.id)
    permission = "can_restrict_members"
    if permission not in permissions:
        return await cq.answer(
            "Sənin bunu etmək ixtiyarın yoxdur.\n"
            + f"Bunun üçün Yetkin yoxdur: {permission}",
            show_alert=True,
        )
    user_id = cq.data.split("_")[1]
    warns = await get_warn(chat_id, await int_to_alpha(user_id))
    if warns:
        warns = warns["warns"]
    if not warns or warns == 0:
        return await cq.answer("İstifadəçinin xəbərdarlığı yoxdur.")
    warn = {"warns": warns - 1}
    await add_warn(chat_id, await int_to_alpha(user_id), warn)
    text = cq.message.text.markdown
    text = f"~~{text}~~\n\n"
    text += f"__Xəbərdarlıq bu şəxs tərəfindən silindi {from_user.mention}__"
    await cq.message.edit(text)


# Rmwarns


@app.on_message(
    filters.command("rmwarns") & ~filters.edited & ~filters.private
)
@adminsOnly("can_restrict_members")
async def remove_warnings(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text(
            "İstifadəçinin xəbərdarlıqlarını silmək üçün mesajını cavablayın."
        )
    user_id = message.reply_to_message.from_user.id
    mention = message.reply_to_message.from_user.mention
    chat_id = message.chat.id
    warns = await get_warn(chat_id, await int_to_alpha(user_id))
    if warns:
        warns = warns["warns"]
    if warns == 0 or not warns:
        await message.reply_text(f"{mention} heç bir xəbərdarlıq yoxdur.")
    else:
        await remove_warns(chat_id, await int_to_alpha(user_id))
        await message.reply_text(f"Xəbərdarlıqları silindi {mention}.")


# Warns


@app.on_message(filters.command("warns") & ~filters.edited & ~filters.private)
@capture_err
async def check_warns(_, message: Message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text("Bu istifadəçini tapa bilmirəm.")
    warns = await get_warn(message.chat.id, await int_to_alpha(user_id))
    mention = (await app.get_users(user_id)).mention
    if warns:
        warns = warns["warns"]
    else:
        return await message.reply_text(f"{mention} heç bir xəbərdarlıq yoxdur.")
    return await message.reply_text(f"{mention} var {warns}/3 xəbərdarlığı.")


# Report


@app.on_message(
    (
            filters.command("report")
            | filters.command(["admins", "admin"], prefixes="@")
    )
    & ~filters.edited
    & ~filters.private
)
@capture_err
async def report_user(_, message):
    if not message.reply_to_message:
        return await message.reply_text(
            "Həmin istifadəçini şikayət etmək üçün onun mesajına cavab verin."
        )

    if message.reply_to_message.from_user.id == message.from_user.id:
        return await message.reply_text("Özünü niyə report edirsən?👮‍♂️")

    list_of_admins = await list_admins(message.chat.id)
    if message.reply_to_message.from_user.id in list_of_admins:
        return await message.reply_text(
            "Cavab verdiyiniz istifadəçinin admin olduğunu bilirsinizmi?"
        )

    user_mention = message.reply_to_message.from_user.mention
    text = f"Report edildi {user_mention} adminlərə."
    admin_data = await app.get_chat_members(
        chat_id=message.chat.id, filter="administrators"
    )  # will it giv floods ?
    for admin in admin_data:
        if admin.user.is_bot or admin.user.is_deleted:
            # return bots or deleted admins
            continue
        text += f"[\u2063](tg://user?id={admin.user.id})"

    await message.reply_to_message.reply_text(text)
