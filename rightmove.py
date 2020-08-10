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

    def get_rents(self, limit, rateLimit=1, params=None):
        async def run(params):
            for location in self.locations[:limit]:
                rl = RightmoveLocation(self.requests, rateLimit, 'rent/find', params, location)
                await rl.main()
                self.results[location] = rl
                # asyncio.ensure_future(rl.main())
                await asyncio.sleep(rateLimit)
            await self.requests.close()
        
        if not params:
            params = {
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
        params.update({'apiApplication': self.apiApplication, 'numberOfPropertiesRequested': '50'})

        self.results = {}
        self.requests = AsyncRequests(url=self.url)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run(params))


class RightmoveLocation(object):
    def __init__(self, asyncRequests, rateLimit, urlPath, params, locationIdentifier):
        self.requests = asyncRequests
        self.rateLimit = rateLimit
        self.urlPath = urlPath
        self.params = {**params, 'locationIdentifier': locationIdentifier}
        self.result = {}  # temp result receiver dict for each request
        self.info = {}
        self.properties = []
        self.requestsLeft = 0

    async def initial_fetch(self):
        await self.requests.fetch(self, self.urlPath, self.params)
        if self.result['result'] == 'SUCCESS':
            keepKeys = ('createDate', 'numReturnedResults', 'radius', 'searchableLocation', 'totalAvailableResults')
            self.info = {k: self.result[k] for k in keepKeys}
            self.properties.extend(self.result['properties'])
            perPage = int(self.params['numberOfPropertiesRequested'])
            self.requestsLeft = (self.result['totalAvailableResults'] - 1) // perPage
            # print('requestsLeft:', self.requestsLeft)
        else:
            print('Error: RightmoveLocation', self.params['locationIdentifier'])

    async def main(self):
        await self.initial_fetch()
        for request in range(1, self.requestsLeft+1):
            self.params['index'] = request*int(self.params['numberOfPropertiesRequested'])
            await asyncio.sleep(self.rateLimit)
            await self.requests.fetch(self, self.urlPath, self.params)
            self.properties.extend(self.result['properties'])

if __name__ == "__main__":
    rightmove = Rightmove()
    rightmove.load_postcodes('postcodes_example.csv')
    rightmove.get_rents(1, 0)

    print(rightmove.results)
    print(len(rightmove.results))

    import pprint

    for rl in rightmove.results.values():
        print(rl.info)
        print(len(set(str(prop) for prop in rl.properties)))
        print(len(rl.properties))
        pprint.pprint(rl.properties[50:52])