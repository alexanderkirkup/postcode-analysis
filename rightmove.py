import asyncio
import json
import pandas as pd
from math import sqrt
from time import time

from async_requests import AsyncRequests

class Rightmove(object):
    def __init__(self, outcodes, rateLimit=0.5):
        self.url = 'https://api.rightmove.co.uk/api/'
        self.apiApplication = 'ANDROID'
        with open('rightmove_outcodes.json', 'r') as JSON:
            self.outcodesDict = json.load(JSON)
        self.load_outcodes(outcodes)
        self.rateLimit = rateLimit

    def load_outcodes(self, outcodes):
        self.outcodes = outcodes
        self.locations = []

        for outcode in outcodes:
            try:
                self.locations.append("OUTCODE^{}".format(self.outcodesDict[outcode]))
            except:
                print('Warning: no outcode code for', outcode)

    def search_properties(self, propType:'rent' or 'sale', params:dict, limit=None, dropResults=['share', 'garage', 'retirement', 'park', 'multiple']):
        """
        Example of 'params' dict:
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
        """
        async def run(url, params):
            self.requests = AsyncRequests(rateLimit=self.rateLimit)
            await asyncio.gather(*[asyncio.ensure_future(self._fetch_location(url, params, location)) for location in self.locations[:limit]])
            await self.requests.close()

        if not self.locations:
            return print('Error: need to load Rightmove locations before fetch')

        if propType == 'rent':
            url = self.url+'rent/find'
            print('Rightmove: searching rental properties...')
        elif propType == 'sale':
            url = self.url+'sale/find'
            print('Rightmove: searching properties for sale...')
        else:
            return print('Error: incorrect propType')

        params.update({'apiApplication': self.apiApplication, 'numberOfPropertiesRequested': '50'})

        self.results = {}
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run(url, params))

        print('Rightmove: {} total properties found'.format(len(self.resultsList)))
        self._clean_results(propType=propType, toDrop=dropResults)
        return 

    async def _fetch_location(self, url, params, locationIdentifier):
        params = {**params, 'locationIdentifier': locationIdentifier}
        perPage = int(params['numberOfPropertiesRequested'])
        requestsLeft = 1
        pageNum = 0
        info = {}
        properties = []

        keepKeys = ('createDate', 'numReturnedResults', 'radius', 'searchableLocation', 'totalAvailableResults')

        while requestsLeft > 0:
            params['index'] = pageNum * perPage
            try:
                result = await self.requests.fetch_json(url, params)
                assert result['result'] == 'SUCCESS'
                if pageNum == 0:
                    info = {k: result[k] for k in keepKeys}
                    requestsLeft += (result['totalAvailableResults'] - 1) // perPage
                else:
                    info['numReturnedResults'] += len(result['properties'])
                properties.extend(result['properties'])
            except Exception:
                print('Error: RightmoveLocation for', params['locationIdentifier'])
            requestsLeft -= 1
            pageNum += 1

        locationName = info['searchableLocation']['name']
        self.results[locationName] = {'info': info, 'properties': properties}

        print("Rightmove: Finished {} ({}/{} successful)".format(locationName, info['numReturnedResults'], info['totalAvailableResults']))
        # print(info)

    def _clean_results(self, propType, toDrop=[]):
        if propType == 'rent':
            urlStart = 'https://www.rightmove.co.uk/property-to-rent/property-'
        elif propType == 'sale':
            urlStart = 'https://www.rightmove.co.uk/property-for-sale/property-'

        for location, resultDict in self.results.items():
            resultDict['properties'][:] = [prop for prop in resultDict['properties'] if not any(propType in prop['propertyType'] for propType in toDrop)]
            for prop in resultDict['properties']:
                del prop['branch']
                del prop['displayPrices']
                prop['location'] = location
                prop['url'] = "{}{}.html".format(urlStart, prop['identifier'])
        return print('Rightmove: Results cleaned')

    def estimate_postcodes(self, latlongDict):
        print('Rightmove: Estimating postcodes... (might take a while)')
        start = time()

        self._outcode_latlong_nest(latlongDict)

        for resultDict in self.results.values():
            for prop in resultDict['properties']:
                nearest, distance = self._nearest_postcode(prop['location'], prop['latitude'], prop['longitude'])
                prop['postcodeEstimate'] = nearest
                prop['postcodeSector'] = nearest[:-2]
                prop['postcodeDistance'] = distance
        return print('Rightmove: Postcodes estimated in {:.2f} secs'.format(time()-start))

    def _outcode_latlong_nest(self, latlongDict):
        self.outcodeLatlongDict = {outcode: {} for outcode in self.outcodes}
        outcodeSet = set(self.outcodes)
        for latlong, postcodes in latlongDict.items():
            for postcode in postcodes[::-1]:
                outcode = postcode.split(' ')[0]
                if outcode in outcodeSet:
                    self.outcodeLatlongDict[outcode][latlong] = postcode

    def _nearest_postcode(self, outcode, lat, lng):
        nearest = (None, float('inf'))
        for lat2,lng2 in self.outcodeLatlongDict[outcode].keys():
            distance = sqrt((lat-lat2)**2 + (lng-lng2)**2)
            if distance < nearest[1]:
                nearest = (self.outcodeLatlongDict[outcode][lat2, lng2], distance)
        return nearest

    # def _nearest_postcode_old(self, lat, lng):
    #     nearest = (None, float('inf'))
    #     for lat2,lng2 in self.latlongDict.keys():
    #         distance = sqrt((lat-lat2)**2 + (lng-lng2)**2)
    #         if distance < nearest[1]:
    #             nearest = (self.latlongDict[lat2, lng2], distance)
    #     return nearest

    def add_journey_times(self, csvPath):
        series = pd.read_csv(csvPath, index_col='postcode')['journeyTime']
        for resultDict in self.results.values():
            for prop in resultDict['properties']:
                try:
                    prop['journeyTime'] = series[prop['postcodeEstimate']]
                except:
                    print('Warning: no journey time for', prop['postcodeEstimate'])

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
        # try:
        #     return self._resultsDf
        # except:
        self._resultsDf = pd.DataFrame(self.resultsList)
        return self._resultsDf

if __name__ == "__main__":
    from postcodes import Postcodes

    p = Postcodes()
    p.load('postcodes_example.csv')

    rightmove = Rightmove(p.get_outcodes(), rateLimit=0.25)

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

    rightmove.search_properties(propType='rent', params=params, limit=50)
    rightmove.to_json('results.json')

    rightmove.load_json('results.json')
    rightmove.estimate_postcodes(p.latlongDict)

    rightmove.add_journey_times('journey_times.csv')

    print(rightmove.resultsDf)
