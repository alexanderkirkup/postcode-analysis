import json
import pandas as pd
import pprint

class RightmoveResults(object):
    def __init__(self, jsonPath, clean=True):
        with open(jsonPath, 'r') as JSON:
            self.raw = json.load(JSON)

    def clean(self, toDrop=[]):
        for location, resultDict in self.raw.items():
            resultDict['properties'][:] = [prop for prop in resultDict['properties'] if not any(propType in prop['propertyType'] for propType in toDrop)]
            for prop in resultDict['properties']:
                del prop['branch']
                del prop['displayPrices']
                prop['location'] = location

    def to_df(self):
        return pd.DataFrame(self.propertyList)

    @property
    def propertyList(self):
        return [prop for resultDict in self.raw.values() for prop in resultDict['properties']]

if __name__ == "__main__":
    results = RightmoveResults('results.json')
    results.clean(toDrop=['share', 'garage', 'retirement', 'park', 'multiple'])
    
    print(results.to_df())

    print(len(results.propertyList))
    # pprint.pprint(results.propertyList[:20])