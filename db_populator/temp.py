import pymongo
import json
client=pymongo.MongoClient()
db=client.db
coll=db.requirements
with open("cs_req.json") as json_file:
    dump = json.load(json_file)
    coll.insert(dump)

print coll.find_one()