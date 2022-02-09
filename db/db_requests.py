"""
Код работы с запросами к БД (SQlite)
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import Column, Integer, Boolean, String, Date, func
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from settings import MYSQL_URL

# engine = create_engine(MYSQL_URL)
engine = create_engine(MYSQL_URL, convert_unicode=True, connect_args=dict(use_unicode=True))
logging.info("DataBase is initiated")
Base = declarative_base()

Sessions = sessionmaker(bind=engine)
session = Sessions()


# Таблица с Redmine инцидентами
class RedmineTable(Base):
    __tablename__ = 'redminenote'  # имя таблицы
    id = Column(Integer, primary_key=True, unique=True, comment="Идентификатор проблемы Redmine")
    subject = Column(String(256), comment="Описание проблемы")
    type = Column(String(100), comment="Тип задачи")
    priority = Column(String(100), comment="Приоритет")
    importance = Column(String(100), comment="Важность")
    category = Column(String(100), comment="Категория массовости")
    team = Column(String(100), comment="Команда")
    jira_issue = Column(String(100), comment="Задача в Jira")
    update_date = Column(Date, nullable=False, comment="Дата создания информации")
    is_sended = Column(Boolean, nullable=False, comment="Статус нотификации о проблеме")

    @staticmethod
    def create_redmine_note(note_id, subject=None, priority=None, type=None, importance=None, category=None, team=None,
                            jira_issue=None):
        new_note = RedmineTable(id=note_id,
                                subject=subject,
                                type=type,
                                priority=priority,
                                importance=importance,
                                category=category,
                                team=team,
                                jira_issue=jira_issue,
                                update_date=datetime.now(),
                                is_sended=False
                                )
        session.add(new_note)
        session.commit()

    @staticmethod
    def delete_redmine_note(note_id):
        session.query(RedmineTable).filter(id == note_id).delete()
        session.commit()

    @staticmethod
    def update_redmine_note(note_id, field='is_sended', value=True):
        condition = {field: value}
        session.query(RedmineTable). \
            filter(RedmineTable.id == note_id). \
            update(condition)
        session.commit()

    @staticmethod
    def search_redmine_note(team, note_id, is_sended):
        # def search_redmine_note(team, **condition):
        # # **condition
        # print('condition=', condition)
        # filters = ""
        # for field, value in condition.items():
        #     if value != None:
        #         filters += f"{field}={value} and "
        #     # else:
        #     #     filters += f"{field} is NULL and "
        #
        # if team:
        #     filters += f"team='{team}'"
        # print('condition=', filters)
        # result = session.query(RedmineTable) \
        #     .with_entities(RedmineTable.id, RedmineTable.subject, RedmineTable.priority, RedmineTable.importance,
        #                    RedmineTable.category, RedmineTable.team, RedmineTable.jira_issue, RedmineTable.is_sended) \
        #     .filter(text(filters)) \
        #     .all()

        # filters = ()
        filters = ""
        if team:
            # new_part = (f"team='{team}'",)
            new_part = f"team='{team}' and "
            filters += new_part
        if note_id:
            # new_part = (f"id={note_id}",)
            new_part = f"id={note_id} and "
            filters += new_part
        if is_sended == None:
            # new_part = (f"is_sended=1",)
            new_part = "is_sended in (0,1)"
            filters += new_part

        elif is_sended:
            # new_part = (f"is_sended=0",)
            new_part = "is_sended=1"
            filters += new_part
        else:
            new_part = "is_sended=0"
            filters += new_part

        if filters == ():
            result = session.query(RedmineTable) \
                .with_entities(RedmineTable.id, RedmineTable.subject, RedmineTable.priority, RedmineTable.importance,
                               RedmineTable.category, RedmineTable.team, RedmineTable.jira_issue) \
                .all()
        else:  # .filter(text(*filters)) \
            result = session.query(RedmineTable) \
                .with_entities(RedmineTable.id, RedmineTable.subject, RedmineTable.priority, RedmineTable.importance,
                               RedmineTable.category, RedmineTable.team, RedmineTable.jira_issue,
                               RedmineTable.is_sended) \
                .filter(text(filters)) \
                .all()
        return rowlist2dictlist(result)


class ChatTable(Base):
    __tablename__ = 'chats'  # имя таблицы
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, comment="Порядковый номер чата")
    chat_id = Column(String(20), nullable=False, comment="Идентификатор чата")
    team = Column(String(20), nullable=False, comment="Команда")

    def __repr__(self):
        return "<chats(id=%s, chat_id=%s)>" % (self.id, self.chat_id)

    @staticmethod
    def create_chat(chat_id, team):
        new_note = ChatTable(
            chat_id=chat_id,
            team=team
        )
        session.add(new_note)
        session.commit()

    @staticmethod
    def search_chat(chat_id=None, team=None):
        if chat_id:
            result = session.query(ChatTable) \
                .with_entities(ChatTable.team, ChatTable.chat_id) \
                .filter(ChatTable.chat_id == chat_id) \
                .all()
            #     .first()
            # return {'team': result['team'], 'chat_id': result['chat_id']} if result else None
        if team == 'All':
            result = session.query(func.distinct(ChatTable.team)).all()
            return rowlist2list(result) if result else None

        elif team and team != 'All':
            result = session.query(ChatTable) \
                .with_entities(ChatTable.team, ChatTable.chat_id) \
                .filter(ChatTable.team == team)\
                .all()

        if not team and not chat_id:
            result = session.query(ChatTable) \
                .with_entities(ChatTable.team, ChatTable.chat_id) \
                .all()
        return rowlist2dict(result) if result else None
        #return rowlist2list(result) if result else None

    @staticmethod
    def delete_chat(chat_id):
        session.query(ChatTable).filter(ChatTable.chat_id == chat_id).delete()
        session.commit()


#########################

class StatisticTable(Base):
    __tablename__ = 'statistic'  # имя таблицы
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, comment="Порядковый номер")
    date = Column(Date, nullable=False, comment="Дата ведения статистики")
    team = Column(String(20), comment="Команда")
    new_tasks = Column(Integer, comment="Новые задачи за день")
    close_tasks = Column(Integer, comment="Закрытые задачи за день")

    @staticmethod
    def create_statistic_row(team):
        new_rec = StatisticTable(date=datetime.date(datetime.now()),
                                 team=team,
                                 new_tasks=0,
                                 close_tasks=0
                                 )
        session.add(new_rec)
        session.commit()

    @staticmethod
    def delete_statistic_row(date_rec, team):
        session.query(StatisticTable).filter(StatisticTable.date == date_rec, StatisticTable.team == team).delete()
        session.commit()

    @staticmethod
    def search_statistic_row(team):
        if team:
            result = session.query(StatisticTable) \
                .with_entities(StatisticTable.team) \
                .filter(StatisticTable.team == team, StatisticTable.date == datetime.date(datetime.now())) \
                .first()
            return singlerowvalue2list(result) if result else None
        else:
            result = session.query(StatisticTable) \
                .with_entities(StatisticTable.team) \
                .filter(StatisticTable.date == datetime.date(datetime.now())) \
                .all()
        return rowlist2list(result) if result else None
        # return result

    @staticmethod
    def update_statistic_row(team, new_tasks=False, close_tasks=False):
        if new_tasks:
            session.query(StatisticTable).filter(StatisticTable.team == team,
                                                 StatisticTable.date == datetime.date(datetime.now())).update(
                {StatisticTable.new_tasks: StatisticTable.new_tasks + 1})
        elif close_tasks:
            session.query(StatisticTable).filter(StatisticTable.team == team,
                                                 StatisticTable.date == datetime.date(datetime.now())).update(
                {StatisticTable.close_tasks: StatisticTable.close_tasks + 1})
        else:
            raise ValueError("не переданы параметры для обновления")
        session.commit()


def prepare_day_redmine_statistic(team):
    date_rec = datetime.date(datetime.now())
    result = session.query(StatisticTable) \
        .with_entities(StatisticTable.new_tasks, StatisticTable.close_tasks) \
        .filter(StatisticTable.team == team, StatisticTable.date == date_rec).first()

    if result:
        return {'new_tasks': result['new_tasks'], 'close_tasks': result['close_tasks']}
    else:
        return None


def prepare_sprint_redmine_statistic(team):
    date_from = datetime.date(datetime.now() - timedelta(days=14))
    date_to = datetime.date(datetime.now() + timedelta(days=1))

    new_sprint_incident = session.query(func.count(RedmineTable.id)) \
        .filter(RedmineTable.update_date <= date_to) \
        .filter(RedmineTable.update_date >= date_from) \
        .filter(RedmineTable.team == team).first()

    list_sprint_incident = session.query(RedmineTable.id) \
        .filter(RedmineTable.update_date <= date_to) \
        .filter(RedmineTable.update_date >= date_from) \
        .filter(RedmineTable.team == team).all()

    incident_priority_result = session.query(RedmineTable.priority, func.count(RedmineTable.id)) \
        .filter(RedmineTable.update_date <= date_to) \
        .filter(RedmineTable.update_date >= date_from) \
        .filter(RedmineTable.team == team).group_by(RedmineTable.priority).all()

    incident_category_result = session.query(RedmineTable.category, func.count(RedmineTable.id)) \
        .filter(RedmineTable.update_date <= date_to) \
        .filter(RedmineTable.update_date >= date_from) \
        .filter(RedmineTable.team == team).group_by(RedmineTable.category).all()

    # return {'new_sprint_incident': singlerowvalue2list(new_sprint_incident),
    #         'list_sprint_incident': rowlist2list(list_sprint_incident),
    #         'incident_priority_result': dict(incident_priority_result),
    #         'incident_category_result': dict(incident_category_result)
    #         }
    return {'new_sprint_incident': singlerowvalue2list(new_sprint_incident),
            'list_sprint_incident': rowlist2list(list_sprint_incident),
            'incident_priority_result': rowlist2dict(incident_priority_result),
            'incident_category_result': rowlist2dict(incident_category_result)
            }


def rowlist2list(rowlist: list):
    templist = []
    for v_row in rowlist:
        templist.append(v_row._data[0])
    return templist


def singlerowvalue2list(value_row):
    for v_row in value_row:
        return str(v_row)


def rowlist2dictlist(rowlist: list):
    dictlist = []
    for temp_row in rowlist:
        temp_dict = {}
        for i, j in zip(temp_row._fields, temp_row._data):
            temp_dict[f'{i}'] = j
        dictlist.append(temp_dict)
    return dictlist


def rowlist2dict(rowlist: list):
    dict_result = {}
    for temp_row in rowlist:
        temp_list = []
        previous_value = dict_result.get(temp_row._data[0])
        if previous_value:
            temp_list.extend(previous_value)  # поиск по имени команды списка значений
        temp_list.append(temp_row._data[1])
        dict_result.update({f'{temp_row._data[0]}': temp_list})
    return dict_result


Base.metadata.create_all(engine)
logging.info("Tables is created")
