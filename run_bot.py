"""
Скрипт запуска сервиса Sender (сервер бота)
"""
import logging
from datetime import time

from pytz import timezone
from telegram.ext import CallbackQueryHandler
from telegram.ext import Updater, CommandHandler

from app.api_bot import start, set_team, broadcasting_evening_news, callback_change_team, sending_new_incident, \
    helping, job_reading_from_redmine, info_request, callback_news, job_cleaning, broadcasting_create_statistic_in_db, \
    sending_release_notification
from settings import BOT_TOKEN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.info("Бот запускается")
updater = Updater(BOT_TOKEN, use_context=True)

dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", helping))
dispatcher.add_handler(CommandHandler("set_team", set_team))
dispatcher.add_handler(CommandHandler("info_request", info_request))

dispatcher.add_handler(CallbackQueryHandler(callback_change_team, pattern='team'))
dispatcher.add_handler(CallbackQueryHandler(callback_news, pattern='news'))

dispatcher.job_queue.run_repeating(callback=job_reading_from_redmine, interval=60, first=5)  # 30
dispatcher.job_queue.run_repeating(callback=sending_new_incident, interval=65, first=10)  # 10
dispatcher.job_queue.run_repeating(callback=sending_release_notification, interval=60, first=15)  # 60

dispatcher.job_queue.run_daily(
    callback=broadcasting_create_statistic_in_db,
    time=time(hour=8, minute=00, tzinfo=timezone('Europe/Moscow'))
)

dispatcher.job_queue.run_daily(
    callback=job_cleaning,
    time=time(hour=17, minute=00, tzinfo=timezone('Europe/Moscow'))
)

dispatcher.job_queue.run_daily(
    callback=broadcasting_evening_news,
    time=time(hour=17, minute=15, tzinfo=timezone('Europe/Moscow'))
)

updater.start_polling()
logging.info("Бот запущен")
updater.idle()
