# An example to get the remaining rate limit using the Github GraphQL API.

import requests
import json

with open('github.token', 'r') as f:
    token = f.read()

headers = {"Authorization": "Bearer " + token}


def run_query(query):  # A simple function to use requests.post to make the API call. Note the json= section.
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))


query = """
{
  repository(owner:"alan-turing-institute", name:"Hut23") {
    issue(number:174) {
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

result = run_query(query)  # Execute the query

try:
    print(json.dumps(result['data'], indent=1))
except:
    print(json.dumps(result, indent=1))


emojis = {'CONFUSED': '😕',
          'EYES': '👀',
          'HEART': '❤️',
          'HOORAY': '🎉',
          'LAUGH': '😄',
          'ROCKET': '🚀',
          'THUMBS_DOWN': '👎',
          'THUMBS_UP': '👍'}

