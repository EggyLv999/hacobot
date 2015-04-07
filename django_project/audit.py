from django.shortcuts import render
from django.http import HttpResponse
import pymongo
import json
import re


    
client=pymongo.MongoClient()
db=client.db

def index(request):
    return render(request, 'audit.html', locals())


def parseaudit(request):
    major = 'Computer Science'
    requirements = db.requirements.find_one({'major' : major})
    inlist=request.POST.get("audit", "").split()
    courselist=[]
    coursedb=[]
    courses=[]
    yearnum=8
    expyear=2019
    for word in inlist:
        match=re.match('[0-9][0-9]\-[0-9][0-9][0-9]',word)
        yearmatch=re.match('CLASSLEVEL:(.+)',word)
        yearconst={'Freshman':6,'Sophomore':4,'Junior':2,'Senior':2}
        expconst={'Freshman':2018,'Sophomore':2017,'Junior':2016,'Senior':2015}
        if match:
            courselist.append(match.group(0)[:2]+match.group(0)[3:6])
        if yearmatch:
            yearnum=yearconst[yearmatch.group(1)]
            expyear=expconst[yearmatch.group(1)]

    
    coursedb.extend(courselist)    
    for key in requirements["courses"]:
        coursedb.extend(requirements["courses"][key])
    
    courses_coll = client.db.courses
    data = courses_coll.find({'number': {'$in': coursedb}})
    
    courseDict = {}
    for datum in data:
        course_id = datum['number']
        courseDict[course_id] = datum
        courseDict[course_id].pop("semesters", None)
    print courselist
    course_list = []
    courses_coll = db.courses.find()
    for item in courses_coll:
        course_list.append(item['number'])
    course_list = json.dumps(course_list)
    return render(request, 'list.html', locals())
