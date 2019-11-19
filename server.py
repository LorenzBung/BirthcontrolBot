from bot import telegram_chatbot
import threading
import dateutil.parser
import datetime as dt
import time

bot = telegram_chatbot()
lock = threading.Lock()


def make_reply(msg, sender):
    reply = None
    if msg is not None:
        if msg == "/help":
            return "Hello! I will remind you to take your birth control on a daily basis.\n\n" \
                "You can use the following commands to control me:\n" \
                "💊 /start - To start the pill reminders.\n" \
                "⏰ /settime - If you set a wrong time, you can re-set it with this command.\n" \
                "🛑 /stop - Stop getting reminders and delete your cycle.\n" \
                "❓ /help - This help message you're seeing right now."
        if bot.status.get(sender, "") == "set_time":
            lock.acquire()
            try:
                try:
                    time = dateutil.parser.parse(msg, dayfirst=True)
                    bot.time[sender] = time
                    bot.reminder[sender] = time.replace(day=dt.datetime.utcnow().day)
                    bot.status[sender] = "running"
                    add_reminder(sender, msg)
                    print("Set time for {}. Start: {}, Reminder: {}".format(sender, bot.time[sender], bot.reminder[sender]))
                    return "Set starting date to {}.\n\nOkay, I will remind you at {:02}:{:02} if you have to take a pill.".format(bot.time[sender], bot.time[sender].hour, bot.time[sender].minute)
                except Exception as e:
                    print(e)
                    return "Please enter in a valid format. Examples: 16.09.2019 23:12 or 16/09/2019 14:27"
            finally:
                lock.release()
        elif msg == "/start":
            bot.status[sender] = "set_time"
            return "Hello! I will remind you to take your birth control on a daily basis.\n\nWhen was the first time you took the pill in this cycle? Please enter time in UTC. (Examples: 16.09.2019 23:12 or 16/09/2019 14:27)"
        elif msg == "/settime":
            bot.status[sender] = "set_time"
            return "When was the first time you took the pill in this cycle? Please enter time in UTC. (Examples: 16.09.2019 23:12 or 16/09/2019 14:27)"
        elif msg == "/stop":
            lock.acquire()
            try:
                try:
                    bot.status.pop(sender)
                    bot.time.pop(sender)
                    bot.reminder.pop(sender)
                    remove_reminder(sender)
                    print("Removed {}.".format(sender))
                    return "Okay, I will stop reminding you."
                except KeyError:
                    return "Okay, I will stop reminding you."
            finally:
                lock.release()


def handle_reminders():
    while True:
        lock.acquire()
        try:
            for sender in list(bot.status.keys()):
                try:
                    cycle_day = (dt.datetime.now() - bot.time[sender]).days % 28
                    if cycle_day < 21:
                        if bot.reminder[sender] <= dt.datetime.utcnow():
                            tomorrow = dt.datetime.utcnow() + dt.timedelta(days=1)
                            bot.reminder[sender] = bot.reminder[sender].replace(day=tomorrow.day)
                            print("Sent reminder to {}.".format(sender))
                            bot.send_message("💊 Pill reminder! Current day in cycle: {}".format(cycle_day + 1), sender)
                except KeyError:
                    pass
        finally:
            lock.release()
        time.sleep(1)


def handle_messages():
    update_id = None
    while True:
        updates = bot.get_updates(offset=update_id)
        updates = updates["result"]
        if updates:
            for item in updates:
                update_id = item["update_id"]
                try:
                    message = str(item["message"]["text"])
                except:
                    message = None
                sender = item["message"]["from"]["id"]
                reply = make_reply(message, sender)
                bot.send_message(reply, sender)
        time.sleep(1)


def load_reminders():
    try:
        with open(".BirthcontrolBot_reminders", "r") as file:
            for line in file:
                try:
                    id, time = line.split("\t")
                    bot.time[id] = dateutil.parser.parse(time, dayfirst=True)
                    bot.reminder[id] = dt.datetime.now()
                    bot.status[id] = "running"
                except:
                    pass
    except FileNotFoundError:
        pass

def add_reminder(id, time):
    with open(".BirthcontrolBot_reminders", "a") as file:
        file.write(id + "\t" + time + "\n")

def remove_reminder(id):
    with open(".BirthcontrolBot_reminders", "w") as file:
        for line in file:
            if not line.startswith(id):
                file.write(line)


if __name__ == "__main__":
    load_reminders()
    message_thread = threading.Thread(target=handle_messages)
    reminder_thread = threading.Thread(target=handle_reminders)
    message_thread.start()
    reminder_thread.start()
