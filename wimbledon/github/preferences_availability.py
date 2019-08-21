import requests
import json
import pandas as pd
from datetime import datetime
import statistics
from IPython.display import HTML, display
from wimbledon.vis.Visualise import DataHandlers
from wimbledon import config


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

alternate_query = """
{
  repository(owner:"alan-turing-institute", name:"Hut23") {
    issue(number:X) {
          number
          title
          url
          comments(first:5) {
            edges {
              node {
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
    }
  }
}
"""

def run_query(query, token):
    """
    A simple function to use requests.post to make the API call. Note the json= section.
    Takes as input a string containing a GraphQL query string
    """
    headers = {"Authorization": "Bearer " + token}
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))


def get_reactions(token, issue):
    """
    Get a dictionary of the emoji reactions that exist for a GitHub issue in the strutcture specified by the GraphQL queries
    """
    def reactions_exist(project_reactions):
        for reaction in project_reactions:
            for edge in reaction['users']['edges']:
                if reaction['content']:
                    return True
        return False

    modified_query = query.replace("X", str(issue))
    result = run_query(modified_query, token)
    project_reactions_first_query = result['data']['repository']['issue']['reactionGroups']
    if reactions_exist(project_reactions_first_query):
        return project_reactions_first_query

    modified_query = alternate_query.replace("X", str(issue))
    result = run_query(modified_query, token)
    project_comments = result['data']['repository']['issue']['comments']['edges']
    for comment in project_comments:
        project_reactions = comment['node']['reactionGroups']
        if reactions_exist(project_reactions):
            return project_reactions
    return project_reactions_first_query


def get_person_availability(fc, person, start_date, end_date):
    """
    Get the mean of a person's FTE proportion available for the start to end datetime objects, using their name or id
    """
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
    """
    Get the mean of a project's FTE requirement for the start to end datetime objects, using the project name or id
    """
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
    """
    Get each team members preference emoji for all projects with a GitHub issue.
    Return a pandas df with person against project and their preference emoji.
    Custom emoji mapping can be provided.
    """
    gid_mapping = {  # People without their full names on github.
     'myyong': 'May Yong',
     'nbarlowATI': 'Nick Barlow',
     'thobson88': 'Timothy Hobson',
     'miguelmorin': 'Miguel Morin',
     'OscartGiles': 'Oscar Giles',
     'AshwiniKV': 'Ashwini Venkatasubramaniam',
    }
    if not emoji_mapping:
        emoji_mapping = {'CONFUSED': '😕',  # Map the emojis from GitHub to those we want to display
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
    issues = fc.projects["GitHub"].dropna()  # Get list of GitHub issues for projects
    for issue_num, project_id in zip(issues, issues.index):
        project_reactions = get_reactions(github_token, issue_num)  # get a dict with the emoji reactions for this issue
        emojis = []
        # Get the relevant emoji for each team member for this GitHub issue and associated project
        for name in names:
            emoji_name = None
            for reaction in project_reactions:
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
                emoji = "❓"  # For team members who have not given a preference to the project
            emojis.append(emoji)
        preference_data[fc.get_project_name(project_id)] = emojis
    preference_data_df = pd.DataFrame(preference_data).set_index('Person')
    # Remove any team members without emoji preferences for any project
    preference_data_df = preference_data_df.loc[~(preference_data_df=="❓").all(axis=1)]
    return preference_data_df


def get_preferences(fc, preference_data_df, first_date=False, last_date=False, person=False, project=False, positive_only=False, emojis_only=False, css=None):
    """
    Create a HTML table with each project that has a resource requirement against every REG team member with availability.
    Table values show the preference emojis alongside the mean availability the person has for the resource required period and
    the mean resource required for the range between the first month with resource required and the last.
    """
    # Get the data on project resource requirement from Forecast
    resreqdf = fc.project_resourcereq.resample('MS').mean()  # grouped by month and mean taken
    if person:
        names = [person]
    else:
        names = list(preference_data_df.index)
    data = {
        "Person": names
    }
    issues = fc.projects["GitHub"].dropna().values
    # If a project name or project id is provided, only get data for that project
    if project:
        if isinstance(project, str):
            try:
                project = fc.get_project_id(project)
            except:
                pass
    # Get projects with some resource requirement but filter by those with a GitHub issue
    for project_id in resreqdf:
        if not project or project == project_id:  # If a project name or project id is provided, only get data for that project
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
                        # If a specific person or project is specified and positive_only is True, only include checks and thumbs
                        if (not person and not project) or not positive_only or emoji == '✅' or emoji == '👍':
                            if emojis_only:
                                emoji_data.append(emoji)
                            else:
                                emoji_data.append(emoji + " " + str(person_availability) + " / " + str(round(resreq, 2)))
                                # emoji_data.append(emoji + " " + str(percentage_availability) + "% (" + str(person_availability) + " / " + str(round(resreq, 2)) + ")")
#                         if project and positive_only and (emoji == '❌' or emoji == '❓'):
#                             print(name, emoji)
#                             data["Person"].remove(name)
#                         else:
#                             print(name, emoji)

                    if (not person and not project) or not positive_only or len(emoji_data) > 0:
                        data[project_title] = emoji_data
    # Created an alphabetically sorted dataframe from the data
    preferences = pd.DataFrame(data).set_index('Person').sort_index().sort_index(axis=1)
    # Create a HTML table from this dataframe that is scrollable
    # Default css can be overridden with argument
    if not css:
        css = """<style>
                    .tableFixHead {
                              overflow: scroll;
                              max-height: 100%;
                              max-width: 100%;
                            }
                    thead th {
                              position: sticky;
                              top: 0;
                              background-color: #4CAF50;
                              color: white;
                            }
                    tbody th {
                              position: sticky;
                              left: 0;
                              padding-top: 12px;
                              padding-top: 12px;
                              padding-bottom: 12px;
                              text-align: left;
                              background-color: #4CAF50;
                              color: white;
                            }
                    thead th:first-child {
                              left: 0;
                              z-index: 1;
                            }
                    td th {
                              border: 1px solid #ddd;
                              padding: 8px;
                            }
                    table {
                               font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;
                               border-collapse: collapse;
                               width: 100%;
                            }
                    tr:nth-child(even){
                               background-color: #f2f2f2;
                            }
                    tr:hover {
                               background-color: #d4fad9;
                            }
            </style>"""
    emoji_table = preferences.to_html()  # Convert to HTML table
    html_table = css + """<div class="tableFixHead">""" + emoji_table + """</div>"""  # Add CSS to table
    return html_table


def get_all_preferences_table(fc=None):
    """
    Create the HTML table described in get_preferences() with default settings
    i.e. for all team members with at least one preference emoji and all projects
    with some resource requirement.
    """
    credentials = config.get_github_credentials()
    token = credentials["token"]

    if not fc:
        fc = DataHandlers.Forecast()
    preference_data_df = get_preference_data(fc, token)
    preferences_with_availability = get_preferences(fc, preference_data_df)
    return preferences_with_availability
