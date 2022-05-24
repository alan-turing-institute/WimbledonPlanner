"""Script for getting Github emojis for Hut23 issues.
Contributor: Script written by @mhauru to get reactions with PyGitHub:
Usage:
    python3 -m pip install PyGithub
    export GITHUB_TOKEN=generate-a-github-API-token-with-repo-rights-and-paste-it-here
    python3 emojis.py some-issue-number maybe-another-issue-number
"""
from github import Github
import emoji as my_emoji
import os
import sys


def getEmoji(reaction:str):
    if (reaction=='laugh'):
        return my_emoji.emojize(':grinning_face_with_smiling_eyes:')
    if (reaction=='+1'):
        return my_emoji.emojize(':thumbs_up:')
    if (reaction=='-1'):
        return my_emoji.emojize(':thumbs_down:')
    return my_emoji.emojize(':red_question_mark:')

def main():
    org_name = "alan-turing-institute"
    repo_name = "Hut23"

    token = os.environ["GITHUB_TOKEN"]
    g = Github(token)
    org = g.get_organization(org_name)
    repo = org.get_repo(repo_name)

    for issue_number in sys.argv[1:]:
        issue_number = int(issue_number)
        issue = repo.get_issue(issue_number)
        print(f"# Issue: {issue.title} ({issue.number})")

        # Initialising with the standard emojis here ensures that when listing
        # results at the end these three come first, in this order, with all
        # others at the end.
        reaction_dict = {"laugh": [], "+1": [], "-1": []}
        for r in issue.get_reactions():
            emoji = r.content
            if emoji not in reaction_dict:
                reaction_dict[emoji] = []
            # Use the display name, or login name if that doesn't exist.
            name = r.user.name
            if not name:
                name = r.user.login
            reaction_dict[emoji].append(name)

        for k, v in reaction_dict.items():
            emoji_str = getEmoji(k) + f" Count: {len(v)}"
            print(emoji_str)
            # print(f"Reaction: {k}, count: {len(v)}")
            print("  ", end="")
            for name in sorted(v):
                print(name, end=", ")
            print()


if __name__ == "__main__":
    main()
    # print(emoji.emojize('Python is :thumbs_up:'))