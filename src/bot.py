import json
from io import open
from datetime import datetime
from os.path import abspath

from telegram.ext import ContextTypes
from telegram import Chat, Message, Update, User

from lib.bot.config import (
    ORG_CHAT_ID,
    BOT_NAME,
    BOT_TELEGRAM_HANDLE,
    BOT_CORE_SYSTEM,
    ORG_CHAT_TITLE,
    ORG_CHAT_HISTORY_FILEPATH,
    bot_response,
)
from lib.bot.utils import (
    deconstruct_error,
    get_chat_admins,
    parse_message,
    parse_message_data,
    parse_chat,
    parse_chat_data,
    parse_user,
    parse_user_data,
)
from lib.abbit import Abbit
from lib.utils import try_get
from constants import HELP_MENU, THE_CREATOR
from lib.logger import debug_logger, error_logger

now = datetime.now()
abbit: Abbit = Abbit(BOT_NAME, BOT_TELEGRAM_HANDLE, BOT_CORE_SYSTEM, ORG_CHAT_ID)
ORG_CHAT_FILEPATH = abspath(ORG_CHAT_HISTORY_FILEPATH)
MATRIX_IMG_FILEPATH = abspath("assets/unplugging_matrix.jpg")


async def handle_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    debug_logger.log(update)
    debug_logger.log(context)
    answer = abbit.chat_history_completion()
    if not answer:
        stopped = abbit.stop()
        debug_logger.log(f"handle_message => abbit={abbit} stopped={stopped}")
        update.message.reply_text(
            "Something went wrong. Please try again or contact @ATLBitLab"
        )
        return await context.bot.send_message(
            chat_id=THE_CREATOR,
            text=f"{abbit.name} completion failed ⛔️: abbit={abbit} stopped={stopped} answer={answer}",
        )
    return await update.message.reply_text(answer)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fn = "handle_message =>"
    try:
        message: Message = parse_message(update)
        message_data: dict = parse_message_data(message)
        message_text: str = try_get(message_data, "text")
        message_date: str = try_get(message_data, "date")
        debug_logger.log(f"{fn} message={message}")
        debug_logger.log(f"{fn} message_data={message_data}")
        debug_logger.log(f"{fn} message_text={message_text}")
        debug_logger.log(f"{fn} message_date={message_date}")
        chat: Chat = parse_chat(update, message)
        chat_data: dict = parse_chat_data(chat)
        chat_id: int = try_get(chat_data, "chat_id", default=ORG_CHAT_ID)
        chat_title: str = try_get(chat_data, "chat_title", default=ORG_CHAT_TITLE)
        debug_logger.log(f"{fn} chat={chat}")
        debug_logger.log(f"{fn} chat_data={chat_data}")
        debug_logger.log(f"{fn} chat_id={chat_id}")
        debug_logger.log(f"{fn} chat_title={chat_title}")
        user: User = parse_user(message)
        user_data: dict = parse_user_data(user)
        user_id: int = try_get(user_data, "user_id")
        username: str = try_get(user_data, "username")
        debug_logger.log(f"{fn} user={user}")
        debug_logger.log(f"{fn} user_data={user_data}")
        debug_logger.log(f"{fn} user_id={user_id}")
        debug_logger.log(f"{fn} username={username}")
        blixt_message = json.dumps(
            {
                "message_text": message_text,
                "message_date": message_date,
                "chat_id": chat_id,
                "chat_title": chat_title,
                "user_id": user_id,
                "username": username,
            }
        )
        debug_logger.log(f"{fn} blixt_message={blixt_message}")
        blixt_chat = open(ORG_CHAT_FILEPATH, "a")
        blixt_chat.write(blixt_message + "\n")
        blixt_chat.close()
        reply_to_message = try_get(message, "reply_to_message")
        reply_to_message_text = try_get(reply_to_message, "text", default="") or ""
        reply_to_message_from = try_get(reply_to_message, "from")
        reply_to_message_from_bot = try_get(reply_to_message_from, "is_bot")
        reply_to_message_bot_handle = try_get(reply_to_message_from, "username")
        debug_logger.log(f"{fn} reply_to_message={reply_to_message}")
        debug_logger.log(f"{fn} reply_to_message_text={reply_to_message_text}")
        debug_logger.log(f"{fn} reply_to_message_from={reply_to_message_from}")
        debug_logger.log(f"{fn} reply_from_bot={reply_to_message_from_bot}")
        debug_logger.log(f"{fn} reply_bot_username={reply_to_message_bot_handle}")
        abbit_tagged = BOT_TELEGRAM_HANDLE in message_text
        reply_to_abbit = reply_to_message_bot_handle == abbit.handle
        started, sent_intro = abbit.status()
        if abbit_tagged or reply_to_abbit:
            if not started and not sent_intro:
                debug_logger.log(f"{fn} Abbot not ready")
                debug_logger.log(f"{fn} sent_intro={sent_intro}")
                debug_logger.log(f"{fn} started={started}")
                debug_logger.log(f"{fn} abbit={abbit.__str__()}")
                hello = abbit.hello()
                hello = "".join(hello)
                debug_logger.log(f"{fn} hello={hello}")
                return await update.message.reply_text(hello)
            elif started and sent_intro:
                abbit_message = {
                    "role": "user",
                    "content": f"{message_text} from {username} on {message_date}",
                }
                debug_logger.log(f"{fn} abbit_message={abbit_message}")
                abbit.update_chat_history(abbit_message)

                return await handle_mention(update, context)

    except Exception as exception:
        status = abbit.status()
        cause, traceback, args = deconstruct_error(exception)
        error_msg = f"args={args}\n" f"cause={cause}\n" f"traceback={traceback}"
        error_logger.log(f"{fn} Error={exception}, ErrorMessage={error_msg}")
        error_logger.log(f"{fn} abbit={abbit} status={status}")
        await context.bot.send_message(chat_id=THE_CREATOR, text=exception)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fn = "help =>"
    try:
        message: Message = parse_message(update)
        message_data: dict = parse_message_data(message)
        chat: Chat = parse_chat(update, message)
        chat_data: int = parse_chat_data(chat)
        user: User = parse_user(message)
        user_data: dict = parse_user_data(user)
        all_data = dict(**message_data, **chat_data, **user_data)
        for k, v in all_data.items():
            debug_logger.log(f"{fn} {k}={v}")
        return await update.message.reply_text(HELP_MENU)
    except Exception as exception:
        error_logger.log(f"{fn} raw exception={exception}")
        cause, traceback, args = deconstruct_error(exception)
        error_msg = f"args={args}\n" f"cause={cause}\n" f"traceback={traceback}"
        error_logger.log(f"{fn} Error={exception}, ErrorMessage={error_msg}")
        await context.bot.send_message(
            chat_id=THE_CREATOR, text=f"Error={exception} ErrorMessage={error_msg}"
        )
        raise exception


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fn = "start =>"
    try:
        message: Message = parse_message(update)
        message_data: dict = parse_message_data(message)
        message_text: str = try_get(message_data, "text")
        message_date: str = try_get(message_data, "date")
        chat: Chat = parse_chat(update, message)
        chat_data: dict = parse_chat_data(chat)
        chat_id = try_get(chat_data, "chat_id", default=ORG_CHAT_ID)
        user: User = parse_user(message)
        user_data: dict = parse_user_data(user)
        user_id = try_get(user_data, "user_id")
        username: str = try_get(user_data, "username")
        chat_admin_data: dict = get_chat_admins(chat_id, context)
        chat_admin_ids = try_get(chat_admin_data, "ids")
        chat_admin_usernames = try_get(chat_admin_data, "usernames")
        is_chat_admin = user_id in chat_admin_ids or username in chat_admin_usernames
        all_data = dict(**message_data, **chat_data, **user_data, **chat_admin_data)
        for k, v in all_data.items():
            debug_logger.log(f"{fn} {k}={v}")
        if not is_chat_admin:
            return await update.message.reply_text(bot_response("forbidden", 0))
        start_intro = abbit.start_command()
        if not start_intro:
            msg = f"started={abbit.started} sent_intro={abbit.sent_intro}"
            error_logger.log(msg)
            raise Exception(f"failed to start: {msg}")
        abbit_message = dict(
            role="user",
            content=f"{message_text} from {username} on {message_date}",
        )
        debug_logger.log(f"{fn} abbit_message={abbit_message}")
        abbit.update_chat_history(abbit_message)
        await message.reply_photo(
            MATRIX_IMG_FILEPATH, f"Unplugging {BOT_NAME} from the Matrix"
        )
        response = abbit.chat_history_completion()
        if not response:
            abbit.stop()
            response = f"{abbit.name} start failed ⛔️! {bot_response('fail', 0)}."
            abbit_str = abbit.__str__()
            error_logger.log(f"{fn} abbit={abbit_str}")
            await context.bot.send_message(
                chat_id=THE_CREATOR, text=f"abbit={abbit_str} response={response}"
            )
        await message.reply_text(response)
    except Exception as exception:
        error_logger.log(f"start => Raw exception={exception}")
        cause, traceback, args = deconstruct_error(exception)
        error_msg = f"args={args}\n" f"cause={cause}\n" f"traceback={traceback}"
        error_logger.log(f"start => Error={exception}, ErrorMessage={error_msg}")
        await context.bot.send_message(
            chat_id=THE_CREATOR, text=f"Error={exception} ErrorMessage={error_msg}"
        )
        raise exception


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fn = "stop =>"
    try:
        # message data
        message: Message = parse_message(update)
        message_data: dict = parse_message_data(message)
        # chat data
        chat: Chat = parse_chat(update, message)
        chat_data: dict = parse_chat_data(chat)
        chat_id = try_get(chat_data, "chat_id", default=ORG_CHAT_ID)
        # user data
        user: User = parse_user(message)
        user_data: dict = parse_user_data(user)
        user_id = try_get(user_data, "user_id")
        username: str = try_get(user_data, "username")
        # chat admin data
        chat_admin_data: dict = get_chat_admins(chat_id, context)
        chat_admin_ids = try_get(chat_admin_data, "ids")
        chat_admin_usernames = try_get(chat_admin_data, "usernames")
        is_chat_admin = user_id in chat_admin_ids or username in chat_admin_usernames
        # log all data for debugging
        all_data = dict(**message_data, **chat_data, **user_data, **chat_admin_data)
        for k, v in all_data.items():
            debug_logger.log(f"{fn} {k}={v}")
        # check sender is chat admin
        if not is_chat_admin:
            return await update.message.reply_text(bot_response("forbidden", 0))
        started = abbit.started
        if not started:
            debug_logger.log(f"{fn} Abbit not started! abbit.started={abbit.started}")
            return await message.reply_text(
                f"/stop failed! Abbit not started! Have you run /start yet?"
                "If so, please try again later or contact @nonni_io"
            )
        stopped = abbit.stop()
        if not stopped:
            err_msg = f"{fn} not stopped! abbit={abbit}, stopped={stopped}"
            error_logger.log(err_msg)
            await message.reply_text(
                "/stop failed! Something went wrong."
                "Please try again later or contact @nonni_io"
            )
            return await context.bot.send_message(chat_id=THE_CREATOR, text=err_msg)
        await message.reply_photo(
            f"Pluggin {BOT_NAME} back into the matrix."
            "To restart, have an admin run the /start command."
        )
    except Exception as exception:
        cause, traceback, args = deconstruct_error(exception)
        error_msg = f"args={args}\n" f"cause={cause}\n" f"traceback={traceback}"
        error_logger.log(f"{fn} Error={exception}, ErrorMessage={error_msg}")
        await context.bot.send_message(
            chat_id=THE_CREATOR, text=f"Error={exception} ErrorMessage={error_msg}"
        )
        raise exception