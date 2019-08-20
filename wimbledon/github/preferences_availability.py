import requests
import json
import pandas as pd
from datetime import datetime
import statistics
from IPython.display import HTML, display
from wimbledon.vis.Visualise import DataHandlers


query = """
{
  repository(owner:"alan-turing-institute", name:"Hut23") {
    issue(number:X) {
          number
          title
          url

          reactionGroups {
            content
            users(first:20) {
                edges {
                    node {
                        login
                        name
                    }
                }
            }
            }
    }
  }
}
"""

def run_query(query, token):
    """A simple function to use requests.post to make the API call. Note the json= section.
    Takes as input a string containing a GraphQL query string"""
    headers = {"Authorization": "Bearer " + token}
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))


def get_person_availability(fc, person, start_date, end_date):
    """Get the mean of a person's FTE proportion available for the start to end datetime objects, using their name or id"""
    peopledf = 1 - fc.people_totals.resample('MS').mean()  # pandas df for team members availability
    if isinstance(person, str):
        try:
            person = fc.get_person_id(person)
        except:
            return 0.0
    peopledf = peopledf[(peopledf.index >= start_date) & (peopledf.index <= end_date)]
    try:
        availability_range = peopledf[person]
    except:
        return 0.0
    average_availability = statistics.mean(availability_range)
    return round(average_availability, 2)


def get_project_requirement(fc, project, start_date, end_date):
    """Get the mean of a project's FTE requirement for the start to end datetime objects, using the project name or id"""
    projectdf = fc.project_resourcereq.resample('MS').mean()  # pandas df for project resource requirement
    if isinstance(project, str):
        try:
            project = fc.get_project_id(project)
        except:
            return 0.0
    projectdf = projectdf[(projectdf.index >= start_date) & (projectdf.index <= end_date)]
    try:
        requirement_range = projectdf[project]
    except:
        return 0.0
    average_requirement = statistics.mean(requirement_range)
    return round(average_requirement, 2)


def get_preference_data(fc, github_token, emoji_mapping=None):
    """Get each team members preference emoji for all projects with a GitHub issue"""
    issues = fc.projects["GitHub"].dropna()  # Get list of GitHub issues for projects
    gid_mapping = {  # People without their full names on github.
     'myyong': 'May Yong',
     'nbarlowATI': 'Nick Barlow',
     'thobson88': 'Timothy Hobson',
     'miguelmorin': 'Miguel Morin',
     'OscartGiles': 'Oscar Giles',
     'AshwiniKV': 'Ashwini Venkatasubramaniam',
    }
    if not emoji_mapping:
        emoji_mapping = {'CONFUSED': '😕',
              'EYES': '👀',
              'HEART': '❤️',
              'HOORAY': '🎉',
              'ROCKET': '🚀',
              'THUMBS_DOWN': '❌',
              'THUMBS_UP': '👍',
              'LAUGH': '✅'}
    names = list(fc.people.full_name)
    preference_data = {
        "Person": names
    }
    for issue_num, project_id in zip(issues, issues.index):
        modified_query = query.replace("X", str(issue_num))
        result = run_query(modified_query, github_token)  # Execute the query
        emojis = []
        for name in names:
            emoji_name = None
            for reaction in result['data']['repository']['issue']['reactionGroups']:
                for edge in reaction['users']['edges']:
                    if edge['node']['name'] == name:
                        emoji_name = reaction['content']
                    if not emoji_name:
                        if edge['node']['login'] in gid_mapping:
                            if gid_mapping[edge['node']['login']] == name:
                                emoji_name = reaction['content']
            if emoji_name:
                emoji = emoji_mapping[emoji_name]
            else:
                emoji = "❓"
            emojis.append(emoji)
        preference_data[fc.get_project_name(project_id)] = emojis
        preference_data_df = pd.DataFrame(preference_data).set_index('Person')
        preference_data_df = preference_data_df.loc[~(preference_data_df=="❓").all(axis=1)]
    return preference_data_df


def get_preferences(fc, preference_data_df, first_date=False, last_date=False, person=False, project=False, positive_only=False, emojis_only=False):
    resreqdf = fc.project_resourcereq.resample('MS').mean() # grouped by month and mean taken
    if person:
        names = [person]
    else:
        names = list(preference_data_df.index)
    data = {
        "Person": names
    }
    issues = fc.projects["GitHub"].dropna().values
    if project:
        if isinstance(project, str):
            try:
                project = fc.get_project_id(project)
            except:
                pass
    for project_id in resreqdf:  # some of these have no GitHub issue
        if not project or project == project_id:
            date_indices = resreqdf.index[resreqdf[project_id] > 0]
            if len(date_indices) > 0:  # if at least one month in the dataframe has a resource requirement of more than 0 FTE
                issue_num = fc.projects.loc[project_id, "GitHub"]
                if issue_num in issues:  # if this project has a GitHub issue
                    first_resreq_date = date_indices[0].strftime("%Y-%m-%d")
                    last_resreq_date = date_indices[-1].strftime("%Y-%m-%d")
                    resreq = get_project_requirement(fc, project_id, first_resreq_date, last_resreq_date)
                    project_title = fc.projects.loc[project_id, "name"]
                    emoji_data = []
                    for name in names:
                        person_availability = get_person_availability(fc, name, first_resreq_date, last_resreq_date)
                        percentage_availability = round((person_availability / resreq) * 100, 2)
                        emoji = preference_data_df[project_title][name]
                        if (not person and not project) or not positive_only or emoji == '✅' or emoji == '👍':
                            if emojis_only:
                                emoji_data.append(emoji)
                            else:
                                emoji_data.append(emoji + " " + str(percentage_availability) + "% (" + str(person_availability) + " / " + str(round(resreq, 2)) + ")")
#                         if project and positive_only and (emoji == '❌' or emoji == '❓'):
#                             print(name, emoji)
#                             data["Person"].remove(name)
#                         else:
#                             print(name, emoji)

                    if (not person and not project) or not positive_only or len(emoji_data) > 0:
                        data[project_title] = emoji_data
    preferences = pd.DataFrame(data).set_index('Person').sort_index().sort_index(axis=1)
    return preferences
