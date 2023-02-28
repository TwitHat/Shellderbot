import telegram.ext as tg
from telegram import Update

try:
    from skylee import CUSTOM_CMD
except:
    CUSTOM_CMD = False

CMD_STARTERS = CUSTOM_CMD or '/'


class CustomCommandHandler(tg.CommandHandler):
    def __init__(self, command, callback, **kwargs):
        if "admin_ok" in kwargs:
            del kwargs["admin_ok"]
        super().__init__(command, callback, **kwargs)

    def check_update(self, update):
        if not isinstance(update, Update) or not update.effective_message:
            return
        message = update.effective_message

        if message.text and len(message.text) > 1:
            fst_word = message.text.split(None, 1)[0]
            if len(fst_word) > 1 and any(fst_word.startswith(start) for start in CMD_STARTERS):
                args = message.text.split()[1:]
                command = fst_word[1:].split('@')
                command.append(message.bot.username)  # in case the command was sent without a username

                if (
                    command[0].lower() not in self.command
                    or command[1].lower() != message.bot.username.lower()
                ):
                    return None

                if filter_result := self.filters(update):
                    return args, filter_result
                else:
                    return False
