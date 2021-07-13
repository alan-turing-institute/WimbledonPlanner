import requests
import pandas as pd
import math
from datetime import datetime
import statistics
from wimbledon import Wimbledon
from wimbledon import config


repo_query_template = """
{{
    repository(owner:"alan-turing-institute", name:"Hut23") {{
        {issue_queries}
    }}
}}
"""

issue_query_template = """
issue{issue_number}: issue(number:{issue_number}) {{
    number
    title
    url

    reactionGroups {{
        content
        users(first:{n_users}) {{
            edges {{
                node {{
                    login
                    name
                }}
            }}
        }}
    }}
}}
"""

comment_query_template = """
issue{issue_number}: issue(number:{issue_number}) {{
    number
    title
    url
    comments(first:{n_comment}) {{
        edges {{
            node {{
                reactionGroups {{
                    content
                    users(first:{n_users}) {{
                        edges {{
                            node {{
                                login
                                name
                            }}
                        }}
                    }}
                }}
            }}
        }}
    }}
}}
"""

# People without their full names on github.
default_gid_mapping = {
    "May Yong": "myyong",
    "Nick Barlow": "nbarlowATI",
    "Timothy Hobson": "thobson88",
    "Oscar Giles": "OscartGiles",
    "Ashwini Venkatasubramaniam": "AshwiniKV",
    "Peter Foster": "pafoster",
    "Flora Roumpani": "entopia",
    "Oliver Strickson": "ots22",
}

# Map the emojis from GitHub to those we want to display
default_emoji_mapping = {
    "CONFUSED": "😕",
    "EYES": "👀",
    "HEART": "❤️",
    "HOORAY": "🎉",
    "ROCKET": "🚀",
    "THUMBS_DOWN": "❌",
    "THUMBS_UP": "👍",
    "LAUGH": "✅",
    "None": "❓",
}

default_css = """
<style>
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
</style>
"""


def build_query(issue_numbers, n_users=20, n_comments=1):
    """Build query for extracting emoji reactions from the Hut23 repo.

    Parameters
    ----------
    issue_numbers : list
        Issue numbers to query
    n_users : int, optional
        Max number of users to query per emoji reaction, by default 20
    n_comments : int, optional
        Query this many issue comments, by  default 1 (only main issue body)

    Returns
    -------
    str
        GraphQL query string to send to the GitHub API

    Raises
    ------
    ValueError
        If number of query nodes exceeds 50,000 (GitHub limit), where the number of
        nodes is 1 + n_issues + n_comments * n_issues + n_users * n_issues  * n_comments
    """
    issue_numbers = set(issue_numbers)  # remove any duplicate issue numbers
    n_issues = len(issue_numbers)
    n_nodes = 1 + n_issues + n_users * n_issues * n_comments
    if n_comments > 1:
        n_nodes += n_comments * n_issues
    if n_nodes >= 50000:
        raise ValueError(
            f"Querying {n_issues} with {n_users} users per emoji reaction will exceed "
            f"GitHub's API limits of 50,000 nodes (query has {n_nodes})"
        )

    if n_comments > 1:
        issue_queries = " ".join(
            comment_query_template.format(
                issue_number=isno, n_users=n_users, n_comments=n_comments
            )
            for isno in issue_numbers
        )
    else:
        issue_queries = " ".join(
            issue_query_template.format(issue_number=isno, n_users=n_users)
            for isno in issue_numbers
        )

    return repo_query_template.format(issue_queries=issue_queries)


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


def unpack_issue_reactions(reactions):
    """
    Convert reactions for one issue (aw returned by the GitHub API) into a pandas
    DataFrame with 1 row per reaction and columns 'name', 'username' and 'emoji' for
    the persono's name on GitHub, GitHub username and their reaction to the issue
    respectively.
    """
    unpacked = []
    for emoji in reactions:
        emoji_name = emoji["content"]
        unpacked += [
            {
                "name": user["node"]["name"],
                "username": user["node"]["login"],
                "emoji": emoji_name,
            }
            for user in emoji["users"]["edges"]
        ]
    return pd.DataFrame(unpacked)


def get_reactions(token, issue_numbers, n_users=20):
    """
    Get a dictionary of the emoji reactions that exist for a GitHub issue in the
    strutcture specified by the GraphQL queries
    """

    # Edit the query string to contain the relevant issue and number of GitHub users
    # This query gets the emojis on the issue itself (i.e. the top comment/ post)
    query = build_query(issue_numbers, n_users=n_users, n_comments=1)
    result = run_query(query, token)
    return {
        issue["number"]: unpack_issue_reactions(issue["reactionGroups"])
        for _, issue in result["data"]["repository"].items()
    }


def get_person_availability(wim, person, start_date, end_date):
    """
    Get the mean of a person's FTE proportion available for the start to end date,
    using their name or id
    """
    peopledf = wim.people_free_capacity
    if isinstance(person, str):
        try:
            person = wim.get_person_id(person)
        except (IndexError, KeyError):
            return 0.0
    peopledf = peopledf[(peopledf.index >= start_date) & (peopledf.index <= end_date)]
    try:
        availability_range = peopledf[person]
    except (IndexError, KeyError):
        return 0.0

    if len(availability_range) > 0 and availability_range.sum() > 0:
        return availability_range.mean()
    else:
        return 0.0


def get_preference_data(
    wim,
    github_token,
    start_date,
    end_date,
    emoji_mapping=default_emoji_mapping,
    gid_mapping=default_gid_mapping,
):
    """
    Get each team members preference emoji for all projects with a GitHub issue.
    Return a pandas df with person against project and their preference emoji.
    Custom emoji mapping can be provided.
    """

    # Get list of GitHub issues for projects
    proj_idx = wim.get_active_projects(start_date, end_date, names=False)
    issues = wim.projects.loc[proj_idx, "github"].dropna().astype(int)
    # Get a list of people active in the team
    names = wim.get_active_people(start_date, end_date, names=True, partners=False)
    names = list(names)
    total_people = len(names)

    all_reactions = get_reactions(github_token, issues, n_users=total_people)

    preference_data = {"Person": names}

    for project_id, issue_num in issues.iteritems():
        # Get a dict with the emoji reactions for this issue
        proj_react = all_reactions[issue_num]
        emojis = []

        # Get the relevant emoji for each team member for this GitHub issue and
        # associated project
        for name in names:
            if len(proj_react) == 0:
                emoji_name = "None"
            elif name in proj_react["name"].values:
                emoji_name = proj_react[proj_react["name"] == name].iloc[0]["emoji"]
            elif (
                name in gid_mapping
                and gid_mapping[name] in proj_react["username"].values
            ):
                emoji_name = proj_react[
                    proj_react["username"] == gid_mapping[name]
                ].iloc[0]["emoji"]
            else:
                # For team members who have not given a preference
                emoji_name = "None"
            emojis.append(emoji_mapping[emoji_name])

        preference_data[wim.get_project_name(project_id)] = emojis

    # Remove any team members without emoji preferences for any project
    # preference_data_df = preference_data_df.loc[
    #    ~(preference_data_df == "❓").all(axis=1)
    # ]
    return pd.DataFrame(preference_data).set_index("Person")


def make_preferences_table(
    wim,
    preference_data_df,
    first_date=datetime.now(),
    last_date=False,
    person=False,
    project=False,
    emojis_only=False,
    css=default_css,
):
    """
    Create a HTML table with each project that has a people requirement against every
    REG team member with availability. Table values show the preference emojis alongside
    the mean availability the person has for the people required period and the mean
    people required for the range between the first month with people required and
    the last.
    """

    # Get the data on project people required, unconfirmed and allocated from Forecast
    peoplereqdf = wim.project_peoplereq
    unconfdf = wim.project_unconfirmed
    allocdf = wim.project_allocated
    totdf = peoplereqdf + unconfdf + allocdf

    if first_date:
        peoplereqdf = peoplereqdf[peoplereqdf.index >= first_date]
        unconfdf = unconfdf[unconfdf.index >= first_date]
        allocdf = allocdf[allocdf.index >= first_date]
        totdf = totdf[totdf.index >= first_date]

    if last_date:
        peoplereqdf = peoplereqdf[peoplereqdf.index <= last_date]
        unconfdf = unconfdf[unconfdf.index <= last_date]
        allocdf = allocdf[allocdf.index <= last_date]
        totdf = totdf[totdf.index <= last_date]

    names = [person] if person else list(preference_data_df.index)
    data = {"Person": names}
    # If a project name or project id is provided, only get data for that project
    if project and isinstance(project, str):
        try:
            project = wim.get_project_id(project)
        except (IndexError, KeyError):
            pass

    # Get projects with some people requirement but filter by those with a GitHub
    # issue
    project_titles = {}
    for project_id in peoplereqdf:
        if project and project != project_id:
            continue

        project_name = wim.projects.loc[project_id, "name"]
        if project_name not in preference_data_df.columns:
            continue

        # If a project name or project id is provided, only get data for that
        # project. Get the dates for each month that the project has a people
        # requirement > 0
        dates_peoplereq = peoplereqdf.index[peoplereqdf[project_id] > 0]
        dates_unconf = unconfdf.index[unconfdf[project_id] > 0]
        dates_alloc = allocdf.index[allocdf[project_id] > 0]

        issue_num = wim.projects.loc[project_id]["github"]
        if (
            len(dates_peoplereq) > 0 or len(dates_unconf) > 0 or len(dates_alloc) > 0
        ) and not math.isnan(issue_num):
            dates_req = totdf.index[totdf[project_id] > 0]
            req_start_date = dates_req[0]
            req_end_date = dates_req[-1]

            if first_date and req_start_date < first_date:
                req_start_date = first_date
            if last_date and req_end_date > last_date:
                req_end_date = last_date

            project_title = (
                project_name
                + "<br>#"
                + str(int(issue_num))
                + "<br>"
                + req_start_date.strftime("%Y-%m")
                + " to "
                + req_end_date.strftime("%Y-%m")
                + "<br>"
                + "FTE: "
            )

            if len(dates_alloc) > 0:
                # if at least one month in the dataframe has a people requirement
                # of more than 0 FTE
                first_alloc_date = dates_alloc[0]
                last_alloc_date = dates_alloc[-1]
                if first_date and first_alloc_date < first_date:
                    first_alloc_date = first_date
                if last_date and last_alloc_date > last_date:
                    last_alloc_date = last_date

                # get mean project requirement in date range
                alloc = allocdf.loc[
                    (allocdf.index >= first_alloc_date)
                    & (allocdf.index <= last_alloc_date),
                    project_id,
                ].mean()

                if alloc >= 0.01:
                    project_title += str(round(alloc, 1)) + " A"
            else:
                alloc = 0

            if len(dates_peoplereq) > 0:
                # if at least one month in the dataframe has a people requirement
                # of more than 0 FTE
                first_peoplereq_date = dates_peoplereq[0]
                last_peoplereq_date = dates_peoplereq[-1]
                if first_date and first_peoplereq_date < first_date:
                    first_peoplereq_date = first_date
                if last_date and last_peoplereq_date > last_date:
                    last_peoplereq_date = last_date

                # get mean project requirement in date range
                peoplereq = peoplereqdf.loc[
                    (peoplereqdf.index >= first_peoplereq_date)
                    & (peoplereqdf.index <= last_peoplereq_date),
                    project_id,
                ].mean()

                if peoplereq >= 0.01:
                    pre = " + " if len(dates_alloc) > 0 else ""
                    post = " R"
                    project_title += pre + "" + str(round(peoplereq, 1)) + post
            else:
                peoplereq = 0

            if len(dates_unconf) > 0:
                # if at least one month in the dataframe has a people requirement
                # of more than 0 FTE
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
                    # add a separator between required and unconfirmed FTE if both
                    # present
                    if len(dates_peoplereq) > 0 or len(dates_alloc) > 0:
                        pre = " + "
                    else:
                        pre = ""
                    post = " U"
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
                    wim, name, req_start_date, req_end_date
                )

                if (unconf + peoplereq) > 0:
                    percentage_availability = round(
                        (person_availability / (unconf + peoplereq)) * 100
                    )
                else:
                    percentage_availability = None

                emoji = preference_data_df[project_name][name]
                if emojis_only or percentage_availability is None:
                    emoji_data.append(emoji)
                else:  # Include availability
                    emoji_data.append(
                        emoji
                        + " "
                        + str(percentage_availability)
                        + "% ("
                        + str(round(person_availability, 1))
                        + " / "
                        + str(round(unconf + peoplereq, 1))
                        + ")"
                    )
            # Store list of preference data for this project
            data[project_name] = emoji_data

    # Created an alphabetically sorted dataframe from the data
    preferences = pd.DataFrame(data).set_index("Person").sort_index().sort_index(axis=1)
    preferences = preferences.rename(columns=project_titles)

    # Create a HTML table from this dataframe
    # remove unecessary row for "Name" label
    preferences.index.name = None
    emoji_table = preferences.to_html(escape=False)  # Convert to HTML table
    return css + """<div class="tableFixHead">""" + emoji_table + """</div>"""


def get_all_preferences_table(wim=None, first_date=datetime.now(), last_date=None):
    """
    Create the HTML table described in make_preferences_table() with default settings
    i.e. for all team members with at least one preference emoji and all projects
    with some people requirement.
    """
    credentials = config.get_github_credentials()
    token = credentials["token"]

    if not wim:
        wim = Wimbledon(update_db=True, with_tracked_time=False)
    preference_data_df = get_preference_data(wim, token, first_date, last_date)
    return make_preferences_table(
        wim, preference_data_df, first_date=first_date, last_date=last_date
    )
