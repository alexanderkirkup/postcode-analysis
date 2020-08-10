import asyncio
import json
from postcodes import Postcodes
from async_requests import AsyncRequests

class Rightmove(object):
    def __init__(self):
        self.postcodes = Postcodes()
        self.url = 'https://api.rightmove.co.uk/api/'
        self.apiApplication = 'ANDROID'

        with open('rightmove_outcodes.json', 'r') as JSON:
            self.outcodesDict = json.load(JSON)

    def load_postcodes(self, csvPath):
        self.postcodes.load(csvPath)
        self.locations = []
        for outcode in self.postcodes.get_outcodes():
            try:
                self.locations.append("OUTCODE^{}".format(self.outcodesDict[outcode]))
            except:
                print('Warning: no outcode code for', outcode)

    def _fetchGenerator(self, limit:int, path:str, params=None):
        if not params:
            params = {
                    'numberOfPropertiesRequested': '1',
                    'minBedrooms': '1',
                    'maxBedrooms': '1',
                    'radius': '0',
                    'sortType': '1',
                    'propertyTypes': 'bungalow,detached,flat,park-home,semi-detached,terraced',
                    #'mustHave': '',
                    'dontShow': 'houseShare,retirement',
                    #'furnishTypes': '',
                    #'keywords': '',
                    }
        params['apiApplication'] = self.apiApplication
        for location in self.locations[:limit]:
            params['locationIdentifier'] = location
            yield {'urlPath': path, 'params': params}

    def get_rents(self, limit, params=None):
        toFetch = self._fetchGenerator(limit=limit, path='rent/find', params=params)
        self.requests = AsyncRequests(url=self.url, fetchList=toFetch, rateLimit=1)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.requests.run())
        self.results = self.requests.resultsList

if __name__ == "__main__":
    rightmove = Rightmove()
    rightmove.load_postcodes('postcodes_example.csv')
    rightmove.get_rents(10)
    print(rightmove.results)
    print(len(rightmove.results))