import pymongo
import json
client=pymongo.MongoClient()
db=client.db
coll=db.courses
with open("dump5.json") as json_file:
    dump = json.load(json_file)
    db.courses.remove({})
    coll.insert(dump.values())
