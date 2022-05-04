import html
from typing import Optional, List
from telegram import Bot, Chat, Update, ParseMode
from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html

from cinderella import dispatcher, BAN_STICKER, KICK_STICKER, LOGGER, SUDO_USERS
from cinderella.modules.disable import DisableAbleCommandHandler
from cinderella.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat
from cinderella.modules.helper_funcs.extraction import extract_user_and_text
from cinderella.modules.helper_funcs.string_handling import extract_time
from cinderella.modules.log_channel import loggable, gloggable


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    chat_name = chat.title or chat.first or chat.username
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("İstifadəçiyə istinad edilmir.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User tapılmadı":
            message.reply_text("Bu useri tapa bilmirəm.")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Admini tag edə bilmərəm.")
        return ""
    
    if user_id == 1118936839:
        message.reply_text("Onu ban edə bilmərəm. Xatasını məndən uzaq elə :)")
        return ""
    
    if user_id == bot.id:
        message.reply_text("Özümü ban edəəcm? Sən öl bu karona camaatın başını xarab edib də!")
        return ""

    log = "<b>{}:</b>" \
          "\n#BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Səbəb:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        bot.send_sticker(chat.id, BAN_STICKER)  
        bot.sendMessage(chat.id, "🔨 {} banlandı}!".format(mention_html(member.user.id, member.user.first_name), mention_html(user.id, user.first_name)),
                        parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Mesaj tapılmadı":
            # Do not reply
            message.reply_text('Banlandı!', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Ban edə bilmədim.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    chat_name = chat.title or chat.first or chat.username
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("İstifadəçiyə istinad edilmir.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User tapılmadı":
            message.reply_text("Bu useri tapa bilmirəm.")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Admini tag edə bilmərəm.")
        return ""
    
    if user_id == 1118936839:
        message.reply_text("Onu ban edə bilmərəm. Xatasını məndən uzaq elə :)")
        return ""
    
    if user_id == bot.id:
        message.reply_text("Özümü ban edəəcm? Sən öl bu karona camaatın başını xarab edib də!")
        return ""

    log = "<b>{}:</b>" \
          "\n#BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Səbəb:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        bot.send_sticker(chat.id, BAN_STICKER)  
        bot.sendMessage(chat.id, "🔨 {} Banlandı}!".format(mention_html(member.user.id, member.user.first_name), mention_html(user.id, user.first_name)),
                        parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Mesaj tapılmadı":
            # Do not reply
            message.reply_text('Banlandı!', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Ban edə bilmədim.")

    return ""



@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def kick(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    chat_name = chat.title or chat.first or chat.username
    
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id):
        message.reply_text("I really wish I could kick admins...")
        return ""

    if user_id == bot.id:
        message.reply_text("Yeahhh I'm not gonna do that")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        bot.send_sticker(chat.id, KICK_STICKER)  # banhammer marie sticker
        bot.sendMessage(chat.id, "{} has been Kicked by {}!".format(mention_html(member.user.id, member.user.first_name), mention_html(user.id, user.first_name)),
                        parse_mode=ParseMode.HTML)
        log = "<b>{}:</b>" \
              "\n#KICKED" \
              "\n<b>Admin:</b> {}" \
              "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                           mention_html(user.id, user.first_name),
                                                           mention_html(member.user.id, member.user.first_name),
                                                           member.user.id)
        if reason:
            log += "\n<b>Reason:</b> {}".format(reason)

        return log

    else:
        message.reply_text("Well damn, I can't kick that user.")

    return ""


@run_async
@bot_admin
@can_restrict
def kickme(bot: Bot, update: Update):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("Səni ban etmək istəyirəm əslində...Heyif ki, adminsən")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("No problem.")
    else:
        update.effective_message.reply_text("Nə? Mən bunu edə bilmərəm:/")


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def sban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    
    update.effective_message.delete()

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User tapılmadı":
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        return ""

    if user_id == bot.id:
        return ""

    log = "<b>{}:</b>" \
          "\n#SILENT BAN" \
          "\n<b>• Admin:</b> {}" \
          "\n<b>• User:</b> {}" \
          "\n<b>• ID:</b> <code>{}</code>".format(html.escape(chat.title), mention_html(user.id, user.first_name), 
                                                  mention_html(member.user.id, member.user.first_name), user_id)
    if reason:
        log += "\n<b>•Səbəb:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        return log

    except BadRequest as excp:
        if excp.message == "Mesaj tapılmadı":
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id, excp.message)       
    return ""

@run_async
@bot_admin
@can_restrict
def kickme(bot: Bot, update: Update):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("Səni ban etmək istəyirəm əslində...Heyif ki, adminsən")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("No problem.")
    else:
        update.effective_message.reply_text("Nə? Mən bunu edə bilmərəm:/")



@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def unban(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User tapılmadı":
            message.reply_text("Bu istifadəçini tapa bilmirəm")
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text("Burda olmadığım halda özümü necə unban edim hə? Bilirəm beynin yandı.")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text("Qrupda vcar da. Nəyini unban edəcəksən?")
        return ""

    chat.unban_member(user_id)
    message.reply_text("Qoşulsun da!")

    log = "<b>{}:</b>" \
          "\n#UNBANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Səbəb:</b> {}".format(reason)

    return log
@run_async
@bot_admin
@can_restrict
@gloggable
def selfunban(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message
    user = update.effective_user

    if user.id not in SUDO_USERS:
        return

    try:
        chat_id = int(args[0])
    except:
        message.reply_text("Düzgün ID ver.")
        return

    chat = bot.getChat(chat_id)

    try:
        member = chat.get_member(user.id)
    except BadRequest as excp:
        if excp.message == "User tapılmadı":
            message.reply_text("Bu istifadəçini tapa bilmirəm")
            return
        else:
            raise

    if is_user_in_chat(chat, user.id):
        message.reply_text("Burdasan da. Ehh sən öl deyirəm karona camaatın başını xarab eliyibe")
        return

    chat.unban_member(user.id)
    message.reply_text("Səni unban elədim.")

    log = (f"<b>{html.escape(chat.title)}:</b>\n"
           f"#UNBANNED\n"
           f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}")

    return log


__help__ = """
 Kömək
 - /kickme: səni qrupdan çıxarır
 - /banme: Sənə ban atır.

*Yalnız admin:*
 - /ban <username>: Useri ban edir
  -/sban <username>: Sakit ban edir
 - /tban <username> x(m/h/d): Müəyyən müddət ərzində ban edir. m = dəqiqə, h = saat, d = gün.
 - /unban <username>: Unban edir
 - /kick <username>: Kick edir
"""

__mod_name__ = "BAN"

BAN_HANDLER = CommandHandler("ban", ban, pass_args=True, filters=Filters.group)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"], temp_ban, pass_args=True, filters=Filters.group)
KICK_HANDLER = CommandHandler("kick", kick, pass_args=True, filters=Filters.group)
UNBAN_HANDLER = CommandHandler("unban", unban, pass_args=True, filters=Filters.group)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.group)
BANME_HANDLER = DisableAbleCommandHandler("banme", banme, filters=Filters.group)
SBAN_HANDLER = CommandHandler("sban", sban, pass_args=True, filters=Filters.group)
ROAR_HANDLER = CommandHandler("roar", selfunban, pass_args=True)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(BANME_HANDLER)
dispatcher.add_handler(SBAN_HANDLER)
dispatcher.add_handler(ROAR_HANDLER)
