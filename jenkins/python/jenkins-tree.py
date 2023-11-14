import jenkins
from dotenv import load_dotenv
import os

def is_disabled(job):
    """Check if a job is disabled."""
    return job.get('color') in ["disabled", "disabled-anime"]

def print_jobs(job, prefix='', continuation_prefix='', printed_paths=set()):
    """Recursive function to print jobs in a tree structure."""

    full_name = job['fullname']

    if full_name in printed_paths:
        return

    printed_paths.add(full_name)

    job_name = full_name.split('/')[-1]
    disabled_status = " *JOB DISABLED*" if is_disabled(job) else ""

    print(f"{prefix}{job_name}{disabled_status}")

    for index, subjob in enumerate(job.get('jobs', [])):
        next_prefix = f"{continuation_prefix}{'└── ' if index == len(job['jobs'])-1 else '├── '}"
        new_continuation_prefix = f"{continuation_prefix}{'    ' if index == len(job['jobs'])-1 else '│   '}"
        print_jobs(subjob, next_prefix, new_continuation_prefix, printed_paths)

jenkins_url = "http://localhost:8080"
user = "tycollisi"

load_dotenv()
JENKINS_API_KEY = os.getenv("JENKINS_API")

server = jenkins.Jenkins(jenkins_url, username=user, password=JENKINS_API_KEY)

jobs = server.get_all_jobs(folder_depth=None, folder_depth_per_request=10)

for index, job in enumerate(jobs):
    if '/' not in job['fullname']:  # Process only top-level jobs/folders
        prefix = '└── ' if index == len(jobs)-1 else '├── '
        continuation_prefix = '    ' if index == len(jobs)-1 else '│   '
        print_jobs(job, prefix, continuation_prefix)
