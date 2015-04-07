from django.shortcuts import render
from django.http import HttpResponse
import re
import random
import math
import scipy
import pymongo
import json
from datetime import datetime, timedelta

def get_course_data(courses, semesters):
    client = pymongo.MongoClient()
    courses_coll = client.db.courses
    data = courses_coll.find({'number': {'$in': courses}})
    ret = {}
    for datum in data:
        course_id = datum['number']
        ret[course_id] = datum
        for sem in semesters:
            if sem[0]=='F':
                preference = ['F14', 'F13', 'S14', 'S13']
            else:
                preference = ['S14', 'S13', 'F14', 'F13']
            pref = None
            for p in preference:
                if (p in datum['semesters']) and datum['semesters'][p]:
                    if pref is None or pref[0] != sem[0]:
                        pref = p
            lectures = datum['semesters'][pref]
            sem_timings = {}
            sections = {}
            lecture_id = -1
            for lecture in lectures:
                lecture_id += 1
                # Add lecture timing if no recitations
                if 'recitations' not in lecture:
                    timings = []
                    if not lecture['meetings']:
                        timings.append((lecture['time_start'], lecture['time_end'], lecture['days']))
                    else:
                        for meeting in lecture['meetings']:
                            timings.append((meeting['time_start'], meeting['time_end'], meeting['days']))
                    sem_timings[lecture['section']] = timings
                    sections[lecture['section']] = {'lecture': lecture_id, 'past_semester': pref}
                    continue
                for rec in lecture['recitations']:
                    timings = []
                    if not rec['meetings']:
                        timings.append((rec['time_start'], rec['time_end'], rec['days']))
                    else:
                        for meeting in rec['meetings']:
                            timings.append((meeting['time_start'], meeting['time_end'], meeting['days']))
                    if not lecture['meetings']:
                        timings.append((lecture['time_start'], lecture['time_end'], lecture['days']))
                    else:
                        for meeting in lecture['meetings']:
                            timings.append((meeting['time_start'], meeting['time_end'], meeting['days']))
                    sem_timings[rec['section']] = timings
                    sections[rec['section']] = {'lecture': lecture_id, 'past_semester': pref}            
            ret[course_id][sem] = {'sections': sections, 'timings': sem_timings}
    return ret

class BetterScoreException(Exception):
    pass

def convertname(sem):
    if sem[0]=='F':
        return 'Fall 20'+sem[1:]
    return 'Spring 20'+sem[1:]
    
def make_schedule(taken, courses, semesters):
    best_score = -1e100
    best_schedule = None
    course_data = get_course_data(courses, semesters)
    sem_courses = {}
    possible_sems = {}
    sem_to_index = {}
    for i in xrange(len(semesters)):
        sem_to_index[semesters[i]] = i
    for course in courses:
        possible_sems[course] = []
        for sem in semesters:
            if sem in course_data[course]:
                possible_sems[course].append(sem)
        if not possible_sems[course]:
            return None # This course doesn't have a valid semester!
    courses_per_sem = (len(courses) / len(semesters))
    extras = len(semesters) - (len(courses) % len(semesters))
    for iter in xrange(1):
        # Sort courses by last 3 digits
        courses = sorted(courses, key=lambda x: x[2:])
        schedule = []
        for sem in semesters:
            schedule.append({'semester': sem, 'courses': []})
        cid = 0
        semid = 0
        for course in courses:
            timings = course_data[course][semesters[semid]]['timings']
            section = random.choice(timings.keys())
            schedule[semid]['courses'].append({'course': course, 'section': section})
            cid += 1
            if cid == courses_per_sem:
                cid = 0
                semid += 1
                if semid == extras:
                    courses_per_sem += 1
        # for course in courses:
            # sem = random.choice(possible_sems[course])
            # timings = course_data[course][sem]['timings']
            # section = random.choice(timings.keys())
            # schedule[sem_to_index[sem]]['courses'].append({'course': course, 'section': section})
        delta_list = [500000, 90000, 9000, 0.1]
        delta = 0
        while delta < len(delta_list):
            # Try making schedule better
            # First, by swapping semesters for some course
            prev_score, marked_courses = eval_schedule(taken, schedule, course_data)
            if delta == 0:
                marked_courses = []
            try:
                # Pick random semester and course
                for sem in schedule:
                    for course in sem['courses']:
                        sem['courses'].remove(course)
                        prev_section = course['section']
                        for new_sem_name in semesters:
                            if new_sem_name == sem['semester']:
                                continue
                            new_sem = sem_to_index[new_sem_name]
                            sections = course_data[course['course']][new_sem_name]['sections']
                            course['section'] = random.choice(sections.keys())
                            schedule[new_sem]['courses'].append(course)
                            score, _ = eval_schedule(taken, schedule, course_data)
                            if score >= prev_score + delta_list[delta]:
                                prev_score = score
                                raise BetterScoreException
                            schedule[new_sem]['courses'].pop()
                        course['section'] = prev_section
                        sem['courses'].append(course)
                # Second, by swapping sections
                # Swapping sections will not help for fulfilling prerequisites
                if delta > 0:
                    for sem in schedule:
                        for course in sem['courses']:
                            prev_section = course['section']
                            sections = course_data[course['course']][sem['semester']]['sections']
                            for section in sections:
                                if section == prev_section:
                                    continue
                                course['section'] = section
                                score, _ = eval_schedule(taken, schedule, course_data)
                                if score >= prev_score + delta_list[delta]:
                                    prev_score = score
                                    raise BetterScoreException
                            course['section'] = prev_section
            except BetterScoreException:
                if score > best_score:
                    best_score = score
                    best_schedule = schedule
                continue
            delta += 1
    for sem in best_schedule:
        sem['semname']=convertname(sem['semester'])
    return (course_data, best_schedule, best_score)


def entropy(l):
    ent=0
    sl=sum(l)
    for i in l:
        if i == 0:
            continue
        ent+=(i*1.0/sl)*math.log(sl/i,2)
    return ent

def parsetime(daychar,timestring):
    if timestring=='TBA':
        return 0
    final=0
    const_day={u'M':0,u'T':2400,u'W':4800,u'R':7200,u'F':9600,u'S':12000,u'U':14400}
    if timestring[5]=='P':
        final+=1200
    final+=const_day[daychar]
    hour=int(timestring[:2])
    if hour!=12:
        final+=hour*60
    final+=int(timestring[3:5])
    return final

def uniquify(seq):
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if not (x in seen or seen_add(x))]

def eval_schedule(taken, schedule, course_data):
    courses_taken = {}
    for course in taken:
        courses_taken[course] = True
    const_time=4.0
    const_fce=2.0
    const_dept=3.0
    score = 0.0
    ltime=[]
    fce_score = []
    for sem in schedule:
        time=[]
        dept=[0]*100
        cnt=0
        ctimes=[]
        cnames=[]
        total_units = 0
        marked=[]
        unfree_days = {}
        for course in sem['courses']:
            #check prereqs
            cdata = course_data[course['course']]
            total_units += cdata['units']
            prereqs = cdata.get('prerequisites', '')
            prereqs = re.sub(r'([0-9]+)', r'("\1" in courses_taken)', prereqs)
            if prereqs and not eval(prereqs):
                score-=1000000
            #todo: check course conflicts
            ctimes.append([])
            cnames.append(course['course'])
            for timing in cdata[sem['semester']]['timings'][course['section']]:
                for day in timing[2]:
                    ctimes[cnt].append((parsetime(day,timing[0]),parsetime(day,timing[1])))
                    unfree_days[day] = True
            cnt += 1
            #time balance
            time.append(cdata.get('avg_hrs', 9))
            #fce score
            section=cdata[sem['semester']]['sections'][course['section']]
            if ('fce' in cdata['semesters'][section['past_semester']][section['lecture']]) and ('Overall course' in cdata['semesters'][section['past_semester']][section['lecture']]['fce']):
                fce_score.append(cdata['semesters'][section['past_semester']][section['lecture']]['fce']['Overall course'])
            else:
                fce_score.append(4.25)
            #department balance
            dept[int((course['course'])[:2])]+=1
        for i in xrange(cnt):
            for j in xrange(i + 1,cnt):
                for t1 in ctimes[i]:
                    bf=False
                    for t2 in ctimes[j]:
                        if not (t1[1]<t2[0] or t1[0]>t2[1]):
                            score-=10000
                            marked.append(cnames[i])
                            marked.append(cnames[j])
                            bf=True
                            break
                    if bf:
                        break
        ltime.append(sum(time))
        score+=const_dept*entropy(dept)
        for course in sem['courses']:
            courses_taken[course['course']] = True
        if total_units > 54:
            score -= 100000
        # # Start later than 1000 if possible
        # for i in xrange(cnt):
        #     for t in ctimes[i]:
        #         if t[0] % 2400 < 1000:
        #             score -= 1000 - (t[0] % 2400)
        # # Try for as many free days as possible
        # for day in ['M', 'T', 'W', 'R', 'F']:
        #     if day not in unfree_days:
        #         score += 10000
        #         break
        
    score+=const_fce*scipy.mean(fce_score)
    score-=const_time*scipy.std(ltime)
    return (score,uniquify(marked))

def gensemesters(begin,end): #inclusive
    semlist=[]
    while(True):
        semlist.append(begin)
        if begin==end:
            return semlist
        if begin[0]=='F':
            begin='S'+str(int(begin[1:])+1)
        else:
            begin='F'+begin[1:]

def index(request):
    print(request.POST)
    post_data = request.POST
    if post_data:
        semesters = gensemesters(post_data['startSem'], post_data['endSem'])
        courses = json.loads(post_data['courses'])
        taken = json.loads(post_data['taken'])
    else:
        taken = []
        courses = ['21122', '21120', '21259', '15112', '15122', '15150', '15251', '15451', '15210', '15213', '15411', '15410', '15354', '15128', '15221', '15381', '15312', '21127', '21241', '76101', '21325']
        semesters = ['F14', 'S15', 'F15', 'S16', 'F16', 'S17', 'F17', 'S18']
    #semesters = ['F14', 'S15', 'F15', 'S16', 'F16', 'S17', 'F17', 'S18']
    course_data, schedule, score = make_schedule(taken, courses, semesters)
    #course_data, schedule, score = make_schedule(taken, courses, semesters[:yearnum])
    for sem in schedule:
        semester = sem['semester']
        tooltip_data={}
        for course in sem['courses']:
            course_id = course['course']
            section = course['section']
            section_data = course_data[course_id][semester]['sections'][section]
            old_sem = section_data['past_semester']
            old_lecture = section_data['lecture']
            course['instructor'] = course_data[course_id]['semesters'][old_sem][old_lecture]['instructors']
            course['timings'] = course_data[course_id][semester]['timings'][section]
            jstimings = []
            dayid = {u'M': 0, u'T': 1, u'W': 2, u'R': 3, u'F': 4, u'S': 5, u'U': 6}
            course['timingstr']=''
            for start_time, end_time, days in course['timings']:
                for day in days:
                    new_start_time = str(datetime.strptime(start_time, '%I:%M%p') + timedelta(days=dayid[day]))
                    new_end_time = str(datetime.strptime(end_time, '%I:%M%p') + timedelta(days=dayid[day]))
                    jstimings.append([new_start_time, new_end_time])
                course['timingstr']=course['timingstr']+days+': '+start_time+'-'+end_time+', '
            course['jstimings'] = jstimings
            course['timingstr']=course['timingstr'][:-2]
            print course['timingstr']
    return render(request, 'index.html', locals())
