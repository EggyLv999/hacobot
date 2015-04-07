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
    for word in inlist:
        match=re.match('[0-9][0-9]\-[0-9][0-9][0-9]',word)
        if match:
            courselist.append(match.group(0)[:2]+match.group(0)[3:6])
    
    coursedb.extend(courselist)    
    for key in requirements["courses"]:
        coursedb.extend(requirements["courses"][key])
    
    courses_coll = client.db.courses
    data = courses_coll.find({'number': {'$in': coursedb}})
    
    courseDict = {}
    for datum in data:
        course_id = datum['number']
        courseDict[course_id] = ()
    
    return render(request, 'list.html', locals())
