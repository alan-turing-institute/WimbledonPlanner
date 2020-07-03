import requests
import json
import pandas as pd
import math
from datetime import datetime
import statistics
from wimbledon import Wimbledon
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
            users(first:Y) {
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
          comments(first:Z) {
            edges {
              node {
                reactionGroups {
                    content
                    users(first:Y) {
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
    request = requests.post(
        "https://api.github.com/graphql", json={"query": query}, headers=headers
    )
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception(
            "Query failed to run by returning code of {}. {}".format(
                request.status_code, query
            )
        )


def get_reactions(token, issue, number_of_people=20, number_of_comments=2):
    """
    Get a dictionary of the emoji reactions that exist for a GitHub issue in the strutcture specified by the GraphQL queries
    """

    def reactions_count(project_reactions):
        count = 0
        for reaction in project_reactions:
            for edge in reaction["users"]["edges"]:
                if reaction["content"]:
                    count += 1
        return count

    # Edit the query string to contain the relevant issue and number of GitHub users
    # This query gets the emojis on the issue itself (i.e. the top comment/ post)
    modified_query = query.replace("X", str(int(issue))).replace(
        "Y", str(number_of_people)
    )
    result = run_query(modified_query, token)
    project_reactions = result["data"]["repository"]["issue"]["reactionGroups"]
    project_reaction_groups_dict = {
        reactions_count(project_reactions): project_reactions
    }

    # If we don't find any emojis from the first query, this one searches subsequent comments (set to first 5 by default)
    modified_query = (
        alternate_query.replace("X", str(int(issue)))
        .replace("Y", str(number_of_people))
        .replace("Z", str(number_of_comments))
    )
    result = run_query(modified_query, token)
    project_comments = result["data"]["repository"]["issue"]["comments"]["edges"]
    for comment in project_comments:
        project_reactions = comment["node"]["reactionGroups"]
        pr_count = reactions_count(project_reactions)
        if pr_count > 0:
            project_reaction_groups_dict[pr_count] = project_reactions
            break

    return project_reaction_groups_dict[max(project_reaction_groups_dict, key=int)]


def get_person_availability(wim, person, start_date, end_date):
    """
    Get the mean of a person's FTE proportion available for the start to end datetime objects, using their name or id
    """
    peopledf = wim.people_free_capacity
    if isinstance(person, str):
        try:
            person = wim.get_person_id(person)
        except:
            return 0.0
    peopledf = peopledf[(peopledf.index >= start_date) & (peopledf.index <= end_date)]
    try:
        availability_range = peopledf[person]
    except:
        return 0.0
    try:
        average_availability = statistics.mean(availability_range)
    except:
        return 0.0
    return round(average_availability, 2)


def get_preference_data(wim, github_token, emoji_mapping=None):
    """
    Get each team members preference emoji for all projects with a GitHub issue.
    Return a pandas df with person against project and their preference emoji.
    Custom emoji mapping can be provided.
    """
    gid_mapping = {  # People without their full names on github.
        "myyong": "May Yong",
        "nbarlowATI": "Nick Barlow",
        "thobson88": "Timothy Hobson",
        "miguelmorin": "Miguel Morin",
        "OscartGiles": "Oscar Giles",
        "AshwiniKV": "Ashwini Venkatasubramaniam",
        "annahadji": "Anna Hadjitofi",
        "misspawty": "Flora Roumpani",
        "pafoster": "Peter Foster",
        "jd2019a": "Joel Dearden",
        "entopia": "Flora Roumpani",
    }
    if not emoji_mapping:
        emoji_mapping = {
            "CONFUSED": "😕",  # Map the emojis from GitHub to those we want to display
            "EYES": "👀",
            "HEART": "❤️",
            "HOORAY": "🎉",
            "ROCKET": "🚀",
            "THUMBS_DOWN": "❌",
            "THUMBS_UP": "👍",
            "LAUGH": "✅",
        }
    names = list(wim.people.name)
    # Giovanni and Miguel have left but put emojis on future projects. Remove them
    names.remove("Giovanni Colavizza")
    names.remove("Miguel Morin")
    preference_data = {"Person": names}
    issues = wim.projects["github"].dropna()  # Get list of GitHub issues for projects
    total_people = len(wim.people)
    for issue_num, project_id in zip(issues, issues.index):
        # Get a dict with the emoji reactions for this issue
        project_reactions = get_reactions(
            github_token, issue_num, number_of_people=total_people
        )
        emojis = []
        # Get the relevant emoji for each team member for this GitHub issue and associated project
        for name in names:
            emoji_name = None
            for reaction in project_reactions:
                for edge in reaction["users"]["edges"]:
                    if edge["node"]["name"] == name:
                        emoji_name = reaction["content"]
                    if not emoji_name:
                        if edge["node"]["login"] in gid_mapping:
                            if gid_mapping[edge["node"]["login"]] == name:
                                emoji_name = reaction["content"]
            if emoji_name:
                emoji = emoji_mapping[emoji_name]
            else:
                emoji = (
                    "❓"
                )  # For team members who have not given a preference to the project
            emojis.append(emoji)
        preference_data[wim.get_project_name(project_id)] = emojis
    preference_data_df = pd.DataFrame(preference_data).set_index("Person")
    # Remove any team members without emoji preferences for any project
    preference_data_df = preference_data_df.loc[
        ~(preference_data_df == "❓").all(axis=1)
    ]
    return preference_data_df


def get_preferences(
    wim,
    preference_data_df,
    first_date=False,
    last_date=False,
    person=False,
    project=False,
    emojis_only=False,
    css=None,
):
    """
    Create a HTML table with each project that has a resource requirement against every REG team member with availability.
    Table values show the preference emojis alongside the mean availability the person has for the resource required period and
    the mean resource required for the range between the first month with resource required and the last.
    """
    # Get the data on project resource requirement from Forecast
    # grouped by month and mean taken
    resreqdf = wim.project_resourcereq.resample("MS").mean()
    #  Also consider unconfirmed projects
    unconfdf = wim.project_unconfirmed.resample("MS").mean()

    if first_date:
        resreqdf = resreqdf[resreqdf.index >= first_date]
        unconfdf = unconfdf[unconfdf.index >= first_date]
    if last_date:
        resreqdf = resreqdf[resreqdf.index <= last_date]
        unconfdf = unconfdf[unconfdf.index <= last_date]
      
    if person:
        names = [person]
    else:
        names = list(preference_data_df.index)
    data = {"Person": names}
    # If a project name or project id is provided, only get data for that project
    if project:
        if isinstance(project, str):
            try:
                project = wim.get_project_id(project)
            except:
                pass

    # Get projects with some resource requirement but filter by those with a GitHub issue
    project_titles = {}
    for project_id in resreqdf:
        if not project or project == project_id:
            # If a project name or project id is provided, only get data for that project
            # Get the dates for each month that the project has a resource requirement > 0           
            dates_resreq = resreqdf.index[resreqdf[project_id] > 0]
            dates_unconf = unconfdf.index[unconfdf[project_id] > 0]
            issue_num = wim.projects.loc[project_id]["github"]
            if (len(dates_resreq) > 0 or len(dates_unconf) > 0) and not math.isnan(
                issue_num
            ):
                project_name = wim.projects.loc[project_id, "name"]

                req_or_unconf_df = resreqdf + unconfdf
                dates_req_or_unconf = req_or_unconf_df.index[
                    req_or_unconf_df[project_id] > 0
                ]
                unconf_or_req_start_date = dates_req_or_unconf[0]
                unconf_or_req_end_date = dates_req_or_unconf[-1]

                if first_date and unconf_or_req_start_date < first_date:
                    unconf_or_req_start_date = first_date
                if last_date and unconf_or_req_end_date > last_date:
                    unconf_or_req_end_date = last_date

                project_title = (
                    project_name
                    + "<br>#"
                    + str(int(issue_num))
                    + "<br>"
                    + unconf_or_req_start_date.strftime("%Y-%m")
                    + " to "
                    + unconf_or_req_end_date.strftime("%Y-%m")
                    + "<br>"
                )

                if len(dates_resreq) > 0:
                    # if at least one month in the dataframe has a resource requirement of more than 0 FTE
                    first_resreq_date = dates_resreq[0]
                    last_resreq_date = dates_resreq[-1]
                    if first_date and first_resreq_date < first_date:
                        first_resreq_date = first_date
                    if last_date and last_resreq_date > last_date:
                        last_resreq_date = last_date
                    
                    # get mean project requirement in date range
                    resreq = resreqdf.loc[
                        (resreqdf.index >= first_resreq_date)
                        & (resreqdf.index <= last_resreq_date),
                        project_id,
                    ].mean()

                    if resreq >= 0.01:
                        project_title += str(round(resreq, 1)) + " FTE"
                else:
                    resreq = 0

                if len(dates_unconf) > 0:
                    # if at least one month in the dataframe has a resource requirement of more than 0 FTE
                    first_unconf_date = dates_unconf[0]
                    last_unconf_date = dates_unconf[-1]
                    if first_date and first_unconf_date < first_date:
                        first_unconf_date = first_date
                    if last_date and last_unconf_date > last_date:
                        last_unconf_date = last_date
                    
                    # get mean project requirement in date range
                    unconf = unconfdf.loc[
                        (unconfdf.index >= first_unconf_date)
                        & (unconfdf.index <= last_unconf_date),
                        project_id,
                    ].mean()

                    if unconf >= 0.01:
                        # add a separator between required and unconfirmed FTE if both present
                        if len(dates_resreq) > 0:
                            pre = " + "
                            post = " UNC"
                        else:
                            pre = ""
                            post = " UNC FTE"
                        project_title += pre + "" + str(round(unconf, 1)) + post
                else:
                    unconf = 0

                # make column header a link to github issue
                project_title = """<a href="{url}/{issue}">{title}</a>""".format(
                    url="https://github.com/alan-turing-institute/Hut23/issues",
                    issue=int(issue_num),
                    title=project_title,
                )
                project_titles[project_name] = project_title
                emoji_data = []
                for name in names:
                    person_availability = get_person_availability(
                        wim, name, unconf_or_req_start_date, unconf_or_req_end_date
                    )

                    percentage_availability = round(
                        (person_availability / (unconf + resreq)) * 100
                    )
                    emoji = preference_data_df[project_name][name]
                    if emojis_only:
                        emoji_data.append(emoji)
                    else:  # Include availability
                        emoji_data.append(
                            emoji
                            + " "
                            + str(percentage_availability)
                            + "% ("
                            + str(round(person_availability, 1))
                            + " / "
                            + str(round(unconf + resreq, 1))
                            + ")"
                        )
                # Store list of preference data for this project
                data[project_name] = emoji_data

    # Created an alphabetically sorted dataframe from the data
    preferences = pd.DataFrame(data).set_index("Person").sort_index().sort_index(axis=1)
    preferences = preferences.rename(columns=project_titles)
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
                              text-align: left;
                              padding-left: 5px;
                              padding-right: 5px;
                              padding-top: 5px;
                              padding-right: 5px;
                            }
                    tbody th {
                              position: sticky;
                              left: 0;
                              padding-top: 10px;
                              padding-bottom: 10px;
                              padding-left: 5px;
                              padding-right: 5px;
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
                    tr {
                              text-align: left;
                    }
                    table {
                               font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;
                               border-collapse: collapse;
                               width: 100%;
                               white-space: pre;
                            }
                    tr:nth-child(even){
                               background-color: #f2f2f2;
                            }
                    tr:hover {
                               background-color: #d4fad9;
                            }
                    th a {
                            width: 100%;
                            height: 100%;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        }
                    a {
                            color: inherit;
                            text-decoration: inherit;
                    }
                    thead th:hover { 
                            background-color: #d4fad9;
                            color: black;     
                        }
                    tr th:hover { 
                            background-color: #d4fad9;
                            color: black;     
                        }
            </style>"""
    # remove unecessary row for "Name" label
    preferences.index.name = None
    emoji_table = preferences.to_html(escape=False)  # Convert to HTML table
    html_table = (
        css + """<div class="tableFixHead">""" + emoji_table + """</div>"""
    )  # Add CSS to table
    return html_table


def get_all_preferences_table(wim=None, first_date=None, last_date=None):
    """
    Create the HTML table described in get_preferences() with default settings
    i.e. for all team members with at least one preference emoji and all projects
    with some resource requirement.
    """
    credentials = config.get_github_credentials()
    token = credentials["token"]

    if not wim:
        wim = Wimbledon(update_db=True, with_tracked_time=False)
    preference_data_df = get_preference_data(wim, token)
    preferences_with_availability = get_preferences(
        wim, preference_data_df, first_date=first_date, last_date=last_date
    )
    return preferences_with_availability
