import asyncio
import json
import pandas as pd
from math import sqrt
from time import time

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
        self.latlongDict = self.postcodes.latlongDict

    def get_rents(self, limit=None, params=None):
        async def run(params):
            for location in self.locations[:limit]:
                await self._fetch_location('rent/find', params, location)
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

    async def _fetch_location(self, urlPath, params, locationIdentifier):
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

    def clean_results(self, toDrop=[]):
        for location, resultDict in self.results.items():
            resultDict['properties'][:] = [prop for prop in resultDict['properties'] if not any(propType in prop['propertyType'] for propType in toDrop)]
            for prop in resultDict['properties']:
                del prop['branch']
                del prop['displayPrices']
                prop['location'] = location
                # prop['propertyType'] = prop['propertyType'].lower()
        return print('Rightmove: cleaned results')

    def _nearest_postcode(self, lat, lng):
        nearest = (None, float('inf'))
        for lat2,lng2 in self.latlongDict.keys():
            distance = sqrt((lat-lat2)**2 + (lng-lng2)**2)
            if distance < nearest[1]:
                nearest = (self.latlongDict[lat2, lng2], distance)
        return nearest

    def estimate_postcodes(self):
        print('Rightmove: Estimating postcodes (will take a while...)')
        start = time()
        for resultDict in self.results.values():
            for prop in resultDict['properties']:
                nearestList, distance = self._nearest_postcode(prop['latitude'], prop['longitude'])
                prop['postcodeEstimate'] = nearestList
                prop['postcodeSectorEstimate'] = nearestList[0][:-2]
                prop['postcodesCount'] = len(nearestList)
                prop['postcodeDistance'] = distance
        return print('Rightmove: Postcodes estimated in {:.2f} secs'.format(time()-start))

    def to_json(self, path, type:dict or list = dict):
        with open(path, 'w') as f:
            if type==dict:
                json.dump(self.results, f, sort_keys=True)
            elif type==list:
                json.dump(self.resultsList, f, sort_keys=True)
            else:
                print('Error: to_json only works with type dict or list')

    def load_json(self, path):
        with open(path, 'r') as JSON:
            self.results = json.load(JSON)

    @property
    def resultsList(self):
        return [prop for resultDict in self.results.values() for prop in resultDict['properties']]

    @property
    def resultsDf(self):
        try:
            return self._resultsDf
        except:
            self._resultsDf = pd.DataFrame(self.resultsList)
            return self._resultsDf

if __name__ == "__main__":
    params = {
            'minBedrooms': '1',
            'maxBedrooms': '1',
            'radius': '0',
            'sortType': '1',
            'propertyTypes': 'flat',
            #'mustHave': '',
            'dontShow': 'houseShare,retirement',
            #'furnishTypes': '',
            #'keywords': '',
            }

    rightmove = Rightmove(rateLimit=0.5)
    rightmove.load_postcodes('postcodes_example.csv')
    rightmove.get_rents(limit=1, params=params)

    rightmove.clean_results(toDrop=['share', 'garage', 'retirement', 'park', 'multiple'])
    rightmove.estimate_postcodes()
    print(rightmove.resultsDf)

    # rightmove.to_json('results.json')