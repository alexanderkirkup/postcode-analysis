import asyncio

import pandas as pd

from async_requests import AsyncRequests


class TfL(object):
    def __init__(self, app_id, app_key, rateLimit=0.1):
        self.url = 'https://api.tfl.gov.uk/'

        self.app_id = app_id
        self.app_key = app_key
        self.rateLimit = rateLimit

    def load_postcodes(self, postcodeDict):
        self.postcodeDict = postcodeDict

    def request_journeys(self, endLocation, limit=None):
        params = {
            'date': '20200901',
            'time': '0800',
            'walkingSpeed': 'Fast',
            'cyclePreference': 'None',
            'alternativeCycle': 'false',
            'alternativeWalking': 'true',
        }
        params.update({'app_id': self.app_id, 'app_key': self.app_key})

        self.results = {}

        async def run(endLocation, params):
            self.requests = AsyncRequests(rateLimit=self.rateLimit)
            await asyncio.gather(*[asyncio.ensure_future(self._fetch_journey(postcode, endLocation, params)) for postcode in list(self.postcodeDict.keys())[:limit]])
            await self.requests.close()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(run(endLocation, params))

    async def _fetch_journey(self, startPostcode, endLocation, params):
        url = f"{self.url}Journey/JourneyResults/{startPostcode}/to/{endLocation}"
        try:
            result, status = await self.requests.fetch(url, params)
            if status == 200:
                self.results[startPostcode] = result
                return print('Journey Planner: Fetched', startPostcode)
            elif status == 300:
                startLatLong = self.postcodeDict[startPostcode]
                url = "{}Journey/JourneyResults/{},{}/to/{}".format(
                    self.url, *startLatLong, endLocation)
                result, status = await self.requests.fetch(url, params)
                self.results[startPostcode] = result
                return print('Journey Planner: Fetched', startPostcode, startLatLong)
            else:
                print('Error: _fetch_journey', startPostcode)
        except Exception as e:
            print(
                f"Error: _fetch_journey {startPostcode} {type(e).__name__} {e.args}")

    def to_json(self, path, type: dict or list = dict):
        with open(path, 'w') as f:
            if type == dict:
                json.dump(self.results, f, sort_keys=True)
            elif type == list:
                json.dump(self.resultsList, f, sort_keys=True)
            else:
                print('Error: to_json only works with type dict or list')

    def load_json(self, path):
        with open(path, 'r') as JSON:
            self.results = json.load(JSON)

    def get_df(self, resultsType: 'results' or 'journeys'):
        if resultsType == 'results':
            return pd.DataFrame(self.resultsList)
        elif resultsType == 'journeys':
            return pd.DataFrame(self.journeysList)
        else:
            print('Error: get_df resultsType incorrect')

    @property
    def resultsList(self):
        return [
        {
        'postcode': postcode, 
        'from': result['journeyVector']['from'], 
        'to': result['journeyVector']['to'], 
        'dateTime': result['searchCriteria']['dateTime'],
        'dateTimeType': result['searchCriteria']['dateTimeType'], 
        'shortestDuration': min([journey['duration'] for journey in result['journeys']])
        } 
        for postcode, result in self.results.items()]
    
    @property
    def journeysList(self):
        return [
        {
        'postcode': postcode, 
        'from': result['journeyVector']['from'], 
        'to': result['journeyVector']['to'], 
        'dateTime': result['searchCriteria']['dateTime'], 
        'dateTimeType': result['searchCriteria']['dateTimeType'],
        'journeyIdx': result['journeys'].index(journey),
        'duration': journey['duration'], 
        'legs': [{'mode': leg['mode']['name'], 'duration': leg['duration']} for leg in journey['legs']]
        } 
        for postcode, result in self.results.items() for journey in result['journeys']]


if __name__ == "__main__":
    import json
    with open('tfl_keys.json', 'r') as JSON:
        tflKeys = json.load(JSON)

    from postcodes import Postcodes
    p = Postcodes()
    p.load('postcodes_example.csv')

    tfl = TfL(
        app_id=tflKeys['app_id'], app_key=tflKeys['app_key'], rateLimit=0.2)

    # tfl.load_postcodes(p.postcodeDict)
    # tfl.request_journeys(endLocation='1000235', limit=100)
    # tfl.to_json('tfl_results.json')

    tfl.load_json('tfl_results.json')

    print(tfl.get_df(resultsType='journeys'))

    # from pprint import pprint
    # pprint(tfl.resultsList[:5])
    # pprint(tfl.journeysList[:5])
    # pprint(tfl.results['SW10 0JG']['journeyVector'])
    # pprint(tfl.results['SW10 0JG']['recommendedMaxAgeMinutes'])
    # pprint(tfl.results['SW10 0JG']['searchCriteria'])
    # pprint(tfl.results['SW10 0JG']['stopMessages'])
    # pprint(tfl.results['SW10 0JG']['journeys'][0].keys())
