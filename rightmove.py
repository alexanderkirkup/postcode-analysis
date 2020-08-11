import asyncio
import json
from postcodes import Postcodes
from async_requests import AsyncRequests

class Rightmove(object):
    def __init__(self, rateLimit=0.5):
        self.postcodes = Postcodes()
        self.rateLimit = rateLimit
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

    def get_rents(self, limit=None, params=None):
        async def run(params):
            for location in self.locations[:limit]:
                await self.fetch_location('rent/find', params, location)
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

    async def fetch_location(self, urlPath, params, locationIdentifier):
        params = {**params, 'locationIdentifier': locationIdentifier}
        perPage = int(params['numberOfPropertiesRequested'])
        requestsLeft = 1
        pageNum = 0
        info = {}
        properties = []

        keepKeys = ('createDate', 'numReturnedResults', 'radius', 'searchableLocation', 'totalAvailableResults')

        while requestsLeft > 0:
            params['index'] = pageNum * perPage
            result = await self.requests.fetch(urlPath, params)
            if result['result'] == 'SUCCESS':
                if pageNum == 0:
                    info = {k: result[k] for k in keepKeys}
                    requestsLeft += (result['totalAvailableResults'] - 1) // perPage
                else:
                    info['numReturnedResults'] += len(result['properties'])
                properties.extend(result['properties'])
            else:
                print('Error: RightmoveLocation', params['locationIdentifier'])
            requestsLeft -= 1
            pageNum += 1
            await asyncio.sleep(self.rateLimit)

        locationName = info['searchableLocation']['name']
        self.results[locationName] = {'info': info, 'properties': properties}
        print('Finished', locationName)
        print(info)

if __name__ == "__main__":
    rightmove = Rightmove()
    rightmove.load_postcodes('postcodes_example.csv')
    rightmove.get_rents()

    # print(rightmove.results)
    print('Number of fetched locations:', len(rightmove.results))

    import json
    with open('results.json', 'w') as f:
        json.dump(rightmove.results, f, sort_keys=True)