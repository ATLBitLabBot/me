from cli_args import DEV_MODE, TEST_MODE, TELEGRAM_MODE, NOSTR_MODE
from lib.abbot.exceptions.exception import AbbotException
from lib.logger import debug_bot

# from lib.abbot.nostr_bot import NostrBotBuilder
from lib.abbot.telegram_bot import TelegramBotBuilder

if __name__ == "__main__":
    try:
        # if not DEV_MODE and not TEST_MODE:
        #     raise AbbotException(
        #         "Do not run in production mode unless you are sure: python src/main.py [--telegram | --nostr] [--dev | --test]"
        #     )
        if TELEGRAM_MODE:
            telegram_abbot: TelegramBotBuilder = TelegramBotBuilder()
            telegram_abbot.run()
        # elif NOSTR_MODE:
        #     nostr_abbot: NostrBotBuilder = NostrBotBuilder()
        #     nostr_abbot.add_relays_connect_and_start_client()
        #     nostr_abbot.run()
        # else:
        #     raise AbbotException("Must specify platform: python src/main.py [--telegram | --nostr] [--dev | --test]")
    except KeyboardInterrupt:
        debug_bot.log(__name__, "Interrupt received, shutting down.")
        debug_bot.log(__name__, "Shutting down...")
        debug_bot.log(__name__, "Shutdown complete.")
