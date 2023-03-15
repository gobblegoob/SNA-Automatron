'''
Create an authenticated session object for SNA
'''

import requests
import json

try:
    requests.packages.urllib3.disable_warnings()
except:
    pass


class SnaAPISession():

    def __init__(self):
        self.SNA_AUTH_FILE = 'sna.json'
        self.API_USER = ''
        self.API_PASSWORD = ''
        self.SMC_URL = ''
        self.API_SESSION = requests.Session()

        # SNA Constants
        self.XSRF_HEADER_NAME = 'X-XSRF-TOKEN'

        # SNA deployment data
        # # This data is required to build queries
        self.SNA_TENANT = ''
        self.SNA_TAGS = {} 
        
        return

    def get_cred_json(self, js_file):
        '''
        Set the credentials, base url, etc
        :arg: str - filename of json cred file
        :return:
        '''
        try:
            with open(js_file) as f:
                api_dict = json.load(f)
                self.BASE_URL = api_dict['SMC_HOST']
                self.API_USER = api_dict['SMC_USER']
                self.API_PASSWORD = api_dict['SMC_PASSWORD']
                return
        except FileNotFoundError as e:
            print(f'Source file not found!  No SNA credentials available \n {e}')

    
    def session_authc(self):
        '''
        Authenticate the session and save the cookie as XSRF-HEADER-NAME
        Default cookie lifetime is 20 mins
        :arg: API Session object
        :return:
        '''
        url = self.BASE_URL + '/token/v2/authenticate'
        login_data = {
            "username": self.API_USER,
            "password": self.API_PASSWORD
        }

        try:
            r = self.API_SESSION.request('POST', url, verify=False, data=login_data)

            if r.status_code == 200:
                print(f'{self.API_USER} is authenticated!')

                #set xsrf token for future requests
                for cookie in r.cookies:
                    if cookie.name == 'XSRF-TOKEN':
                        self.API_SESSION.headers.update({self.XSRF_HEADER_NAME: cookie.value})
                        break
                return 
        
            else:
                print(f'Failure to authenticate session: {r.status_code}')
                quit()

        except ConnectionError as ce:
            print(f'Connection to SMC failed.\n{ce}')
            quit()

    def sna_session_init(self, js_file):
        '''
        Initializes session variables based on a source json file.
        :arg: str - json file name
        :return:
        '''
        # Pull in creds from json file
        self.get_cred_json(js_file)
        # Authenticate api session
        self.session_authc()
        # get tenant id and set
        self.get_tenant_id()
        # get a list of all sna tags
        self.get_tags()
        return


    def end_api_session(self):
        uri = self.BASE_URL + '/token'
        r = self.API_SESSION.delete(uri, timeout=30, verify=False)
        self.API_SESSION.headers.update({self.XSRF_HEADER_NAME: None})
        print(f'Session terminated: {r}')


    def get_tenant_id(self):
        '''
        Set global variable for tenant ID - also returns the tenant ID
        :return: str
        '''
        url = self.BASE_URL + '/sw-reporting/v1/tenants'

        try:
            r = self.API_SESSION.request('GET', url, verify=False)
            if r.status_code == 200:
                tenants = json.loads(r.content)['data']
                tenant_id = tenants[0]['id']
                self.SNA_TENANT = str(tenant_id)
                return
            else:
                print(f'Bad response from get_tenant_id: {r.status_code}')
        except Exception as e:
            print(f'Encountered exception in get_tenant_id: {e}')


    def get_tags(self):
        '''
        Gets a list of all SNA tags/hostgroups
        Set global class variable SNA_TAGS
        :return: list
        '''
        url = self.BASE_URL + '/smc-configuration/rest/v1/tenants/' + self.SNA_TENANT + '/tags/'

        try:
            r = self.API_SESSION.request('GET', url, verify=False)
            if r.status_code == 200:
                self.SNA_TAGS = json.loads(r.content)['data']
                return self.SNA_TAGS
            else:
                print(f'Bad response in get_tags: {r.response.status_code}')
        except Exception as e:
            print(f'Encountered exception in get_tags: {e}')


if __name__ == '__main__':
    session = SnaAPISession()

    session.get_cred_json('sna.json')
    session.session_authc()

    session.get_tenant_id()
    print(session.SNA_TENANT)

    session.get_tags()
    print(json.dumps(session.SNA_TAGS, indent=4))


    session.end_api_session()