import html
import subprocess
import importlib
import os
import json
import sys
import requests

from typing import List
from time import sleep

from telegram import Bot, Update, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters, run_async
from telegram.utils.helpers import escape_markdown, mention_html

from cinderella import dispatcher, WHITELIST_USERS, SUPPORT_USERS, SUDO_USERS, DEV_USERS, OWNER_ID, TOKEN
from cinderella.__main__ import IMPORTED, HELPABLE, MIGRATEABLE, STATS, USER_INFO, DATA_IMPORT, DATA_EXPORT, CHAT_SETTINGS, USER_SETTINGS 
from cinderella.modules.disable import DisableAbleCommandHandler
from cinderella.modules.log_channel import loggable, gloggable
from cinderella.modules.helper_funcs.chat_status import bot_admin, can_promote, user_admin, can_pin, sudo_plus, dev_plus, connection_status
from cinderella.modules.helper_funcs.extraction import extract_user, extract_user_and_text


@run_async
@dev_plus
def gitpull(bot: Bot, update: Update):

    sent_msg = update.effective_message.reply_text("Bütün dəyişiklikləri pultdan götürün və sonra yenidən başlamağa cəhd edin.")
    subprocess.Popen('git pull', stdout=subprocess.PIPE, shell=True)

    sent_msg_text = sent_msg.text + "\n\nDəyişikliklər edildi... Güman edirəm.. Yenidən başladın "

    for i in reversed(range(5)):
        sent_msg.edit_text(sent_msg_text + str(i + 1))
        sleep(1)
    
    sent_msg.edit_text("Yenidən başladıldı")
    
    os.system('restart.bat')
    os.execv('start.bat', sys.argv)


@run_async
@dev_plus
def restart(bot: Bot, update: Update):

    update.effective_message.reply_text("Yeni nümunəyə başlayıram və bunu bağlayıram")

    os.system('restart.bat')
    os.execv('start.bat', sys.argv)


@run_async
@dev_plus
def load(bot: Bot, update: Update):

    message = update.effective_message
    text = message.text.split(" ", 1)[1]
    load_messasge = message.reply_text(f"Modul yüklənir : <b>{text}</b>", parse_mode=ParseMode.HTML)
    
    try:
        imported_module = importlib.import_module("cinderella.modules." + text)
    except:
        load_messasge.edit_text("Belə bir modul var?")
        return

    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if not imported_module.__mod_name__.lower() in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        load_messasge.edit_text("Modul artıq yükləndi.")
        return
    
    if "__handlers__" in dir(imported_module):
        handlers = imported_module.__handlers__
        for handler in handlers:
            if type(handler) != tuple:
                dispatcher.add_handler(handler)
            else:
                handler_name, priority = handler
                dispatcher.add_handler(handler_name, priority)
    else:
        IMPORTED.pop(imported_module.__mod_name__.lower())
        load_messasge.edit_text("Modulda müəyyən edilmiş idarəedici siyahısı yoxdur!")
        return

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    load_messasge.edit_text("Modul uğurla yükləndi : <b>{}</b>".format(text), parse_mode=ParseMode.HTML)


@run_async
@dev_plus
def unload(bot: Bot, update: Update):

    message = update.effective_message
    text = message.text.split(" ", 1)[1]
    unload_messasge = message.reply_text(f"Modul silinir : <b>{text}</b>", parse_mode=ParseMode.HTML)

    try:
        imported_module = importlib.import_module("cinderella.modules." + text)
    except:
        unload_messasge.edit_text("Belə modul varmı?")
        return

    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__
    
    if imported_module.__mod_name__.lower() in IMPORTED:
        IMPORTED.pop(imported_module.__mod_name__.lower())
    else:
        unload_messasge.edit_text("Yüklənməmiş modulu silə bilmədim.")
        return
    
    if "__handlers__" in dir(imported_module):
        handlers = imported_module.__handlers__
        for handler in handlers:
            if type(handler) == bool:
                unload_messasge.edit_text("Bu modul silinə bilməz!")
                return
            elif type(handler) != tuple:
                dispatcher.remove_handler(handler)
            else:
                handler_name, priority = handler
                dispatcher.remove_handler(handler_name, priority)
    else:
        unload_messasge.edit_text("Modulda müəyyən edilmiş idarəedici siyahısı yoxdur!")
        return

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE.pop(imported_module.__mod_name__.lower())

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.remove(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.remove(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.remove(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.remove(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.remove(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS.pop(imported_module.__mod_name__.lower())

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS.pop(imported_module.__mod_name__.lower())

    unload_messasge.edit_text(f"Modul uğurla silindi : <b>{text}</b>", parse_mode=ParseMode.HTML)


@run_async
@connection_status
@sudo_plus
def listmodules(bot: Bot, update: Update):

    message = update.effective_message
    module_list = []

    for helpable_module in HELPABLE:
        helpable_module_info = IMPORTED[helpable_module]
        file_info = IMPORTED[helpable_module_info.__mod_name__.lower()]
        file_name = file_info.__name__.rsplit("cinderella.modules.", 1)[1]
        mod_name = file_info.__mod_name__
        module_list.append(f'- <code>{mod_name} ({file_name})</code>\n')
    module_list = "Following modules are loaded : \n\n" + ''.join(module_list)
    message.reply_text(module_list, parse_mode=ParseMode.HTML)


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def promote(bot: Bot, update: Update, args: List[str]) -> str:
    
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    log_message = ""
    
    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text("Siz istifadəçiyə istinad etmirsiniz🤷🏻‍♂.")
        return log_message

    try:
        user_member = chat.get_member(user_id)
    except:
        return log_message
    
    if user_member.status == 'administrator' or user_member.status == 'creator':
        message.reply_text("Bir admini necə tanıtdırım?")
        return log_message

    if user_id == bot.id:
        message.reply_text("Özümə yetki verə bilmərəm. Bunun üçün başqa birini tapın")
        return log_message

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    try:
        bot.promoteChatMember(chat.id, user_id,
                            can_change_info=bot_member.can_change_info,
                            can_post_messages=bot_member.can_post_messages,
                            can_edit_messages=bot_member.can_edit_messages,
                            can_delete_messages=bot_member.can_delete_messages,
                            can_invite_users=bot_member.can_invite_users,
                            # can_promote_members=bot_member.can_promote_members,
                            can_restrict_members=bot_member.can_restrict_members,
                            can_pin_messages=bot_member.can_pin_messages)
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            message.reply_text("Qrupda olmayana yetki verə bilmərəm")
            return log_message
        else:
            message.reply_text("Xata.")
            return log_message
                         
    bot.sendMessage(chat.id, " <b>{}</b>uğurla yetkiləndirildi!".format(user_member.user.first_name or user_id), parse_mode=ParseMode.HTML)
    
    log_message += "<b>{}:</b>" \
                   "\n#YETKİLƏNDİRİLDİ" \
                   "\n<b>Admin:</b> {}" \
                   "\n<b>User:</b> {}".format(html.escape(chat.title),
                                                mention_html(user.id, user.first_name),
                                                mention_html(user_member.user.id, user_member.user.first_name))

    return log_message


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def demote(bot: Bot, update: Update, args: List[str]) -> str:

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    log_message = ""

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("Siz istifadəçiyə istinad etmirsiniz")
        return log_message

    try:
        user_member = chat.get_member(user_id)
    except:
        return log_message
    
    if user_member.status == 'creator':
        message.reply_text("Qrupu bu hesab yaradıb. Onu necə adminlikdən silim?")
        return log_message

    if not user_member.status == 'administrator':
        message.reply_text("Yetkisi olmayanın yetkisini almaq istəyirsən? Dolamısan məni?")
        return log_message

    if user_id == bot.id:
        message.reply_text("Mənim yetkimi alırsan? Nəyimi bəyənmədin? Bunu edə bilmərəm mən. Çağır başqası etsin.")
        return log_message

    try:
        bot.promoteChatMember(chat.id, user_id,
                              can_change_info=False,
                              can_post_messages=False,
                              can_edit_messages=False,
                              can_delete_messages=False,
                              can_invite_users=False,
                              can_restrict_members=False,
                              can_pin_messages=False,
                              can_promote_members=False)

        bot.sendMessage(chat.id, "Yetkisi uğurla alındı <b>{}</b>!".format(user_member.user.first_name or user_id), parse_mode=ParseMode.HTML)

        log_message += "<b>{}:</b>" \
                       "\n#DEMOTED" \
                       "\n<b>Admin:</b> {}" \
                       "\n<b>User:</b> {}".format(html.escape(chat.title),
                                                    mention_html(user.id, user.first_name),
                                                    mention_html(user_member.user.id, user_member.user.first_name))
        
        return log_message
    except BadRequest:
        message.reply_text("Yetksini ala bilomədim. Ola bilsin, ya mən yetki verməmişəm, ya da admin deyiləm.")
        return log_message


#Until the library releases the method
@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
def set_title(bot: Bot, update: Update, args: List[str]):

    chat = update.effective_chat
    message = update.effective_message

    user_id, title = extract_user_and_text(message, args)
    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if not user_id:
        message.reply_text("Siz istifadəçiyə istinad etmirsiniz")
        return

    if user_member.status == 'creator':
        message.reply_text("Bu hesab qrupu yaradıb, mən ona xüsusi ad qoya bilmərəm")
        return

    if not user_member.status == 'administrator':
        message.reply_text("Admin olmayanlara xüsusi ad? Məzələnirsən?Yetki ver sonra.")
        return

    if user_id == bot.id:
        message.reply_text("Özüm özümə ad qoya bilmərəm. Mənə yetki verən mənə layiq olanı qoysun")
        return

    if not title:
        message.reply_text("Setting blank title doesn't do anything!")
        return

    if len(title) > 16:
        message.reply_text("The title length is longer than 16 characters.\nTruncating it to 16 characters.")

    result = requests.post(f"https://api.telegram.org/bot{TOKEN}/setChatAdministratorCustomTitle?chat_id={chat.id}&user_id={user_id}&custom_title={title}")
    status = result.json()["ok"]

    if status == True:
        bot.sendMessage(chat.id, "Sucessfully set title for <code>{}</code> to <code>{}</code>!".format(user_member.user.first_name or user_id, title[:16]), parse_mode=ParseMode.HTML)
    else:
        description = result.json()["description"]
        if description == "Bad Request: not enough rights to change custom title of the user":
            message.reply_text("Yetki vermədiyim adminlərə xüsusi ad qoya bilmərəm.")


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def pin(bot: Bot, update: Update, args: List[str]) -> str:

    user = update.effective_user
    chat = update.effective_chat

    is_group = chat.type != "private" and chat.type != "channel"
    prev_message = update.effective_message.reply_to_message

    is_silent = True
    if len(args) >= 1:
        is_silent = not (args[0].lower() == 'notify' or args[0].lower() == 'loud' or args[0].lower() == 'violent')

    if prev_message and is_group:
        try:
            bot.pinChatMessage(chat.id, prev_message.message_id, disable_notification=is_silent)
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        log_message = "<b>{}:</b>" \
                      "\n#Sancıldı" \
                      "\n<b>Admin:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name))
        
        return log_message


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def unpin(bot: Bot, update: Update) -> str:

    chat = update.effective_chat
    user = update.effective_user

    try:
        bot.unpinChatMessage(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise

    log_message = "<b>{}:</b>" \
                  "\n#UNPINNED" \
                  "\n<b>Admin:</b> {}".format(html.escape(chat.title),
                                       mention_html(user.id, user.first_name))

    return log_message

@run_async
@bot_admin
@user_admin
def invite(bot: Bot, update: Update):

    chat = update.effective_chat

    if chat.username:
        update.effective_message.reply_text(chat.username)
    elif chat.type == chat.SUPERGROUP or chat.type == chat.CHANNEL:
        bot_member = chat.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = bot.exportChatInviteLink(chat.id)
            update.effective_message.reply_text(invitelink)
        else:
            update.effective_message.reply_text("Linklə dəvət yetkim yoxdur!")
    else:
        update.effective_message.reply_text("Yalnız supergroup üçün link götürə bilirəm!")

@run_async
@connection_status
def adminlist(bot: Bot, update: Update):
    administrators = update.effective_chat.get_administrators()
    user = update.effective_user
    msg = update.effective_message
    text = "Admins in *{}*:".format(update.effective_chat.title or "this chat")
    for admin in administrators:
        user = admin.user
        status = admin.status
        name = "[{}](tg://user?id={})".format(user.first_name + (user.last_name or ""), user.id)
        if status == "creator":
            text += "\n 🔱 *Yaradıcı*:"
            text += "\n` 🤴🏻 `{} \n\n ⚜️ *Adminlər*:".format(name)
    for admin in administrators:
        user = admin.user
        status = admin.status
        chat = update.effective_chat
        count = chat.get_members_count()
        name = "[{}](tg://user?id={})".format(user.first_name + (user.last_name or ""), user.id)
           
        if status == "administrator":
            text += "\n` 👮🏻‍♂️ `{}".format(name)
            members = "\n\n*Üzvlər:*\n`👨‍👩‍👧‍👦 ` {} users".format(count)
            
    msg.reply_text(text + members, parse_mode=ParseMode.MARKDOWN)

@run_async
@bot_admin
@user_admin
def setchatpic(bot: Bot, update: Update):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    user_member = chat.get_member(user.id)
    if user_member.can_change_info == False:
       msg.reply_text("Qrup məlumatı dəyişə bilməzsən")
       return

    if msg.reply_to_message:
       if msg.reply_to_message.photo:
          pic_id = msg.reply_to_message.photo[-1].file_id
       elif msg.reply_to_message.document:
          pic_id = msg.reply_to_message.document.file_id
       else:
          msg.reply_text("Qrup ikonu olaraq yalnız şəkil qoymaq olar!")
          return
       dlmsg = msg.reply_text("Gözləyin...\nViruslar üçün axtarılır..🔎")
       tpic = bot.get_file(pic_id)
       tpic.download('gpic.png')
       try:
          with open('gpic.png', 'rb') as chatp:
               bot.set_chat_photo(int(chat.id), photo=chatp)
               msg.reply_text("✅Yeni çat ikonu əlavə edildi!")
       except BadRequest as excp:
          msg.reply_text(f"Error! {excp.message}")
       finally:
          dlmsg.delete()
          if os.path.isfile('gpic.png'):
             os.remove("gpic.png")
    else:
          msg.reply_text("Qrup fotosu üçün reply edin!")


@run_async
@bot_admin
@user_admin
def rmchatpic(bot: Bot, update: Update):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    user_member = chat.get_member(user.id)
    if user_member.can_change_info == False:
       msg.reply_text("Qrup ikonunu silmək üçün kifayət qədər yetkiniz yoxdur")
       return
    try:
        bot.delete_chat_photo(int(chat.id))
        msg.reply_text("✅Çat ikonu uöurla silindi!")
    except BadRequest as excp:
       msg.reply_text(f"Error! {excp.message}.")
       return    
    
def __chat_settings__(chat_id, user_id):
    return "Sən adminsən: `{}`".format(
        dispatcher.bot.get_chat_member(chat_id, user_id).status in ("administrator", "creator"))

__help__ = """
 - /adminlist: Admin siyahısını verir

*Yalnız admin*
 - /pin: Reply edilən mesajı sakit pinləyir. Hərkəsi xəbərdar etmək üçün 'loud'və ya 'notify' istifadə edin.
 - /unpin: Pindəki sonuncu mesajı silir
 - /invitelink: Dəvət linki
 - /promote: Reply edilən üzvə yetki verir
 - /demote: Reply edilən üzvün yetkisini alır
 - /settitle: Botun yetki verdiyi hesaba özəl ad verir
 - /setgpic: Reply edilən şəkli qrup ikonu olaraq qoyur.
 - /delgpic: Qrup ikonunu siir. 
"""

ADMINLIST_HANDLER = DisableAbleCommandHandler(["adminlist","admins"], adminlist)

PIN_HANDLER = CommandHandler("pin", pin, pass_args=True, filters=Filters.group)
UNPIN_HANDLER = CommandHandler("unpin", unpin, filters=Filters.group)

INVITE_HANDLER = DisableAbleCommandHandler("invitelink", invite, filters=Filters.group)

PROMOTE_HANDLER = CommandHandler("promote", promote, pass_args=True)
DEMOTE_HANDLER = CommandHandler("demote", demote, pass_args=True)

SET_TITLE_HANDLER = CommandHandler("settitle", set_title, pass_args=True)

GITPULL_HANDLER = CommandHandler("gitpull", gitpull)
RESTART_HANDLER = CommandHandler("restart", restart)

LOAD_HANDLER = CommandHandler("load", load)
UNLOAD_HANDLER = CommandHandler("unload", unload)
LISTMODULES_HANDLER = CommandHandler("listmodules", listmodules)
CHAT_PIC_HANDLER = CommandHandler("setgpic", setchatpic, filters=Filters.group)
DEL_CHAT_PIC_HANDLER = CommandHandler("delgpic", rmchatpic, filters=Filters.group)


dispatcher.add_handler(ADMINLIST_HANDLER)
dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(SET_TITLE_HANDLER)
dispatcher.add_handler(GITPULL_HANDLER)
dispatcher.add_handler(RESTART_HANDLER)
dispatcher.add_handler(LOAD_HANDLER)
dispatcher.add_handler(UNLOAD_HANDLER)
dispatcher.add_handler(LISTMODULES_HANDLER)
dispatcher.add_handler(CHAT_PIC_HANDLER)
dispatcher.add_handler(DEL_CHAT_PIC_HANDLER)


__mod_name__ = "Admin"
