import json
import csv

# Simple script; this is just used so that code is not too messy.Parsing of the config.json happens often.
class Parser:
    def __init__(self):
        pass

    def parsejson(self, path_obj):
        fields = json.load(path_obj)
        path_obj.close()
        return fields

    def parsecsv(self, path_obj):
        reader = csv.DictReader(path_obj)
        return reader