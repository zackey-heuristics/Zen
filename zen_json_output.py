"""
This module is used to output Zen results in JSON format.

Usage:
    python zen_json_output.py [GITHUB_USERNAME] [--token GITHUB_TOKEN] [--output OUTPUT_JSON_FILE_PATH]
    python zen_json_output.py [GITHUB_USERNAME_URL] [--token GITHUB_TOKEN] [--output OUTPUT_JSON_FILE_PATH]
    python zen_json_output.py [GITHUB_REPOSITORY_URL] [--token GITHUB_TOKEN] [--output OUTPUT_JSON_FILE_PATH]
    python zen_json_output.py [GITHUB_ORGANIZATION_NAME] --org [--token GITHUB_TOKEN] [--output OUTPUT_JSON_FILE_PATH]
"""
import argparse
import datetime
import json
from math import e
import pathlib
import re
import sys
from urllib import response
from typing import Optional

import requests


def find_contributors_from_repo(username: str, repo: str, authorization_token: Optional[str] = None) -> list[str]:
    """
    Find contributors from a repository.
    
    Args:
        username (str): GitHub username
        repo (str): GitHub repository name
        authorization_token (str, optional): GitHub token
    
    Returns:
        contributors (list[str]): List of contributors
    """
    if authorization_token:
        headers = {"Authorization": f"token {authorization_token}"}
        response = requests.get('https://api.github.com/repos/%s/%s/contributors?per_page=100' % (username, repo), headers=headers).text
    else:
        response = requests.get('https://api.github.com/repos/%s/%s/contributors?per_page=100' % (username, repo)).text
        
    contributors = re.findall(r'https://github\.com/(.*?)"', response)
    return contributors


def find_repos_from_username(username: str, authorization_token: Optional[str] = None) -> list[str]:
    """
    Find repositories from a username.
    
    Args:
        username (str): GitHub username
    
    Returns:
        list[str]: List of repositories
    """
    if authorization_token:
        headers = {"Authorization": f"token {authorization_token}"}
        response = requests.get('https://api.github.com/users/%s/repos?per_page=100&sort=pushed' % username, headers=headers).text
    else:
        response = requests.get('https://api.github.com/users/%s/repos?per_page=100&sort=pushed' % username).text
        
    repos = re.findall(r'"full_name":"%s/(.*?)",.*?"fork":(.*?),' % username, response)
    non_forked_repos = []
    for repo in repos:
        if repo[1] == 'false':
            non_forked_repos.append(repo[0])
    return non_forked_repos


def find_users_from_organization(organization: str, authorization_token: Optional[str] = None) -> list[str]:
    """
    Find users from an organization.
    
    Args:
        organization (str): GitHub organization name
    
    Returns:
        members (list[str]): List of users
    """
    if authorization_token:
        headers = {"Authorization": f"token {authorization_token}"}
        response = requests.get('https://api.github.com/orgs/%s/members?per_page=100' % organization, headers=headers).text
    else:
        response = requests.get('https://api.github.com/orgs/%s/members?per_page=100' % organization).text
        
    members = re.findall(r'https://github\.com/(.*?)"', response)
    return members


def find_email_from_contributor(username: str, repo: str, contributor: str, authorization_token: Optional[str] = None) -> dict[str, str]:
    """
    Find email from a contributor.
    
    Args:
        username (str): GitHub username
        repo (str): GitHub repository name
        contributor (str): GitHub contributor name
    
    Returns:
        dict[str, str]: Email of the contributor
    """
    if authorization_token:
        headers = {"Authorization": f"token {authorization_token}"}
    
    return_results: dict[str, str] = {}
    
    if authorization_token:
        response = requests.get('https://github.com/%s/%s/commits?author=%s' % (username, repo, contributor), headers=headers).text
    else:
        response = requests.get('https://github.com/%s/%s/commits?author=%s' % (username, repo, contributor)).text
    
    latest_commit = re.search(r'href="/%s/%s/commit/(.*?)"' % (username, repo), response)
    if latest_commit:
        latest_commit = latest_commit.group(1)
    else:
        latest_commit = 'dummy'
    
    if authorization_token:
        commit_details = requests.get('https://github.com/%s/%s/commit/%s.patch' % (username, repo, latest_commit), headers=headers).text
    else:
        commit_details = requests.get('https://github.com/%s/%s/commit/%s.patch' % (username, repo, latest_commit)).text
    
    email = re.search(r'<(.*)>', commit_details)
    if email:
        email = email.group(1)
        return_results[contributor] = {}
        return_results[contributor]['email'] = email
        if requests.get('https://haveibeenpwned.com/api/v2/breachedaccount/' + email).status_code == 200:
            return_results[contributor]['pwned'] = True
        else:
            return_results[contributor]['pwned'] = False
    else:
        return_results[contributor] = email
    
    return return_results


def find_email_from_username(username: str, authorization_token: Optional[str] = None) -> dict[str, str]:
    """
    Find email from a username.
    
    Args:
        username (str): GitHub username
    
    Returns:
        dict[str, str]: Email of the username
    """
    repos = find_repos_from_username(username, authorization_token)
    for repo in repos:
        return_results = find_email_from_contributor(username, repo, username, authorization_token)
        if return_results:
            return return_results
    return {}


def find_emails_from_repo(username: str, repo: str, authorization_token: Optional[str] = None) -> dict[str, str]:
    """
    Find emails from a repository.
    
    Args:
        username (str): GitHub username
        repo (str): GitHub repository name
    
    Returns:
        dict[str, str]: Emails of the contributors
    """
    contributors = find_contributors_from_repo(username, repo, authorization_token)
    return_results = {}
    for contributor in contributors:
        return_results.update(find_email_from_contributor(username, repo, contributor, authorization_token))
    return return_results


def find_emails_from_organization_usernames(usernames: list[str], authorization_token: Optional[str] = None) -> dict[str, str]:
    """
    Find emails from organization usernames.
    
    Args:
        usernames (list[str]): List of GitHub usernames
    
    Returns:
        dict[str, str]: Emails of the usernames
    """
    return_results = {}
    for username in usernames:
        return_results.update(find_email_from_username(username, authorization_token))
    return return_results
    

def main():
    parser = argparse.ArgumentParser(description="Output Zen results in JSON format.")
    parser.add_argument("target", help="GITHUB_USERNAME, GITHUB_USERNAME_URL, GITHUB_REPOSITORY_URL, or GITHUB_ORGANIZATION_NAME")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--token", help="GitHub token")
    parser.add_argument("--org", help="Organization", action="store_true")
    args = parser.parse_args()
    target = args.target
    output = args.output
    if args.token:
        authorization_token = args.token
    else:
        authorization_token = None
    is_target_organization = args.org
    
    # remove the trailing slash from the target string if it exists
    if target.endswith("/"):
        target = target[:-1]
    
    target_organization = target_repo = target_user = False
    
    # check input target type
    if target.count("/") < 4:
        if "/" in target:
            username = target.split("/")[-1]
        else:
            username = target
        if is_target_organization:
            target_organization = True
        else:
            target_user = True
    elif target.count("/") == 4:
        target_repo = target.split("/")
        username = target_repo[-2]
        repo = target_repo[-1]
        target_repo = True
    else:
        print("Invalid input target type.", file=sys.stderr)
        sys.exit(1)
    
    # find emails
    if target_organization:
        usernames = find_users_from_organization(username, authorization_token)
        json_result = find_emails_from_organization_usernames(usernames, authorization_token)
    elif target_user:
        json_result = find_email_from_username(username, authorization_token)
    elif target_repo:
        json_result = find_emails_from_repo(username, repo, authorization_token)
    
    # Output the result
    if output:
        with open(output, "w") as f:
            json.dump(json_result, f, indent=4, ensure_ascii=False)
        print(f"{pathlib.Path(output).resolve()}")
    else:
        print(json.dumps(json_result, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()

