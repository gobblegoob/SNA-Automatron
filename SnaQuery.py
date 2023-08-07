''''
    Flow Query SNA
'''

import json
import datetime
import time
import colorama

class SnaQuery():

    def __init__(self):
        self.FLOW_QUERY_FILE = 'sna-flowquery.json'
        self.API_SESSION = ''
        self.SNA_JSON = ''

        # Tag names
        self.SOURCE_TAG_NAMES_INCLUDE = []
        self.SOURCE_TAG_NAMES_EXCLUDE = []
        self.DEST_TAG_NAMES_INCLUDE = []
        self.DEST_TAG_NAMES_EXCLUDE = []

        # Tag ID numbers
        self.SOURCE_TAG_ID_INCLUDE = []
        self.SOURCE_TAG_ID_EXCLUDE = []
        self.DEST_TAG_ID_INCLUDE = []
        self.DEST_TAG_ID_EXCLUDE = []

        # Dictionary with the query payload 
        self.FLOW_QUERY = {}

        self.QUERY_NAME = 'My Automated Flow Query'
        self.QUERY_TIME = 1440  # Default minutes for flow query scan. 24 hours.

    def set_sna_json(self, fn):
        '''
        Set the source json file
        :arg: str - name of json file
        :return:
        '''
        self.SNA_JSON = fn
        return
    
    def get_query_data(self):
        '''
        Read the sna json file for query data
        :return:
        '''
        try:
            with open(self.SNA_JSON) as f:
                my_dict = json.load(f)
                self.SOURCE_TAG_NAMES_INCLUDE = my_dict['TAGS']['SOURCE_TAG_NAMES']['INCLUDE']
                self.SOURCE_TAG_NAMES_EXCLUDE = my_dict['TAGS']['SOURCE_TAG_NAMES']['EXCLUDE']
                self.DEST_TAG_NAMES_INCLUDE = my_dict['TAGS']['DESTINATION_TAG_NAMES']['INCLUDE']
                self.DEST_TAG_NAMES_EXCLUDE = my_dict['TAGS']['DESTINATION_TAG_NAMES']['EXCLUDE']
            return self.SNA_JSON
        except FileNotFoundError as e:
            print(f'Unable to locate source json file {self.SNA_JSON}\n{e}')
            quit()


    def set_tag_ids(self, tags):
        '''
        Get query tag names and pull the tag ID numbers.
        '''
        #print(json.dumps(tags_dict, indent = 4))

        # set the source tag id list for include
        for stni in self.SOURCE_TAG_NAMES_INCLUDE:
            for i in tags:
                if i['name'] == stni:
                    self.SOURCE_TAG_ID_INCLUDE.append(i['id'])

        # set the source tag id list for exclude
        for stne in self.SOURCE_TAG_NAMES_EXCLUDE:
            for j in tags:
                if j['name'] == stne:
                    self.SOURCE_TAG_ID_EXCLUDE.append(j['id'])

        # set the destination tag id for include
        for dtni in self.DEST_TAG_NAMES_INCLUDE:
            for k in tags:
                if k['name'] == dtni:
                    self.DEST_TAG_ID_INCLUDE.append(k['id'])

        # set the destination tag for exclude
        for dtne in self.DEST_TAG_NAMES_EXCLUDE:
            for l in tags:
                if l['name'] == dtne:
                    self.DEST_TAG_ID_EXCLUDE.append(l['id'])

        print(f'Included source tags: {self.SOURCE_TAG_ID_INCLUDE}')
        print(f'Excluded source tags: {self.SOURCE_TAG_ID_EXCLUDE}')            
        print(f'Included destination tags: {self.DEST_TAG_ID_INCLUDE}')
        print(f'Excluded destination tags: {self.DEST_TAG_ID_EXCLUDE}')
        return

    
    def get_flow_query(self):
        '''
        Pull the flow query json file in as a dictionary.  
        This will allow us to set query parameters and set the query payload
        :return:
        '''
        try:
            with open('sna-flowquery.json') as f:
                self.FLOW_QUERY = json.load(f)
                f.close()
                return

        except FileNotFoundError as e:
            print(f'Flow Query file not found: {e}')
            quit()

    
    def create_flow_query(self):
        '''
        Merges our query parameters with the query payload
        :return:
        '''
        # Create timestamps for query filters in the correct format.  
        end_datetime = datetime.datetime.utcnow()
        # This line dictates how far back the flow query would go
        # 1440 minutes = 24 hours
        # Shorten for quicker tests
        start_datetime = end_datetime - datetime.timedelta(minutes=self.QUERY_TIME)
        end_timestamp = end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')
        start_timestamp = start_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')

        self.FLOW_QUERY['startDateTime'] = start_timestamp
        self.FLOW_QUERY['endDateTime'] = end_timestamp

        # Set the query parameters peer and subject tag ids
        self.FLOW_QUERY['searchName'] = self.QUERY_NAME
        self.FLOW_QUERY['subject']['hostGroups']['includes'] = self.SOURCE_TAG_ID_INCLUDE
        self.FLOW_QUERY['subject']['hostGroups']['excludes'] = self.SOURCE_TAG_ID_EXCLUDE
        self.FLOW_QUERY['peer']['hostGroups']['includes'] = self.DEST_TAG_ID_INCLUDE
        self.FLOW_QUERY['peer']['hostGroups']['excludes'] = self.DEST_TAG_ID_EXCLUDE

        # print(json.dumps(self.FLOW_QUERY, indent=4))
        return


    def run_flow_query(self, session):
        '''
        Initiates the flow query - and returns the results as the report finishes
        Imports the api session object and variables from SnaAPISession
        :return:
        '''
        query_url = session.BASE_URL  + '/sw-reporting/v2/tenants/' + session.SNA_TENANT + '/flows/queries'
        
        request_headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json'
        }

        my_session = session.API_SESSION

        r = my_session.request('POST', query_url, verify=False, data=json.dumps(self.FLOW_QUERY), headers=request_headers)
        if r.status_code == 201:
            print('Getting SNA Flow Query... Please wait...\n')
            search = json.loads(r.content)['data']['query']

            url = session.BASE_URL + '/sw-reporting/v2/tenants/' + session.SNA_TENANT + '/flows/queries/' + search['id']

            # While search is not complete - check status every x seconds
            while search['percentComplete'] != 100.0:
                r = my_session.request('GET', url, verify=False)
                search = json.loads(r.content)['data']['query']

                # Adding a nice progress bar
                if search['percentComplete'] < 100.0:
                    color = 'colorama.Fore.YELLOW'
                else:
                    color = 'colorama.Fore.GREEN'

                percent = 100.0 * (search['percentComplete']/float(100.0))
                bar = '█' * int(percent) + '-' * (100 - int(percent))
                print(color + f'\r|{bar}| {percent:.2f}%', end='\r')

                time.sleep(1)
            
            print(colorama.Fore.GREEN + '\n -- SNA Flow Query Completed -- ')
            print(colorama.Fore.RESET)
            # set the url to check check the serach results and get them
            url = session.BASE_URL + '/sw-reporting/v2/tenants/' + session.SNA_TENANT + '/flows/queries/' + search["id"] + "/results"
            r = my_session.request('GET', url, verify=False)
            results = json.loads(r.content)['data']['flows']

            #print(json.dumps(results, indent=4))
        return results


    def init_query(self, tags):
        '''
        Initializes the query data 
        :return:
        '''
        self.get_query_data()
        self.set_tag_ids(tags)
        self.get_flow_query()
        self.create_flow_query()
        
        return
    

    def set_query_name(self, qname):
        '''
        Can set the name of the query so it shows up in logs
        :arg: str - Name of query
        :return:
        '''
        if qname is not None:
            self.QUERY_NAME = qname
            return
        else:
            return


if __name__ == '__main__':
    query = SnaQuery()

    # set query file
    query.set_sna_json('sna-flowquery.json')
    query.get_query_data()