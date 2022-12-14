import datetime
import logging
import pytz
from telegram import *
from telegram.ext import *
import json
import pandas as pd
import tabulate
import os


def getCurrenttime():
    return datetime.datetime.today()


def getLogindata():
    with open("logindata.json", 'r') as logindata:
        token = json.load(logindata)["TOKEN"]
        return token


def getSchedule():
    with open("scheduleDB.json", 'r') as scheduleDB:
        schedule = json.load(scheduleDB)
        return schedule


def getTodaySchedule(purpose='default'):
    if purpose == 'table':
        a = getSchedule()[str(getCurrenttime().weekday())]
        for key, value in a.items():
            for keys, b in value.items():
                if len(b) > 22:
                    x = list(b)
                    x[b.find(' ', b.find(' ') + 1)] = '\n'
                    b = ''.join(x)
                    value[keys] = b
                    a[key] = value
        return a
    return getSchedule()[str(getCurrenttime().weekday())]


def askSchedule(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='HTML',
                             text=f"<code>{tabulate.tabulate(pd.DataFrame.from_dict(getTodaySchedule(purpose='table'), orient='index'), headers='keys')}</code>")


def askNext(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"Your next class is {list(nextClass()[1].values())[0]['subject']} in {list(nextClass()[1].values())[0]['room']} at {list(nextClass()[1].keys())[0]}.")


def nextClass(date=getCurrenttime().weekday(), time=getCurrenttime()):
    if date == 6 or date == 7:
        return [time, list(getSchedule()['0'].items())[0]]
    elif time.hour >= 20 and time.minute >= 15:
        d = time + datetime.timedelta(days=1)
        d = d.replace(hour=0, minute=0)
        return nextClass(date=d.weekday(), time=d)
    for t, c in {key: value for (key, value) in getTodaySchedule().items() if value['subject'] != ""}.items():
        ctime = time
        h, m = map(int, t.split(':'))
        ctime = ctime.replace(hour=h, minute=m)
        if ctime > time:
            print(t)
            return [ctime,
                    {t: {key: value for (key, value) in getTodaySchedule().items() if value['subject'] != ""}[t]}]


def scheduleNT():
    nxttime = nextClass()
    nttime = datetime.datetime.now()
    if nxttime[0] - datetime.timedelta(minutes=30) < nttime:
        return nextClass(time=getCurrenttime() + datetime.timedelta(minutes=30))
    when = nxttime
    return when


def createJob(update, context):
    context.job_queue.run_once(ntAlarm, when=(scheduleNT()[0] - datetime.timedelta(minutes=30)).astimezone(pytz.UTC),
                               context=update.effective_chat.id, name='nt')


def ntAlarm(context: CallbackContext):
    context.bot.send_message(chat_id="550113618",
                             text=f"You have a {list(scheduleNT()[1].values())[0]['subject']} in 30 minutes at {list(scheduleNT()[1].keys())[0]}!")


def ntList(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=' '.join([str(job.next_t) for job in context.job_queue.jobs()]))


# '''
def main():
    updater = Updater(token=os.environ.get("TOKEN"))
    dispatcher = updater.dispatcher
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    updater.start_polling()
    dispatcher.add_handler(CommandHandler('today', askSchedule))
    dispatcher.add_handler(CommandHandler('next', askNext))
    dispatcher.add_handler(CommandHandler('notify', createJob))
    dispatcher.add_handler(CommandHandler('ntslist', ntList))


#    ntmsg(timep30())


if __name__ == "__main__":
    main()

# '''
