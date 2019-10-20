# coding: utf8
"""
"THE BEER-WARE LICENSE" (Revision 42):
Remy CHATEL <remychatel@fastmail.com> wrote this file.  As long as you retain this notice you can do whatever you want with this stuff. If we meet some day, and you think this stuff is worth it, you can buy me a beer in return.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from ics import Calendar, Event
from datetime import datetime, timedelta, timezone
from urllib.request import urlopen
from enum import Enum
import sys
class sortKey(Enum):
    ALPHABETICAL = 0
    START_DATE = 1
    COMPLETED = 3
    REMAINING = 4
#-------------------------------------------------------------------------------#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
"""
Report Settings
    url: The ics address of the timetable
    excluded_strings: List of word to filter non relevant entries
    keyword_lab: List of word to identify graded labs
    keyword_exam: List of word to identify exams
    hide_past: Whether to hide past exams and labs in the report
    hide_completed: Whether to hide completed courses
    sort: Key to sort by (ALPHABETICAL, START_DATE, COMPLETED, REMAINING)
    remote: Fetches the calendar from the Internet, otherwise, uses local calendar at the given URL
"""
url = ""
excluded_strings = ["VACANCES", "J3A", "PRESENTATION", "ACCUEIL", "FORUM", "Village", "FERIE", "REUNION", "BILAN", "SISY-TRONC COMMUN", "Soutenances SFE"]
keyword_lab = ["BE noté", "PC notée"]
keyword_exams = ["Exam", "Examen", "QCM", "Test"]
hide_past = True
hide_completed = True
sort = sortKey.COMPLETED
remote = True
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if (remote and not "https://hyperplng.isae-supaero.fr/hp/Telechargements/ical/Edt_" in url) or url == "":
    print("\nInvalid url: please import valid URL from Hyperplanning")
    sys.exit()

if remote:
    c = Calendar(urlopen(url).read().decode())
else:
    c = Calendar(open(url, 'r').read()) # Uncomment here to use local .ics file

courses = []
graded = []

# Parsing
for e in c.events:
    # Test for excluded words
    if not any([(word in e.name) for word in excluded_strings]):
        # Extract data from event
        title = e.name.split(" - ")
        code = title[0]
        name = title[1]
        date = e.begin
        length = e.duration.seconds//60
        ellapsed = length if date <= datetime.now(timezone.utc) else 0
        # Check if course already in list
        if any([(code in event[0]) for event in courses]):
            # If true, then add length to the course
            for course in courses:
                if code in course[0]:
                    course[2] += length
                    course[3] += ellapsed
                    course[4] =  date if date < course[4] else course[4]
                    course[5] =  date if date > course[5] else course[5]
        else:
            # Add the course otherwise
            courses.append([code, name, length, ellapsed, date, date, [], []])
        # Check if it is a graded lab or an exam
        if any([word in e.description for word in keyword_lab]):
            for course in courses:
                if code in course[0] and not any([date.day == date_be.day and date.month and date_be.month for date_be in course[6]]):
                    course[6].append(date)
        elif any([word in e.description for word in keyword_exams]):
            for course in courses:
                if code in course[0] and not any([date.day == date_be.day and date.month and date_be.month for date_be in course[7]]):
                    course[7].append(date)

for course in courses:
    for be in course[6]:
        graded.append(["BE noté", course[0], course[1], be])
    for exam in course[7]:
        graded.append(["Exam",    course[0], course[1], exam])


# Sorting
graded.sort(key=lambda x:x[3])
for e in courses:
    e[6].sort()
    e[7].sort()
if sort == sortKey.ALPHABETICAL:
    courses.sort()
elif sort == sortKey.START_DATE:
    courses.sort(key=lambda x: x[4])
elif sort == sortKey.COMPLETED:
    courses.sort(key=lambda x: -x[3]/x[2])
elif sort == sortKey.REMAINING:
    courses.sort(key=lambda x: x[3]/x[2])


# Printing
separator = "+----------------------------------------------------------------------------------------+"
text_output =[]
# 62 to .ics?
username = ""
if remote:
    username = url.split(".ics")[0][62:]
else:
    username = url[:-4]
text_output.append("\n\nTimetable report for {:s}".format(username))
text_output.append("Generated on {:%d-%m-%y}\n\n".format(datetime.now(timezone.utc)))

text_output.append(separator)
text_output.append("| {:^8s} | {:^35s} | {:^5s} | {:^5s} | {:^5s} | {:^5s} | {:^5s} |".format(
            "Code",
            "Course name",
            "Done",
            "Spent",
            "Total",
            "Begin",
            "End"
        ))

for e in courses:
    if not hide_completed or e[2] != e[3]:
        text_output.append(separator)
        text_output.append("| {:8s} | {:35s} | {:> 4d}% | {:02d}h{:02d} | {:02d}h{:02d} | {:DD-MM} | {:DD-MM} |".format(
            e[0],
            e[1][:35],
            int(100*e[3]/e[2]) if e[2] != 0 else 0,
            e[3]//60,
            e[3]%60,
            e[2]//60,
            e[2]%60,
            e[4],
            e[5]
        ))
        
        for be in e[6]:
            if not hide_past or be > datetime.now(timezone.utc):
                text_output.append("| {:8s} |      {:7s} on {:DD-MM}               |       |       |       |       |       |".format("", "BE noté", be))
        for exam in e[7]:
            text_output.append("| {:8s} |      {:7s} on {:DD-MM}               |       |       |       |       |       |".format("", "Exam", exam))
text_output.append(separator)
text_output.append("\n\n")
text_output.append("            Upcoming graded events")
separator = "+-------------------------------------------------------+"
text_output.append(separator)
for g in graded:
    if not hide_past or g[3] > datetime.now(timezone.utc):
        text_output.append("| {:7s} | {:35s} | {:DD-MM} |".format(g[0], g[2], g[3]))
text_output.append(separator)

for t in text_output:
    print(t)
#-------------------------------------------------------------------------------
with open("report.txt", 'w') as f:
    for t in text_output:
        f.write(t+"\n")

print("done")
