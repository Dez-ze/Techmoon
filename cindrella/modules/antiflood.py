import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler, CommandHandler, run_async
from telegram.utils.helpers import mention_html

from cinderella import dispatcher
from cinderella.modules.helper_funcs.chat_status import is_user_admin, user_admin, can_restrict, can_delete
from cinderella.modules.log_channel import loggable
from cinderella.modules.sql import antiflood_sql as sql

FLOOD_GROUP = 3


@run_async
@loggable
def check_flood(bot: Bot, update: Update) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    if not user:  # ignore channels
        return ""

    # ignore admins
    if is_user_admin(chat, user.id):
        sql.update_flood(chat.id, None)
        return ""

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""
    
    soft_flood = sql.get_flood_strength(chat.id)
    if soft_flood:  # kick
        chat.unban_member(user.id)
        reply = "Sənin çoxlu mesaj atmağını bəyənmədim! {} çıx get!".format(mention_html(user.id, user.first_name))

    else:  # ban
        chat.kick_member(user.id)
        reply = "Sənin çoxlu mesaj atmağını bəyənmədim. {} banlandı!".format(mention_html(user.id, user.first_name))
    try:
        keyboard = []
        msg.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        msg.delete()
        return "<b>{}:</b>" \
               "\n#FLOOD_CTL" \
               "\n<b>• User:</b> {}" \
               "\nQrupda Flood etdi.".format(html.escape(chat.title),
                                             mention_html(user.id, user.first_name))

    except BadRequest:
        msg.reply_text("Mənim insanları atmaq yetkim yoxdur. Ya yetkimi verin, ya da anti-flood rejimini söndürəcəm")
        sql.set_flood(chat.id, 0)
        return "<b>{}:</b>" \
               "\n#INFO" \
               "\nİnsanları atmaq yetkim olmadığı üçün anti-flood rejimi söndürüldü.".format(chat.title)


@run_async
@user_admin
@can_restrict
@loggable
def set_flood(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    if len(args) >= 1:
        val = args[0].lower()
        if val == "off" or val == "no" or val == "0":
            sql.set_flood(chat.id, 0)
            message.reply_text("Anti-flood söndürüldü")

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat.id, 0)
                message.reply_text("Anti-flood söndürüldü")
                return "<b>{}:</b>" \
                       "\n#SETFLOOD" \
                       "\n<b>• Admin:</b> {}" \
                       "\nAnti-flood söndürüldü.".format(html.escape(chat.title), mention_html(user.id, user.first_name))

            elif amount < 1:
                message.reply_text("Anti-flood ya 0 ola bilər(sönülü) ya da 1")
                return ""

            else:
                sql.set_flood(chat.id, amount)
                message.reply_text("Flood əleyhinə yeniləndi və {} olaraq təyin edildi".format(amount))
                return "<b>{}:</b>" \
                       "\n#SETFLOOD" \
                       "\n<b>• Admin:</b> {}" \
                       "\nAnti-flood <code>{}</code> olaraq təyin olundu.".format(html.escape(chat.title),
                                                                    mention_html(user.id, user.first_name), amount)

        else:
            message.reply_text("Tanınmayan arqument - rəqəm, "off" və ya "no" istifadə edin.")
    else:
        message.reply_text("Bir arqument verin! Spam əleyhinə rəqəm təyin edin.\n" \
                           "Məsələn `/setflood 5` ", parse_mode=ParseMode.MARKDOWN)
    return ""


@run_async
def flood(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message # type: Optional[Message]
    limit = sql.get_flood_limit(chat.id)
    if limit == 0:
        update.effective_message.reply_text("Hal-hazırda anti-flood sönülüdür")
    else:
        soft_flood = sql.get_flood_strength(chat.id)
        if soft_flood:
            msg.reply_text(" {} - dan çox mesaj atanı qrupdan çıxarıram " 
                           "Onlar yeindən qoşula bilər".format(limit, parse_mode=ParseMode.MARKDOWN))
        else:
            msg.reply_text("{} - dan çox mesaj atanı qrupdan çıxarıram " 
                           .format(limit, parse_mode=ParseMode.MARKDOWN))

@run_async
@user_admin
@loggable
def set_flood_strength(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    if args:
        if args[0].lower() in ("on", "yes"):
            sql.set_flood_strength(chat.id, False)
            msg.reply_text("Flood limitini keçənlər banlanır")
            return "<b>{}:</b>\n" \
                   "<b>• Admin:</b> {}\n" \
                   "Daha sərt anti-flood rejimini yandırdı. Flood edənlər ban ediləcəkdir".format(html.escape(chat.title),
                                                                            mention_html(user.id, user.first_name))

        elif args[0].lower() in ("off", "no"):
            sql.set_flood_strength(chat.id, True)
            msg.reply_text("Flood limitini keçənlər sadəcə kick edilir. Qrupa yenidən qatıl bilərlər.")
            return "<b>{}:</b>\n" \
                   "<b>• Admin:</b> {}\n" \
                   "Yüngül anti-flood rejimini yandırdı. Flood edənlər kick ediləcək".format(html.escape(chat.title),
                                                                                  mention_html(user.id,
                                                                                               user.first_name))

        else:
            msg.reply_text("Mən yalnız on/yes/no/off anlayıram!")
    else:
        soft_flood = sql.get_flood_strength(chat.id)
        if soft_flood == True:
            msg.reply_text("İstifadəçi flood limitini keçdikdə kick edilir ",
                           parse_mode=ParseMode.MARKDOWN)
                 
        elif soft_flood:
            msg.reply_text("Defolt olaraq flood limitini keçən istifadəçi ban edilir.",
                           parse_mode=ParseMode.MARKDOWN)
        
        elif soft_flood == False:
            msg.reply_text("Fİstifadəçi flood limitini keçdikdə ban edilir",
                           parse_mode=ParseMode.MARKDOWN)
    return ""

def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    soft_flood = sql.get_flood_strength(chat_id)
    if limit == 0:
        return "Flood nəzarəti söndürülb."
    else:
        if soft_flood:
            return " `{}` qədər mesaj atıldıqda flood olaraq hesab olunur və istifadəçi *KİCK* edilir.".format(limit)
        else:
            return "`{}` qədər mesaj atıldıqda flood olaraq hesab olunur və istifadəçi *BAN* edilir.".format(limit)
__help__ = """
Bəzən bir istifadəçi qrupa qoşulub, 100+mesaj atıb qrupu bardaq edir? Antiflood ilə bu bir daha olmayacaq!
Antiflood X sayda mesaj atanlara qarşı tədbir görmək üçündür. Bu zaman istifadəçi *kick* və ya *ban* edilir.
 - /flood: hal-hazırki ayarlara baxmaq
*Yalnız admin:*
 - /setflood <int/'no'/'off'>: antiflood rejimini yandırır və ya söndürür.
 - /strongflood <on/yes/off/no>: Yandırıldıqda X sayda mesaj atan user ban edilir.
"""

__mod_name__ = "ANTIFLOOD"

FLOOD_BAN_HANDLER = MessageHandler(Filters.all & ~Filters.status_update & Filters.group, check_flood)
SET_FLOOD_HANDLER = CommandHandler("setflood", set_flood, pass_args=True, filters=Filters.group)
FLOOD_HANDLER = CommandHandler("flood", flood, filters=Filters.group)
FLOOD_STRENGTH_HANDLER = CommandHandler("strongflood", set_flood_strength, pass_args=True, filters=Filters.group)

dispatcher.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(FLOOD_HANDLER)
dispatcher.add_handler(FLOOD_STRENGTH_HANDLER)
