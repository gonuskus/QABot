"""
Код по взаимодействию с ботом
"""

# from external_services.redmine import read_from_redmine
import logging
import random
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Unauthorized
from telegram.ext import CallbackContext

import external_services.jira as jira
from db.db_handler import delete_chat_in_db, create_chat_in_db, search_statistic_in_db, \
    create_statistic_in_db, search_chat_in_db
from external_services.redmine import prepare_incident_notification, prepare_day_statistic_about_team, \
    prepare_sprint_statistic_about_team, reading_from_redmine, mark_sended_notification, cleaning
from tools.dict_catalog import tg_member, evening_title, teams, broadcasting_news


# CommandHandler

def start(update: Update, context: CallbackContext) -> None:
    """
    Инициализация рассылки нотификаций для участника приславшего команду /start
    """
    from_user = update.message.from_user.name
    message = f"Привет, {from_user}!\n" \
              f"Я верный помощник QA! Я шлю напоминания, там где нужна реакция " \
              f"и делаю за QA рутинную работу, которая мне по силам!\n" \
              f"Введи /help, если захочешь узнать обо мне больше\n" \
              f"Чтобы получать рассылку от меня введи /set_team\n"
    update.message.reply_text(message)


def keyboard_change_team():
    """
    Генерация кнопок с именами команд для подписки на рассылку
    """
    keyboard_team = []
    for item in teams.keys():
        keyboard_team.append([InlineKeyboardButton(text=item, callback_data=f'team_{item}')])
    keyboard_team.append([InlineKeyboardButton("Отменить", callback_data='team_Cancel')])
    return InlineKeyboardMarkup(keyboard_team)


def set_team(update: Update, context: CallbackContext) -> None:
    """
    Отправка сообщения с кнопками выбора команды
    далее уходим в режим ожидания ответа callback_change_team
    """
    chat_id = update.message.chat_id
    searching_result = search_chat_in_db(chat_id=chat_id)

    if searching_result:
        update.message.reply_text(f"Для этого чата задана команда - {list(searching_result.keys())[0]}.\n"
                                  f'Выбери новую команду:', reply_markup=keyboard_change_team())
    else:
        update.message.reply_text(f"Для этого чата еще НЕ задана команда.\n"
                                  f'Выбери свою команду:', reply_markup=keyboard_change_team())


def callback_change_team(update: Update, context: CallbackContext) -> None:
    """
    Приемка и обработка ответа от пользователя
    """
    chat_id = update.effective_chat.id
    query = update.callback_query
    answer_text = re.split(r"team_", query.data)[1]
    query.answer()
    if answer_text == 'Cancel':
        searching_result = search_chat_in_db(chat_id=chat_id)
        if searching_result:
            query.edit_message_text(
                text='Команда не изменена.\n'
                     f'Чат по прежнему подключен к рассылке {list(searching_result.keys())[0]} команды. \n'
                     'Чтобы получать рассылку введи /set_team')
        else:
            query.edit_message_text(
                text='Для получения сообщений необходимо выбрать команду.\n'
                     'Чат НЕ подключен к рассылке. \n'
                     'Чтобы получать рассылку введи /set_team')
    else:
        __set_team(update, context, team=answer_text)
        query.edit_message_text(
            text=f"Выбрана команда: {answer_text}.\n"
                 f"В этот чат будут поступать сообщения для {answer_text} команды.")


def __set_team(update: Update, context: CallbackContext, team):
    """
    Когда ответ получен, записываем данные в бд
    и заодно создаем запись о статистике по команде
    """
    chat_id = update.effective_chat.id
    searching_result = search_chat_in_db(chat_id=chat_id)
    if searching_result:
        delete_chat_in_db(chat_id)
        create_chat_in_db(chat_id=chat_id, team=team)
    else:
        create_chat_in_db(chat_id=chat_id, team=team)
    existing_team_statistic_row = search_statistic_in_db(team=team)
    if not existing_team_statistic_row:
        create_statistic_in_db(team=team)


def helping(update: Update, context: CallbackContext) -> None:
    """
    Текстовка для команды help
    """
    chat_id = update.message.chat_id
    searching_result = search_chat_in_db(chat_id=chat_id)
    if searching_result:
        update.message.reply_text(f"Для этого чата задана команда - {list(searching_result.keys())[0]}.\n"
                                  "Когда нибудь тут будет больше информации\n")
    else:
        update.message.reply_text(f"Для этого чата НЕ задан получатель для рассылки информации!\n"
                                  "Когда нибудь тут будет больше информации...\n"
                                  "А пока можешь почитать <a href='https://confluence.fabrikant.ru/display/~v.gonuskus/QA+Bot'>о планах моего развития</a>",
                                  parse_mode="html")


def keyboard_news_button():
    """
    Список возможных срезов информации по команде
    """
    keyboard_news, keyboard_button = [], []

    for item, key in broadcasting_news.items():
        keyboard_button.append(InlineKeyboardButton(text=f'{key}', callback_data=f'news_{item}'))
    keyboard_news.append(keyboard_button)
    keyboard_news.append([InlineKeyboardButton("Отменить", callback_data='news_Cancel')])
    return InlineKeyboardMarkup(keyboard_news)


def info_request(update: Update, context: CallbackContext) -> None:
    """
    Отправка сообщения с кнопками выбора новостей
    далее уходим в режим ожидания ответа callback_news
    """
    update.message.reply_text('Выбери тип запроса:', reply_markup=keyboard_news_button())


def callback_news(update: Update, context: CallbackContext) -> None:
    """
    Приемка и обработка ответа от пользователя
    """
    query = update.callback_query
    answer_text = re.split(r"news_", query.data)[1]
    query.answer()
    if answer_text == 'Cancel':
        update.effective_message.edit_reply_markup(None)
    else:
        query.edit_message_text(
            text=f"{broadcasting_news[answer_text]}:")
        # broadcasting_template(context, template_method=answer_text)
        news_request_template(update, context, template_method=answer_text)


# job_queue

def job_reading_from_redmine(context: CallbackContext) -> None:
    """
    Запуск чтения данных из Redmine по подписанным командам
    """
    logging.info('job_reading_from_redmine')
    # team_list = search_statistic_in_db()
    team_list = search_chat_in_db(team='All')
    if team_list:
        # reading_from_redmine(team_list[])
        reading_from_redmine(team_list)
    else:
        logging.info('А job_reading_from_redmine ничего не читает!')


def news_request_template(update: Update, context: CallbackContext, template_method) -> None:
    """
    Обертка-шаблон для рассылки по запросу
    """
    chat_id = update.effective_chat.id
    subscribers = search_chat_in_db(chat_id=chat_id)
    if subscribers:
        eval(template_method + "(subscribers=subscribers, context=context)")


# def broadcasting_template(context: CallbackContext, template_method) -> None:
#     """
#     Обертка-шаблон для запланированной рассылки на всех подписчиков
#     """
#     subscribers = search_chat_in_db()
#     if subscribers:
#         eval(template_method + "(subscribers=subscribers, context=context)")


def broadcasting_evening_news(context: CallbackContext) -> None:
    """
    Обертка для запланированной рассылки на всех подписчиков
    реализовано только для prepare_evening_news
    """
    logging.info('broadcasting_news_prepare_evening_news')
    subscribers = search_chat_in_db()
    if subscribers:
        prepare_evening_news(subscribers=subscribers, context=context)


def sending_new_incident(context: CallbackContext) -> None:
    """
    Отправка нотификаций о новых инцидентах, назначенных на команду
    """

    logging.info("sending_new_incident")
    subscribers = search_chat_in_db()
    if subscribers:
        for subscriber_team in subscribers.keys():
            incident_list = prepare_incident_notification(team=subscriber_team, is_sended=False)
            if incident_list:
                for chat_team in subscribers[subscriber_team]:
                    for incident in incident_list:
                        try:
                            context.bot.sendMessage(chat_id=chat_team,
                                                    text='❗ ❗ ❗ \n'
                                                         f"New incident for {incident['team']} - {incident['priority']}\n"
                                                         f"Важность ({incident['importance']})  |  Категория ({incident['category']})\n"
                                                         f"https://redmine.fabrikant.ru/redmine/issues/{incident['id']} \n"
                                                         f"https://jira.fabrikant.ru/browse/{incident['jira_issue']} \n"
                                                    )
                        except Unauthorized:
                            delete_chat_in_db(subscribers[subscriber_team])
                            logging.info(f"Chat {subscribers[subscriber_team]} was deleted")
                        mark_sended_notification(incident['id'])


def sending_release_notification(context: CallbackContext) -> None:
    """
    Информация о готовом релизе
    """
    logging.info("sending_release_notification")
    subscribers = search_chat_in_db()
    if not subscribers:
        return
    for subscriber_team in subscribers.keys():
        fixversion = jira.search_release(subscriber_team)
        if fixversion:
            release_members = jira.prepare_release_info(team=subscriber_team, jira_fix_version=fixversion)
            member_srt = f"👀 В составе релиза задачи: "
            for member in range(len(release_members)):
                member_srt += f"{tg_member[release_members[member]]} | "
            for chat_team in subscribers[subscriber_team]:
                context.bot.sendMessage(chat_id=chat_team,
                                        text=f"🏆 В тестирование переведен релиз {fixversion} ({subscriber_team})\n"
                                             f"{member_srt}\n",
                                        )


def prepare_evening_news(context: CallbackContext, subscribers) -> None:
    """
    Статистика по команде на конец дня
    """
    logging.info('prepare_evening_news')
    for subscriber_team in subscribers.keys():
        # for subscriber_team in subscribers:
        statistic_dict = prepare_day_statistic_about_team(team=subscriber_team)
        all_count_incident = prepare_incident_notification(team=subscriber_team)
        title = random.choice(evening_title) + f"Подведем итоги дня {subscriber_team} team\n"
        for chat_team in subscribers[subscriber_team]:
            context.bot.sendMessage(chat_id=chat_team,
                                    text=f'{title} \n'
                                         f"🚩 Открыто новых инцидентов: {statistic_dict['new_tasks'] if statistic_dict else 0}\n"
                                         f"✅ Закрыто инцидентов: {statistic_dict['close_tasks'] if statistic_dict else 0}\n"
                                         f"🚧 Всего инцидентов на команде: {len(all_count_incident)}\n"
                                    )


def prepare_sprint_news(context: CallbackContext, subscribers):
    """
    Отправка статистики в начале дня
    """
    logging.info("sending_sprint_news")
    for subscriber_team in subscribers.keys():
        dict_result = prepare_sprint_statistic_about_team(team=subscriber_team)
        if dict_result['new_sprint_incident'] != '0':
            priority_str = f"🚥 Критичность: \n"
            for priority in dict_result['incident_priority_result'].items():
                priority_str += f"{priority[0]} = {priority[1][0]}   \n"

            category_str = f"🚨 Массовость: \n"
            for category in dict_result['incident_category_result'].items():
                category_str += f"{category[0]} = {category[1][0]}   \n"

            incident_str = f"ℹ Список инцидентов:\n"
            for incident_number in range(len(dict_result['list_sprint_incident'])):
                incident_str += f"https://redmine.fabrikant.ru/redmine/issues/{dict_result['list_sprint_incident'][incident_number]} \n"

        for chat_team in subscribers[subscriber_team]:
            if dict_result['new_sprint_incident'] == '0':
                context.bot.sendMessage(chat_id=chat_team,
                                        text=f'Спринт статистика (2 недели) {subscriber_team}: \n'
                                             f'😈 Ни одного инцидента с боя\n')
            else:
                context.bot.sendMessage(chat_id=chat_team,
                                        text=f'Спринт статистика (2 недели) {subscriber_team}: \n'
                                             f"🚩 Всего инцидентов: {dict_result['new_sprint_incident']}\n"
                                             f"{priority_str}\n"
                                             f"{category_str}\n"
                                             f"{incident_str}\n")


def broadcasting_create_statistic_in_db(context: CallbackContext) -> None:
    subscribers = search_chat_in_db()
    if subscribers:
        for subscriber_team in subscribers.keys():
            existing_team_statistic_row = search_statistic_in_db(team=subscriber_team)
            if not existing_team_statistic_row:
                create_statistic_in_db(team=subscriber_team)


def job_cleaning(context: CallbackContext) -> None:
    cleaning
