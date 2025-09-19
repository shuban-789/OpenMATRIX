import json
import csv

# Simple script; this is just used so that code is not too messy.Parsing of the config.json happens often.
class Parser:
    def __init__(self):
        pass

    def parsejson(self, path_obj):
        with open(path_obj, "r") as f:
            fields = json.load(f)
        return fields

    def parsecsv(self, path_obj):
        reader = csv.DictReader(path_obj)
        return reader