"""
Код обработки логики Jira
"""
import logging

import external_services.redmine as redmine
from jira import JIRA
from settings import JIRA_PASSWORD, JIRA_LOGIN, JIRA_URL
from tools.dict_catalog import team_member, teams

# jira = JIRA(server=JIRA_URL, basic_auth=(JIRA_LOGIN, JIRA_PASSWORD))

jira = JIRA(basic_auth=(JIRA_LOGIN, JIRA_PASSWORD), options={'server': JIRA_URL})


def create_jira_incident(redmine_id):
    result = jira.search_issues(
        f'issueFunction in issueFieldMatch("project = COM", "customfield_11610", "{redmine_id}")')
    if result:
        logging.info(f"Ой! а в Jira уже оформлен такой баг! {result[0].key}")
        return result[0].key
    else:
        redmine_incident_info = redmine.redmine_search_incident_info(redmine_id)
        if redmine_incident_info:
            team_name = (
                redmine_incident_info.assigned_to.name.replace('_', '').replace('Команда ', '').replace(' ', ''))

            return jira.create_issue(
                project={'key': teams[team_name]['jira_project']},
                summary=f'{redmine_incident_info.subject}',
                description=f'{redmine_incident_info.description}',
                issuetype={'name': 'Bug'},
                labels=[team_name, 'Incident'],
                priority={'name': 'Major'},
                customfield_12305=[{'value': teams[team_name]['section']}],
                customfield_11610=f'https://redmine.fabrikant.ru/redmine/issues/{redmine_id}',
                assignee=None
            )
        else:
            return None


def search_release(team_name):
    issue = jira.search_issues(
        f'project in ({teams[team_name]["jira_project"]}) AND type = Task AND summary ~ Релиз AND status in ("In testing", "Ready for testing")')
    if issue:
        return issue[0].fields.fixVersions[0]
    else:
        return None


def prepare_release_info(team, jira_fix_version):
    member_result_list = []
    for member in range(len(team_member[team])):
        result = jira.search_issues(
            f'fixVersion = {jira_fix_version} and ("QA Engineer" in ({team_member[team][member]}) or assignee in ({team_member[team][member]}))')
        if result:
            member_result_list.append(team_member[team][member])
    return member_result_list
