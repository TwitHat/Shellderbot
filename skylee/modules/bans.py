import html

from telegram import Chat, User, ParseMode
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html

from skylee import dispatcher, LOGGER
from skylee.modules.disable import DisableAbleCommandHandler
from skylee.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat
from skylee.modules.helper_funcs.extraction import extract_user_and_text
from skylee.modules.helper_funcs.string_handling import extract_time
from skylee.modules.helper_funcs.admin_rights import user_can_ban
from skylee.modules.helper_funcs.alternate import typing_action
from skylee.modules.log_channel import loggable


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
@typing_action
def ban(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    if user_can_ban(chat, user, context.bot.id) is False:
    	message.reply_text("You don't have enough rights to ban users!")
    	return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Dude atleast refer some user to ban!")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        message.reply_text("I can't seem to find this user")
        return ""
    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("I'm not gonna ban an admin, don't make fun of yourself!")
        return ""

    if user_id == context.bot.id:
        message.reply_text("I'm not gonna BAN myself, are you crazy or wot?")
        return ""

    log = f"<b>{html.escape(chat.title)}:</b>\n#BANNED\n<b>Admin:</b> {mention_html(user.id, user.first_name)}\n<b>User:</b> {mention_html(member.user.id, member.user.first_name)} (<code>{member.user.id}</code>)"
    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    try:
        chat.kick_member(user_id)
        #context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        context.bot.sendMessage(
            chat.id,
            f"let {mention_html(member.user.id, member.user.first_name)} walk the plank.",
            parse_mode=ParseMode.HTML,
        )
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Banned!', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Well damn, I can't ban that user.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
@typing_action
def temp_ban(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    if user_can_ban(chat, user, context.bot.id) is False:
    	message.reply_text("You don't have enough rights to temporarily ban someone!")
    	return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Dude! atleast refer some user to ban...")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        message.reply_text("I can't seem to find this user")
        return ""
    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Wow! let's start banning Admins themselves?...")
        return ""

    if user_id == context.bot.id:
        message.reply_text("I'm not gonna BAN myself, are you crazy or wot?")
        return ""

    if not reason:
        message.reply_text("You haven't specified a time to ban this user for!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    reason = split_reason[1] if len(split_reason) > 1 else ""
    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = f"<b>{html.escape(chat.title)}:</b>\n#TEMP BANNED\n<b>Admin:</b> {mention_html(user.id, user.first_name)}\n<b>User:</b> {mention_html(member.user.id, member.user.first_name)} (<code>{member.user.id}</code>)\n<b>Time:</b> {time_val}"
    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    try:
        chat.kick_member(user_id, until_date=bantime)
        #context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text(f"Banned! User will be banned for {time_val}.")
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(f"Goodbye.. we'll meet after {time_val}.", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Well damn, I can't ban that user.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
@typing_action
def kick(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    if user_can_ban(chat, user, context.bot.id) is False:
    	message.reply_text("You don't have enough rights to kick users!")
    	return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        message.reply_text("I can't seem to find this user")
        return ""
    if is_user_ban_protected(chat, user_id):
        message.reply_text("Yeahh... let's start kicking admins?")
        return ""

    if user_id == context.bot.id:
        message.reply_text("Yeahhh I'm not gonna do that")
        return ""

    if res := chat.unban_member(user_id):
        #context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        context.bot.sendMessage(
            chat.id,
            f"Untill we meet again {mention_html(member.user.id, member.user.first_name)}.",
            parse_mode=ParseMode.HTML,
        )
        log = f"<b>{html.escape(chat.title)}:</b>\n#KICKED\n<b>Admin:</b> {mention_html(user.id, user.first_name)}\n<b>User:</b> {mention_html(member.user.id, member.user.first_name)} (<code>{member.user.id}</code>)"
        if reason:
            log += f"\n<b>Reason:</b> {reason}"

        return log

    else:
        message.reply_text("Get Out!.")

    return ""


@run_async
@bot_admin
@can_restrict
@loggable
@typing_action
def banme(update, context):
    user_id = update.effective_message.from_user.id
    chat = update.effective_chat
    user = update.effective_user
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("Yeahhh.. not gonna ban an admin.")
        return

    if res := update.effective_chat.kick_member(user_id):
        update.effective_message.reply_text("Yes, you're right! GTFO..")
        return f"<b>{html.escape(chat.title)}:</b>\n#BANME\n<b>User:</b> {mention_html(user.id, user.first_name)}\n<b>ID:</b> <code>{user_id}</code>"
    else:
        update.effective_message.reply_text("Huh? I can't :/")


@run_async
@bot_admin
@can_restrict
@typing_action
def kickme(update, context):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("Yeahhh.. not gonna kick an admin.")
        return

    if res := update.effective_chat.unban_member(user_id):
        update.effective_message.reply_text("Yeah, you're right Get Out!..")
    else:
        update.effective_message.reply_text("Huh? I can't :/")


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
@typing_action
def unban(update, context):
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    args = context.args

    if user_can_ban(chat, user, context.bot.id) is False:
    	message.reply_text("You don't have enough rights to unban people here!")
    	return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        message.reply_text("I can't seem to find this user")
        return ""
    if user_id == context.bot.id:
        message.reply_text("How would I unban myself if I wasn't here...?")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text("Why are you trying to unban someone who's already in this chat?")
        return ""

    chat.unban_member(user_id)
    message.reply_text("Done, they can join again!")

    log = f"<b>{html.escape(chat.title)}:</b>\n#UNBANNED\n<b>Admin:</b> {mention_html(user.id, user.first_name)}\n<b>User:</b> {mention_html(member.user.id, member.user.first_name)} (<code>{member.user.id}</code>)"
    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    return log


__help__ = """

Some people need to be publicly banned; spammers, annoyances, or just trolls.
This module allows you to do that easily, by exposing some common actions, so everyone will see!

 × /kickme: Kicks the user who issued the command
 × /banme: Bans the user who issued the command
*Admin only:*
 × /ban <userhandle>: Bans a user. (via handle, or reply)
 × /tban <userhandle> x(m/h/d): Bans a user for x time. (via handle, or reply). m = minutes, h = hours, d = days.
 × /unban <userhandle>: Unbans a user. (via handle, or reply)
 × /kick <userhandle>: Kicks a user, (via handle, or reply)

An example of temporarily banning someone:
`/tban @username 2h`; this bans a user for 2 hours.
"""

__mod_name__ = "Bans"

BAN_HANDLER = CommandHandler("ban", ban, pass_args=True, filters=Filters.group)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"], temp_ban, pass_args=True, filters=Filters.group)
KICK_HANDLER = CommandHandler("kick", kick, pass_args=True, filters=Filters.group)
UNBAN_HANDLER = CommandHandler("unban", unban, pass_args=True, filters=Filters.group)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.group)
BANME_HANDLER = DisableAbleCommandHandler("banme", banme, filters=Filters.group)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(BANME_HANDLER)
