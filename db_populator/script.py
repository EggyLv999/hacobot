import urllib2
import json
from pyquery import PyQuery as pq
from lxml import etree
import urllib
import csv
import xml.etree.ElementTree as ET
import re
import os
depts = [{"id":31,"name":"Aerospace Studies-ROTC"},{"id":48,"name":"Architecture"},{"id":60,"name":"Art"},{"id":3,"name":"Biological Sciences"},{"id":42,"name":"Biomedical Engineering"},{"id":70,"name":"Business Administration"},{"id":62,"name":"CFA Interdisciplinary"},{"id":39,"name":"CIT Interdisciplinary"},{"id":99,"name":"Carnegie Mellon University-Wide Studies"},{"id":64,"name":"Center for the Arts in Society"},{"id":86,"name":"Center for the Neural Basis of Cognition"},{"id":6,"name":"Chemical Engineering"},{"id":9,"name":"Chemistry"},{"id":12,"name":"Civil & Environmental Engineering"},{"id":2,"name":"Computational Biology"},{"id":15,"name":"Computer Science"},{"id":93,"name":"Creative Enterprise:Sch of Pub Pol & Mgt"},{"id":51,"name":"Design"},{"id":54,"name":"Drama"},{"id":73,"name":"Economics"},{"id":18,"name":"Electrical & Computer Engineering"},{"id":19,"name":"Engineering & Public Policy"},{"id":76,"name":"English"},{"id":53,"name":"Entertainment Technology Pittsburgh"},{"id":94,"name":"Heinz College Wide Courses"},{"id":79,"name":"History"},{"id":5,"name":"Human-Computer Interaction"},{"id":4,"name":"Information & Communication Technology"},{"id":14,"name":"Information Networking Institute"},{"id":95,"name":"Information Systems:Sch of IS & Mgt"},{"id":8,"name":"Institute for Software Research"},{"id":11,"name":"Language Technologies Institute"},{"id":38,"name":"MCS Interdisciplinary"},{"id":10,"name":"Machine Learning"},{"id":27,"name":"Materials Science & Engineering"},{"id":21,"name":"Mathematical Sciences"},{"id":24,"name":"Mechanical Engineering"},{"id":92,"name":"Medical Management:Sch of Pub Pol & Mgt"},{"id":30,"name":"Military Science-ROTC"},{"id":82,"name":"Modern Languages"},{"id":57,"name":"Music"},{"id":32,"name":"Naval Science - ROTC"},{"id":80,"name":"Philosophy"},{"id":69,"name":"Physical Education"},{"id":33,"name":"Physics"},{"id":85,"name":"Psychology"},{"id":91,"name":"Public Management:Sch of Pub Pol & Mgt"},{"id":90,"name":"Public Policy & Mgt:Sch of Pub Pol & Mgt"},{"id":16,"name":"Robotics"},{"id":96,"name":"Silicon Valley"},{"id":88,"name":"Social & Decision Sciences"},{"id":17,"name":"Software Engineering"},{"id":36,"name":"Statistics"},{"id":98,"name":"StuCo (Student Led Courses)"},{"id":45,"name":"Tepper School of Business"},{"id":66,"name":"Dietrich College Interdisciplinary"},{"id":52,"name":"BXA Intercollege Degree Programs"},{"id":67,"name":"Dietrich College Information Systems"},{"id":65,"name":"General Dietrich College"},{"id":47,"name":"Tepper School of Business"}]
def pr(data):
    print json.dumps(data, sort_keys=True, indent=2, separators=(',', ': '))

def loadFCEs(fces, url):
    tree = ET.parse(url)
    root = tree.getroot()
    for Table in root.findall('Table1'):
        fce = {}
        for course in Table:
            attr = re.sub('_x\d+A?_', '', course.tag.replace("_x0020_", " "))
            attr = re.sub('\d+', '', attr).strip()
            fce[attr] = course.text.replace("&nbsp;","")
        if not re.match('\d+',fce["Course ID"]): continue
        if fce["Course ID"] not in fces:
            fces[fce["Course ID"]] = []
        fces[fce["Course ID"]].append(fce)

def queryDetails(course,sem,db):
    d = pq(url="https://enr-apps.as.cmu.edu/open/SOC/SOCServlet/courseDetails?COURSE="+
           course+"&SEMESTER="+ sem)
    if d("dt:contains('Prerequisites')").next().text().strip() != "":
        db[course]["prerequisites"] = d("dt:contains('Prerequisites')").next().text().strip()
        if db[course]["prerequisites"] == "None": db[course]["prerequisites"] = ""
        db[course]["corequisites"] = d("dt:contains('Corequisites')").next().text().strip()
        if db[course]["corequisites"] == "None": db[course]["corequisites"] = ""
        db[course]["description"] = d("h4:contains('Description:')").next().text().strip()
        
def loadDB(sem, db, dept):
    response = urllib2.urlopen('https://apis.scottylabs.org/v1/schedule/'+sem+'/departments/'+str(dept)+'/courses?app_id=561374f4-f2b8-4a34-bb42-37a8b1ea4a2c&app_secret_key=d5XI0TzZdoBEVRIHOki9rg6TlGZREr6aiwUnT7yw5R8ozb4tW0_sME-g&limit=100')
    data = json.load(response)
    
    courses = data["courses"]
    
    
    for course in courses:
        if course["number"] not in db:
            db[course["number"]] = course
            db[course["number"]]["description"] = ""  
            db[course["number"]]["semesters"] = {}
            db[course["number"]]["semesters"][sem] = course["lectures"]
            db[course["number"]].pop("lectures", None)
        else:
            db[course["number"]]["semesters"][sem] = course["lectures"]
    
    for course in db:
        if db[course]["description"] == "":
            queryDetails(course,"F14",db)
            queryDetails(course,"S14",db)
            queryDetails(course,"S15",db)

db = {}
for dept in depts:
    loadDB("F13", db, dept["id"])
    loadDB("F14", db, dept["id"])
    loadDB("S14", db, dept["id"])

fces = {}
#loadFCEs(fces, "SurveyResults-SchoolComputerScience-2014-Fall.xml")
#loadFCEs(fces, "SurveyResults-SchoolComputerScience-2014-Spring.xml")
#loadFCEs(fces, "SurveyResults-SchoolComputerScience-2014-Summer.xml")
#loadFCEs(fces, "SurveyResults-SchoolComputerScience-2013.xml")
files = [f for f in os.listdir('.') if os.path.isfile(f)]

for f in files:
    if 'xml' in f:
        loadFCEs(fces, f)
fcedb = {}

for course in fces:
    if course not in db:
        continue
    if course not in fcedb:
        fcedb[course] = {}
    hrs = 0.0
    hrs_cnt = 0.0
    overall = 0.0
    overall_cnt = 0.0
    for item in fces[course]:
        if "Course ID" not in item or "Instructor" not in item or "Year" not in item or "Semester" not in item:
            continue
        
        sem = ""
        if item["Semester"] == "Spring": sem = "S"
        elif item["Semester"] == "Summer": sem = "M"
        else: sem = "F"
        sem += item["Year"][-2:]
        
        if sem not in fcedb[course]: 
            fcedb[course][sem] = []
        
        fcedb[course][sem].append(item)

        if "Hrs Per Week" in item:
            if re.match('\d+.?\d*',item["Hrs Per Week"]):
                hrs += float(item["Hrs Per Week"])
                hrs_cnt += 1
        if "Overall course" in item:
            if re.match('\d+.?\d*',item["Overall course"]):
                overall += float(item["Overall course"])
                overall_cnt += 1
    if overall_cnt > 0:
        db[course]["avg_overall_rating"] = overall / overall_cnt
    if hrs_cnt > 0:
        db[course]["avg_hrs"] = hrs / hrs_cnt

fceAttrs = ["Clear learning goals", "Enrollment", "Explain course requirements", "Explains subject matter", "Feedback to students", "Importance of subject", "Interest in student learning", "Overall course", "Overall teaching", "Show respect for students", "Hrs Per Week"]
for course in db:
    for sem in db[course]["semesters"]:
        for courseItem in db[course]["semesters"][sem]:
            if "location" not in courseItem: continue
            if re.match(r'CMB',courseItem["location"]) or courseItem["instructors"] == "Doha, Qatar":
                db[course]["semesters"][sem].remove(courseItem)
                continue
            l = []
            fce = {}
            fceSum = {}
            fceCnt = {}
            for attr in fceAttrs: fceSum[attr] = fceCnt[attr] = 0.0
            for instructor in [re.sub(r'\W+', '', x.strip()) for x in courseItem["instructors"].split(',') ]:
                if course not in fcedb or sem not in fcedb[course]:
                    continue
                for fceItem in fcedb[course][sem]:
                    if instructor.lower() in fceItem["Instructor"].lower():
                        l.append(fceItem)
                        break
            for attr in fceAttrs:
                for item in l:
                    if attr in item:
                        if re.match('\d+.?\d*',item[attr]):
                            fceSum[attr] += float(item[attr])
                            fceCnt[attr] += 1
                if fceCnt[attr] > 0:
                    fce[attr] = fceSum[attr] / fceCnt[attr]
            courseItem["fce"] = fce

for course in db:
    for sem in db[course]["semesters"]:
        for courseItem in db[course]["semesters"][sem]:
            if re.match(r'CMB',courseItem["location"]) or courseItem["instructors"] == "Doha, Qatar":
                db[course]["semesters"][sem].remove(courseItem)
pr(db)
                
            

                
            
