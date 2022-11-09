'''
    Check a list of IP's for associated domain names on Shodan.io
    Input:
        - A list of IP addresses from SNA - Most likely public IP addresses that are unknown that you want to add to SNA host groups
        - A list of domains you want to look for
'''

import requests
from datetime import datetime
import csv
import json
from openpyxl import Workbook
import re

class ShodanQuery():

    BASE_URL = 'https://api.shodan.io/shodan/host/'
    API_KEY = ""
    # This is the list of IP addresses you are targeting to add to a hostgroup
    output_list = []
    # This is a dict of IP's and associated domains that do not fit the criteria of your search
    other_hosts = []
    SRC_IP_LIST = []


    def __init__(self):
        self.BASE_URL = 'https://api.shodan.io/shodan/host/'
        self.API_KEY = ''
        # This is the list of IP addresses targeted to add to a hostgroup
        self.OUTPUT_LIST = []
        self.OTHER_HOSTS = []
        self.SRC_IP_LIST = [
            '52.71.205.145',
            '54.205.147.219',
            '100.24.139.212',
            '34.218.87.84',
            '35.164.169.76'
        ]

        self.SRC_IP_LIST = ['34.218.87.84']

    def get_cred_json(self, js_file):
        """
        Look for the json file with Shodan credentials
        """
        try:
            with open(js_file) as f:
                api_dict = json.load(f)
                self.API_KEY = api_dict['shodan_api_key']
        except FileNotFoundError as e:
            print(f' Source file not found! \n {e}')
            quit()

    def get_ip_list(self):
        '''
        Gets a list o fIP's to query from a designated file
        :return:
        '''
        
        with open('newiplist.csv', newline='') as iplist:
            ipreader = csv.reader(iplist, delimiter=',')
            for ip in ipreader:
                self.SRC_IP_LIST.append(ip[0])

        self.SRC_IP_LIST = self.dedup_list(self.SRC_IP_LIST)
        return
    

    def set_ip_list(self, ip_list):
        '''
        Sets IP list based on a list passed as an argument
        :arg: list - list of ip addresses
        :return: 
        '''
        if ip_list != None:
            self.SRC_IP_LIST = self.dedup_list(ip_list)
        else:
            print('IP List is empty')
        return


    def get_host(self, src_ip):
        query = self.BASE_URL + src_ip + '?key=' + self.API_KEY

        payload = {}
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            response = requests.request("GET", query, headers=headers, data=payload)
            response = response.json()
            return response
        except Exception as e:
            print(f'API Query Error: \n {e}')



    def dedup_list(self, my_list):
        '''
        deduplicate a list
        '''
        deduped_list = list(dict.fromkeys(my_list))
        return deduped_list


    def find_ip_by_domain(self, response, domain):
        '''
        Will investigate each API response looking for our specified domain name(s)
        Will update global variable output_lists to contain all verified host ip addresses
        Will also update a dict of all ip addresses and domains that do not match the specified domain name(s)
        That will allow you to research this list seperately
        :arg: response: The host lookup api response from Shodan.io
        :arg: your speciied domain name(s)
        :return: boolean - True if domain was found, false if not
        '''

        try:
            dlist = response['domains']
            l = dlist.__len__()
            i = 0
            host_ip = response['ip_str']

            for d in dlist:
                if d == domain:
                    self.OUTPUT_LIST.append(host_ip)
                    break
                elif d != domain and i == l-1: 
                    # check the cert CN as a final check
                    if self.check_cert_cn(response) == True:
                        self.OUTPUT_LIST.append(host_ip)
                        break
                    else:
                        other = {
                            'ip': host_ip,
                            'domains': dlist
                            }
                        self.OTHER_HOSTS.append(other)
                        break
                elif d != domain and i < l:
                    i += 1
        except TypeError as e:
            print(f'Type Error Detected: {e}')
        except KeyError as e:
            pass
        except Exception as e:
            print(f'General Excecption in find_ip_by_domain: {e}')



    def unknown_host_to_spreadsheet(self):
        '''
        Creates a spreadhseet with all of hte unknown hosts in the list as well as their
        associated domain names
        :return:
        '''

        wb = Workbook()
        sheet = wb.active
        i = 2

        # Create Headers
        sheet['A1'] = 'IP Address'
        sheet['B1'] = 'Domain 1'
        sheet['C1'] = 'Domain 2'
        sheet['D1'] = 'Domain 3'
        sheet['E1'] = 'Domain 4'
        # Need to incrament a character to position cells in a sheet
        for h in self.OTHER_HOSTS:
            # Need to incrament a character to position cells in a sheet
            # ch and coord handle correctly incrementing the focused cell on the sheet 
            ch = 'A'
            coord = ch + str(i)
            sheet[coord] = h['ip']
            for d in h['domains']:
                ch = chr(ord(ch) + 1)
                coord = ch + str(i)
                sheet[coord] = d
            i += 1
    
        today = datetime.today()
        try:
            my_date = str(today.year) + '_' + str(today.month) + '_' + str(today.day)
            fn = f'{my_date}_OtherDomainsReport.xlsx'
            wb.save(filename=fn)
        except PermissionError as p:
            print(f'Unable to save report: Possibly file with name {fn} is open\n{p}')
            return
        except Exception as e:
            print(f'Error in unknown_host_to_spreadsheet\n {e}')
            return
    
        # print(json.dumps(self.OTHER_HOSTS, indent=4))
        return

    def shodan_query(self, my_domain):
        '''
        Execute shodan queries against our ips in the ip list.  Create the lists
        for domain associated and unmatched ip addresses
        :arg: str -- domain you wish to search for
        :return:
        '''
        self.get_cred_json('shodan.json')
        
        for host in self.SRC_IP_LIST:
            this = self.get_host(host)
            try:
                self.find_ip_by_domain(this, my_domain)
            except KeyError as e:
                print(f'Error looking up {host}\n Shodan may have no data for this IP\n{e}')
                self.output_list.append(host)
        return


    def check_cert_cn(self, response):
        '''
        Check the response for a certificate - CN then SAN fields for a specific string
        This will match a string in the CN or SubjectAltName certificate fields that meet the required criteria
        :arg: dict - response from a host lookup call
        :return: boolean - True if string is found
        '''
        match_string = 'ring.devices.'
        # Check CN Field
        #print(json.dumps(response['data'][0]['ssl']['cert']['subject']['CN'], indent=4))
        my_cn = response['data'][0]['ssl']['cert']['subject']['CN']
        if re.search(match_string, my_cn):
            return True
        else:
            return False

        #subject_alt_name = json.dumps(response['data'][0]['ssl']['cert']['extensions'], indent=4)


if __name__ == "__main__":
    sq = ShodanQuery()
    sq.get_cred_json("shodan.json")
    start_time = datetime.now()

    # Comment this line out for testing
    # sq.get_ip_list()

    sq.shodan_query('ring.com')
    '''
    for host in sq.SRC_IP_LIST:
        this = sq.get_host(host)
        try:
            # print(this['domains'])
            sq.find_ip_by_domain(this, 'ring.com')
        except KeyError as e:
            print(f'Error looking up {host}\n Shodan may have no data for this IP\n Error Reported: {e}')
            sq.output_list.append(host)
        
    #sq.unknown_host_to_spreadsheet()
    '''
    print('Output List --------------------')
    for i in sq.OUTPUT_LIST:
        print(f'{i}')
    print('End Output List --------------------')
