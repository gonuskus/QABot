"""
Код обработки логики Redmine
"""
from db.db_requests import ChatTable
from db.db_requests import RedmineTable
from db.db_requests import StatisticTable
from db.db_requests import prepare_day_redmine_statistic, prepare_sprint_redmine_statistic


# RedmineTable
def search_redmine_incidents(team=None, note_id=None, is_sended=None):
    """
    Инициация поиска записи в БД
    note_id - номер задачи Redmine
    is_sended - статусы отправки нотификации по данной задачи
    returns список словарей с информацией о новых инцидентах
    """
    return RedmineTable().search_redmine_note(team=team, note_id=note_id, is_sended=is_sended)


def create_redmine_incidents(note_id, subject, type, priority, importance, category, team, jira_issue):
    """
    Инициация создания записи в БД
    note_id - Номер задачи Redmine
    subject - Описание проблемы
    priority - Приоритет
    importance - Важность
    """
    RedmineTable().create_redmine_note(note_id=note_id, subject=subject, type=type, priority=priority, importance=importance,
                                       category=category, team=team, jira_issue=jira_issue)


def update_redmine_incidents(note_id):
    """
    Инициация редактирования записи в БД
    note_id - номер задачи Redmine
    """
    RedmineTable().update_redmine_note(note_id)


def delete_redmine_incidents(note_ids):
    """
    Инициация удаления записи в БД
    note_ids - список номеров задач Redmine
    """
    RedmineTable().delete_redmine_note(note_ids)


# StatisticTable

def create_statistic_in_db(team):
    """
    Создаем запись в БД о статистике по команде
    """
    StatisticTable().create_statistic_row(team=team)


def search_statistic_in_db(team=None):
    """
    Создаем запись в БД о статистике по команде
    """
    return StatisticTable().search_statistic_row(team=team)


def update_statistic_in_db(team, new_tasks=False, close_tasks=False):
    """
    Обновляем статистику
    """
    check_existing = search_statistic_in_db(team=team)
    if not check_existing:
        create_statistic_in_db(team=team)
    StatisticTable().update_statistic_row(team=team, new_tasks=new_tasks, close_tasks=close_tasks)


def delete_statistic_in_db(team, date):
    """
    Очищаем статистику
    """
    StatisticTable().delete_statistic_row(date_rec=date, team=team)


# def prepare_day_statistic_in_db(team):
#     """
#     Создаем статистику за день
#     """
#     return prepare_day_redmine_statistic(team=team)
#
#
# def prepare_sprint_statistic_in_db(team):
#     """
#     Создаем статистику за спринт
#     """
#     return prepare_sprint_redmine_statistic(team=team)


"""
Код обработки логики Redmine
"""


def search_chat_in_db(chat_id=None, team=None):
    """
    Поиск в БД номера чата по имени команды
    return
    """
    return ChatTable().search_chat(chat_id=chat_id, team=team)


def create_chat_in_db(chat_id, team=None):
    """
    Создать запись о чате в БД
    """
    ChatTable().create_chat(chat_id=chat_id, team=team)


def delete_chat_in_db(chat_id):
    """
    Удалить в БД запись о чате
    """
    ChatTable().delete_chat(chat_id=chat_id)
