"""
Код обработки логики Redmine
"""

import logging

from redminelib import Redmine
import external_services.jira as jira
import db.db_handler as db
from db.db_requests import prepare_day_redmine_statistic, prepare_sprint_redmine_statistic
from settings import REDMINE_KEY, REDMINE_URL
from tools.dict_catalog import teams


def redmine_init():
    """
    Пришлось пересоздавать сессию, потому что данные кешируются
    и запросы от Redmine возвращают одни и те же значения
    """
    return Redmine(REDMINE_URL, key=REDMINE_KEY)


def search_info_in_redmine(team_list):
    """
    Запрос к Redmine по заданному фильтру о задачах назначенных на команду
    project_id - проект Redmine
    status_id - статусы задачи
    assigned_to_id - id команды, на которую назначена задача
    return ResourceSet
    """
    redmine = redmine_init()
    filter_assigned_to_id = ''
    for team_name in team_list:
        filter_assigned_to_id += str(teams[team_name]['redmine_assigned_to_id']) + '|'
    return redmine.issue.filter(project_id=2, status_id="!10|16", assigned_to_id=str(filter_assigned_to_id))


def redmine_search_incident_info(redmine_id):
    """
    Поиск по заданному номеру инцидента, для оформления бага в Jira
    """
    redmine = redmine_init()
    try:
        return redmine.issue.get(resource_id=redmine_id)
    except (Exception,):
        logging.info(f"Упс!В Redmine по номеру {redmine_id} ничего не найдено !")
        return None


def reading_from_redmine(team_list):
    """
    Забирает с Redmine результат выборки, проверяет каких записей не хватает в бд
    и добавляет в бд новые записи о проблемах
    """
    issues = search_info_in_redmine(team_list)
    logging.info(f'инцидентов {len(issues)}')
    for i in range(len(issues)):
        incident_team = (issues[0].assigned_to.name.replace('_', '').replace('Команда ', '').replace(' ', ''))
        if incident_team in teams.keys():
            result = db.search_redmine_incidents(note_id=issues[i].id)
            if not result:
                category = getattr(issues[i], 'category', None)
                custom_fields = getattr(issues[i], 'custom_fields', None)
                jira_issue = jira.create_jira_incident(redmine_id=issues[i].id)
                #jira_issue = None
                db.create_redmine_incidents(note_id=issues[i].id, subject=issues[i].subject,
                                            type=issues[0].tracker,
                                            priority=str(issues[i].priority),
                                            category=category.name if category else None,
                                            importance=custom_fields[8].value if custom_fields[8] else None,
                                            team=incident_team,
                                            jira_issue=str(jira_issue)
                                            )
                db.update_statistic_in_db(team=incident_team, new_tasks=True)


def prepare_incident_notification(team=None, is_sended=None):
    """
    Подготовка списка неотправленных id инцидентов
    """
    return db.search_redmine_incidents(team=team, is_sended=is_sended)


def mark_sended_notification(note_id):
    """
    Отметка об отправлении инцидента в чат команды
    """
    db.update_redmine_incidents(note_id=note_id)


def cleaning():
    """
    Очищает устаревшие записи из бд.
    Забирает с Redmine актуальные результаты выборки, формирует список актуальных id,
    сравнивает с содержимым БД, разницу удаляет
    """
    actual_list_id = []
    team_list = db.search_statistic_in_db()
    if team_list:
        # reading_from_redmine(team_list)
        issues_from_redmine = search_info_in_redmine(team_list)
        for i in range(len(issues_from_redmine)):
            actual_list_id.append(issues_from_redmine[i].id)
        issues_from_db = db.search_redmine_incidents()
        for issue in issues_from_db:
            if issue['id'] not in actual_list_id:
                # db.delete_redmine_incidents(issue['id'])
                db.update_statistic_in_db(team=issue['team'], close_tasks=True)


def create_new_row_statistic(team):
    """
    Создает новую запись для ведения статистики за день по конкретной команде
    """
    result = db.search_statistic_in_db(team=team)
    if result:
        logging.info("Запись уже существует!")
    else:
        db.create_statistic_in_db(team=team)


def prepare_day_statistic_about_team(team):
    """
    Собирает информацию по команде
    team - имя команды, для которой готовится статистика
    period - период сбора информация (Day, Sprint)
    returns список словарей
    """
    return prepare_day_redmine_statistic(team=team)


def prepare_sprint_statistic_about_team(team):
    """
    Собирает информацию по команде за спринт.
    """
    return prepare_sprint_redmine_statistic(team=team)
