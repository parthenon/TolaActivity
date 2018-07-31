#! /usr/local/bin/python2

"""
This script uses GitHub APIs to fetch a list of issues associated with a project.
It outputs issue numbers and titles for all cards in all columns of the project.
The output is particularly useful for putting into the GitHub release notes.
"""

import requests
from requests.auth import HTTPBasicAuth
import json
import sys
import re

headers = {'Accept': 'application/vnd.github.inertia-preview+json'}

project_name = raw_input('Enter the project name: ')
print '\nEnter 1 to use GitHub token authorization (https://github.com/settings/tokens)'
print 'Enter 2 to use GitHub username and password: '
auth_pref = raw_input('Enter 1 or 2: ')
if auth_pref == '1':
    token = raw_input('GitHub token: ')
    headers['Authorization'] = 'token %s' % token
    auth = ''
elif auth_pref == '2':
    username = raw_input('GitHub username: ')
    password = raw_input('GitHub password: ')
    auth = HTTPBasicAuth(username, password)
else:
    print type(auth_pref)
    print 'You must choose either 1 or 2.  You chose %s. Exiting.' % auth_pref
    sys.exit()

projects_url = 'https://api.github.com/repos/mercycorps/TolaActivity/projects'
columns_template = 'https://api.github.com/projects/%s/columns'
cards_template = 'https://api.github.com/projects/columns/%s/cards'
issue_template = 'https://api.github.com/repos/mercycorps/TolaActivity/issues/%s'

# Get the project id
print 'Fetching data'
response = requests.get(projects_url, headers=headers, auth=auth)
projects = json.loads(response.text)
project_id = ''
columnn_ids = []
for project in projects:
    pname = project['name'].strip()
    if project_name == pname:
        project_id = project['id']
        break
else:
    print "The project you entered couldn't be found in the list of your" \
        "available projects. Exiting."
    sys.exit()

# Get the columns ids associated with the project
columns_url = columns_template % project_id
response = requests.get(columns_url, headers=headers, auth=auth)

column_ids = [col['id'] for col in json.loads(response.text)]
for col_id in column_ids:

    # Loop through each card in each column and the the issue data associated
    # with the card
    cards_url = cards_template % col_id
    cards_response = requests.get(cards_url, headers=headers, auth=auth)

    issues = []
    for card in json.loads(cards_response.text):
        match = re.search('(\d+)$', card['content_url'])
        issue_num = match.group(1)
        issue_url = issue_template % issue_num
        issue_response = requests.get(issue_url, headers=headers, auth=auth)
        issues.append((issue_num, json.loads(issue_response.text)['title']))

issues.sort(key=lambda k: int(k[0]), reverse=True)
print ''
for i in issues:
    print '#%s - %s' % (i)
