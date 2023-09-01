'''
Ingests a list of IP addresses - will add these IP addresses to the designated hostgroups

inputs: 
 - ip list
 - destination hostgroups (list)

execute: 
 - hostgroup upgrade
output: 
 - success?

'''
import json
import requests

class SnaTagAdd():

    def __init__(self):
        self.MY_TAG_ID = ''
        self.MY_TAG_NAME = ''


    def get_my_tag_id(self, tag_name, tags):
        '''
        Gets a tag name for the tag we wish to update and returns the tag id
        :arg: tag_name str - name of tag/hostgroup to update
        :arg: tags - dict - all tags from the SNA session object
        :return: tag_id
        '''

        for i in tags:
            if i['name'] == tag_name:
                self.MY_TAG_ID = i['id']
                self.MY_TAG_NAME = i['name']
                break
            elif i['name'] == tag_name[0]:
                self.MY_TAG_ID = i['id']
                self.MY_TAG_NAME = i['name']
                break
            else:
                # Clear tag id if the tag we're searching for is not found.
                self.MY_TAG_ID = ''
        return self.MY_TAG_ID


    def get_tag_data(self, url, sna_session):
        '''
        In order to update a tag - we must pull the tag data to create the payload
        :arg: int tag id
        :arg: SnaAPISession object
        :return: dict Tag Data
        '''
        response_headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json'
        }
        r = sna_session.request('GET', url, verify=False, headers=response_headers)
        if r.status_code == 200:
            data = json.loads(r.content)
            return data['data']
        else:
            print(f'Error getting tag data {r.status_code}')
            if r.status_code == 401:
                print(f'Session timed out.  Attempting to reauthenticate session ')
                return False
            else:
                print('Closing the program')
                quit()

    
    def dedup_list(self, l):
        '''
        Return a deduplicated list
        :arg: list - some list
        :return: list - a deduplicated list
        '''
        dlist = list(dict.fromkeys(l))
        return dlist
        

    def update_tags(self, ip_list, sna_session):
        '''
        ingests IP list in order to add to the source
        :arg: list - ip list
        :arg: object - sna session object
        '''

        request_headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json'
        }
        my_session = sna_session.API_SESSION

        # Do not continue if MY_TAG_ID is unset.  This is probably due to an invalid destination tag selected 
        if self.MY_TAG_ID == '':
            print(f'The destination tag {self.MY_TAG_NAME} is likely invalid.  Unable to update Tag.')
            return

        url = sna_session.BASE_URL + '/smc-configuration/rest/v1/tenants/' + sna_session.SNA_TENANT + '/tags/' + str(self.MY_TAG_ID)

        payload = self.get_tag_data(url, my_session)

        # Validate session is still active, return false if the session cookie is expired
        if payload is False:
            return False

        updated_ranges = payload['ranges']
        for ip in ip_list:
            updated_ranges.append(ip)
        updated_ranges = self.dedup_list(updated_ranges)

        payload['ranges'] = updated_ranges
        
        r = my_session.request('PUT', url, verify=False, data=json.dumps(payload), headers=request_headers )

        if r.status_code == 200:
            print(f'Tag {self.MY_TAG_NAME} is updated!')

        else:
            print(f'There was an error updating the host group {self.MY_TAG_NAME}\n{r.status_code}')
    
        return
    

    def update_tag_with_removals(self, ip_list, sna_session):
        '''
        Updates a hostgroup while removing stale entries
        :arg: list - ip list
        :arg: object - sna session object
        '''

        request_headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json'
        }
        my_session = sna_session.API_SESSION

        # Do not continue if MY_TAG_ID is unset.  This is probably due to an invalid destination tag selected 
        if self.MY_TAG_ID == '':
            print(f'The destination tag {self.MY_TAG_NAME} is likely invalid.  Unable to update Tag.')
            return

        url = sna_session.BASE_URL + '/smc-configuration/rest/v1/tenants/' + sna_session.SNA_TENANT + '/tags/' + str(self.MY_TAG_ID)

        payload = self.get_tag_data(url, my_session)

        # Validate session is still active, return false if the session cookie is expired
        if payload is False:
            return False

        payload['ranges'] = ip_list
        
        r = my_session.request('PUT', url, verify=False, data=json.dumps(payload), headers=request_headers )

        if r.status_code == 200:
            print(f'Tag {self.MY_TAG_NAME} is updated!')

        else:
            print(f'There was an error updating the host group {self.MY_TAG_NAME}\n{r.status_code}')
    
        return


if __name__ == '__main__':
    tag = SnaTagAdd()
    tag.MY_TAG_NAME = 'Dynamic Ring IPs'
    ip_list = ['34.234.171.45', '52.70.61.48', '52.20.195.83', '34.193.202.53']