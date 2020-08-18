from rightmove import Rightmove
from postcodes import Postcodes

p = Postcodes()
p.load('postcodes_example.csv')

rightmove = Rightmove(p.get_outcodes(), rateLimit=0.2)

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

rightmove.search_properties(propType='rent', params=params, limit=2)
# rightmove.to_json('results.json')

# rightmove.load_json('results.json')
# rightmove.estimate_postcodes(p.latlongDict)

# rightmove.add_journey_times('journey_times.csv')

# print(rightmove.resultsList[:10])