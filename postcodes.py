import pandas as pd

class Postcodes(object):
    def __init__(self):
        self.postcodeDict = {}
        self.latlongDict = {}
        self.outcodes = []

    def load(self, csvPath: str, drop_exp=True, outcodes_to_drop=['CR90', 'N1P', 'N81', 'NW1W', 'NW26', 'SE1P'], dicts=True):
        '''
        Loads local csv of postcodes to a pandas DataFrame and (by default) cleans and extracts the important bits to object attributes.

        Latest csv postcode dataset for London can be found at: https://data.london.gov.uk/dataset/postcode-directory-for-london
        '''
        self.df = pd.read_csv(csvPath)
        print('Postcodes: loaded csv')        

        if drop_exp:
            self._drop_expired()

        if outcodes_to_drop:
            self._drop_outcodes(outcodes_to_drop)  # The default dropped outcodes are only for London-based post office sorting locations.

        if dicts:
            self._create_dicts()

    def _drop_expired(self):
        '''
        Drops all postcodes marked with an expiry date from the DataFrame.
        '''
        self.df = self.df[self.df['doterm'].isnull()]
        print('Postcodes: dropped expired')
    
    def _drop_outcodes(self, to_drop: list):
        '''
        Drops postcodes that start with the outcodes specified in 'to_drop' from the DataFrame.
        '''
        self.df['outcode'] = [postcode.split(' ')[0] for postcode in self.df['pcds']]
        self.df = self.df[~self.df['outcode'].isin(to_drop)]
        print('Postcodes: dropped selected outcodes')

    def _create_dicts(self):
        '''
        Adds two dictionaries to object attributes: 
        1) postcode -> (lat, long)
        2) (lat, long) -> postcode
        '''
        self.postcodeDict = {postcode: (lat, lon) for postcode, lat, lon in zip(self.df['pcds'], self.df['lat'], self.df['long'])}
        for postcode, latlong in self.postcodeDict.items():
            if latlong in self.latlongDict:
                self.latlongDict[latlong].append(postcode)
            else:
                self.latlongDict[latlong] = [postcode]
        print('Postcodes: created dicts')

    def get_outcodes(self):
        '''
        Returns sorted list of all unique outcodes (first part of a UK postcode) in these postcodes.
        '''
        if not self.outcodes:
            for postcode in self.postcodeDict.keys():
                if postcode.split(' ')[0] in self.outcodes:
                    continue
                else:
                    self.outcodes.append(postcode.split(' ')[0])
            self.outcodes.sort()

        return self.outcodes
        
if __name__ == "__main__":

    p = Postcodes()
    p.load('postcodes_example.csv')
    # print(p.df[['pcds', 'lat', 'long']])
    print(len(p.postcodeDict))

    countDict = {latlong: len(postcodes) for latlong, postcodes in p.latlongDict.items()}
    sortedCounts = sorted(countDict.values())[::-1]
    print(sortedCounts[:100])

    # countDict2 = {count: p.latlongDict[latlong] for latlong, count in countDict.items()}
    # for count in sortedCounts[:10]:
    #     print(count, countDict2[count])