import re

def parseaudit(instr):
    inlist=instr.split()
    courselist=[]
    for word in inlist:
        match=re.match('[0-9][0-9]\-[0-9][0-9][0-9]',word)
        if match:
            courselist.append(match.group(0)[:2]+match.group(0)[3:6])
    return courselist
