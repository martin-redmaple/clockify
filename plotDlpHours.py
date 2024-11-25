from dotenv import load_dotenv
import os
import requests
import json
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import calendar

load_dotenv()  # take environment variables from .env.

# Get the Clockify access token
CLOCKIFY_API_KEY = os.environ["CLOCKIFY_API_KEY"]

# Define the Clockify base URL
CLOCKIFY_BASE_URL = "https://api.clockify.me/api/v1"
CLOCKIFY_REPORTS_URL = "https://reports.api.clockify.me/v1"

# Define the timespan that we want time entries from
START_DATETIME = datetime.datetime(
    2023, 12, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

STOP_DATETIME = datetime.datetime(
    2024, 11, 30, 23, 59, 59, tzinfo=datetime.timezone.utc)

# Define the days per month to plot the expected burn line
DAYS_PURCHASED = [
    (datetime.datetime(2023, 12, 1), 7),
    (datetime.datetime(2024,  1, 1), 7),
    (datetime.datetime(2024,  2, 1), 7),
    (datetime.datetime(2024,  3, 1), 6),
    (datetime.datetime(2024,  4, 1), 5),
    (datetime.datetime(2024,  5, 1), 5),
    (datetime.datetime(2024,  6, 1), 5),
    (datetime.datetime(2024,  7, 1), 5),
    (datetime.datetime(2024,  8, 1), 5),
    (datetime.datetime(2024,  9, 1), 5),
    (datetime.datetime(2024, 10, 1), 5),
    (datetime.datetime(2024, 11, 1), 5)
]

# Define the hours in a work day
WORK_DAY_HOURS = 8

# Define the project that we want time entries for
PROJECT = "DevOps Support 23/24 - RMSOW23058"

# Define the auth headers
getHeaders = {
    'x-api-key': CLOCKIFY_API_KEY
}
postHeaders = {
    'x-api-key': CLOCKIFY_API_KEY,
    'content-type': 'application/json'
}

# Get the list of workspaces
resp = requests.get(f"{CLOCKIFY_BASE_URL}/workspaces", headers=getHeaders)
workspaces = resp.json()

# Get the workspace ID for the Hexiosec Workspace
workspaceId = None
for workspace in workspaces:
    if workspace['name'] == "Hexiosec":
        workspaceId = workspace['id']

# Get a list of all the projects in the workspace
resp = requests.get(
    f"{CLOCKIFY_BASE_URL}/workspaces/{workspaceId}/projects", headers=getHeaders)
projects = resp.json()

# Get the workspace ID for the project
projectId = None
for project in projects:
    if project['name'] == PROJECT:
        projectId = project['id']

if projectId == None:
    raise RuntimeError("Failed to find specified project")

# Get the detailed report
body = {
    'dateRangeStart': START_DATETIME.strftime('%Y-%m-%dT%H:%M:%SZ'),
    'dateRangeEnd': STOP_DATETIME.strftime('%Y-%m-%dT%H:%M:%SZ'),
    'projects': {
        'ids': [projectId]
    },
    'detailedFilter': {
        'pageSize': 1000
    }
}
resp = requests.post(
    f"{CLOCKIFY_REPORTS_URL}/workspaces/{workspaceId}/reports/detailed", headers=postHeaders, data=json.dumps(body))
timeEntries = resp.json()

# Create a list of the entries
timeUsed = [(START_DATETIME, 0)]
for timeEntry in timeEntries['timeentries']:
    # form the tuple of the date and total
    item = (datetime.datetime.fromisoformat(
        timeEntry['timeInterval']['start']), timeEntry['timeInterval']['duration']/3600)

    timeUsed.append(item)

# Now sort the timeUsed entries by the date
timeUsed.sort(key=lambda tup: tup[0])

# Now run along the list of entries and generate the cumulative total
cumulativeTotal = 0
timeUsedCumulative = []
for entry in timeUsed:
    cumulativeTotal += entry[1]
    timeUsedCumulative.append((entry[0], cumulativeTotal))

# Transform the days purchased data into something that we can plot
timeExpected = []
timeExpectedCumulative = 0
# Add a zero at the start
timeExpected.append((DAYS_PURCHASED[0][0], 0))
for monthValue in DAYS_PURCHASED:
    # Get the last working day of the month
    lastMonthDay = calendar.monthrange(
        monthValue[0].year, monthValue[0].month)[1]
    monthEndDate = datetime.datetime(
        monthValue[0].year, monthValue[0].month, lastMonthDay)
    # Sum up the cumulative time
    timeExpectedCumulative += monthValue[1]*WORK_DAY_HOURS
    timeExpected.append((monthEndDate, timeExpectedCumulative))


plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
plt.plot(*zip(*timeUsedCumulative), marker='.')
plt.plot(*zip(*timeExpected), marker='.')
plt.gcf().autofmt_xdate()
plt.grid()
plt.xlabel("Date")
plt.ylabel("Hours")
plt.title(f"DLP Hours Used (as of {
          datetime.datetime.now().strftime("%Y/%m/%d")})")

plt.show()


print("DONE")
