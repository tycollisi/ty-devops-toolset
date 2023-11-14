import jenkins
from dotenv import load_dotenv
import os


COLORS = {
    "BLUE": "\033[94m",
    "GREEN": "\033[0;32m",
    "RED": "\033[91m",
    "ENDC": "\033[0m"
}

def colorize(text, color):
    """Return text wrapped in ANSI color codes."""
    return COLORS[color] + text + COLORS["ENDC"]

def is_disabled(job):
    return job.get('color') in ["disabled", "disabled-anime"]

def print_jobs(job, prefix='', continuation_prefix='', printed_paths=set()):
    """Recursive function to print jobs in a tree structure."""
    
    full_name = job['fullname']
    
    # Avoid printing duplicates
    if full_name in printed_paths:
        return
    
    printed_paths.add(full_name)
    
    # Determine job name and if it's disabled
    job_name = full_name.split('/')[-1]
    if is_disabled(job):
        job_name = colorize(job_name + " *JOB DISABLED*", "RED")
    
    # Print current job/folder
    if 'jobs' in job and '/' in full_name:  # If the current job has subjobs, consider it a service.
        print(prefix + colorize(job_name, "BLUE"))
    elif job_name in ["test", "production"]:
        print(prefix + colorize(job_name, "GREEN"))
    else:
        print(prefix + job_name)

    # If there are subjobs, print them with new prefixes
    if 'jobs' in job:
        subjobs = job['jobs']
        for index, subjob in enumerate(subjobs):
            next_prefix = continuation_prefix + ('└── ' if index == len(subjobs)-1 else '├── ')
            new_continuation_prefix = continuation_prefix + ('    ' if index == len(subjobs)-1 else '│   ')
            print_jobs(subjob, next_prefix, new_continuation_prefix, printed_paths)

# Connect to Jenkins
jenkins_url = "http://locahost:8080"
user = "tycollisi"

# Get Jenkins API Key
load_dotenv()
JENKINS_API_KEY = os.getenv("JENKINS_API")

server = jenkins.Jenkins(jenkins_url, username=user, password=JENKINS_API_KEY)

# Fetch all jobs
jobs = server.get_all_jobs(folder_depth=None, folder_depth_per_request=10)

# Start printing the tree structure
for index, job in enumerate(jobs):
    # Only process top-level jobs/folders (those without '/' in their fullname)
    if '/' not in job['fullname']:
        prefix = ('└── ' if index == len(jobs)-1 else '├── ')
        continuation_prefix = ('    ' if index == len(jobs)-1 else '│   ')
        print_jobs(job, prefix, continuation_prefix)
