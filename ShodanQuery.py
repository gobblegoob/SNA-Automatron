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
import time

class ShodanQuery():


    def __init__(self):
        self.BASE_URL = 'https://api.shodan.io/shodan/host/'
        self.API_KEY = ''
        # This is the list of IP addresses targeted to add to a hostgroup
        self.OUTPUT_LIST = []
        # this is a list of IP addresses and associated domains that do not fit the criteria of your search
        self.OTHER_HOSTS = []
        self.SRC_IP_LIST = [
            '17.253.11.200',
            '3.217.147.217',
            '8.8.8.8',
            '17.248.190.70',
            '34.194.167.237',
            '23.203.120.24'
        ]
        self.CERT_STR = ''

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
            # Delay 1 second to meet Shodan rate limiting
            time.sleep(1)
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
        if self.OTHER_HOSTS == {}:
            print('No unconfirmed hosts detected\nNot creating an unknown domain spreadsheet.')
            return

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
                # Breaks the loop and continues on if more than 26 domain names are seen
                if ch == '[':
                    break
                coord = ch + str(i)
                sheet[coord] = d
            i += 1
    
        today = datetime.today()
        try:
            my_date = str(today.year) + '_' + str(today.month) + '_' + str(today.day)
            fn = f'{my_date}_OtherDomainsReport.xlsx'
            wb.save(filename=fn)
            print(f'Report Created! {fn}')
        except PermissionError as p:
            print(f'Unable to save report: Possibly file with name {fn} is open\n{p}')
            return
        except Exception as e:
            print(f'Error in unknown_host_to_spreadsheet\n {e}')
            return
    
        # print(json.dumps(self.OTHER_HOSTS, indent=4))
        return


    def progress_bar(self, progress, total):
        percent = 100 * progress / float(total)
        bar = '█' * int(percent) + '-' * (100 - int(percent))
        print(f'\r|{bar}| {percent:.2f}%', end='\r')


    def shodan_query(self, my_domain):
        '''
        Execute shodan queries against our ips in the ip list.  Create the lists
        for domain associated and unmatched ip addresses
        :arg: str -- domain you wish to search for
        :return:
        '''
        self.get_cred_json('shodan.json')
        
        total = self.SRC_IP_LIST.__len__()
        print(f'Total IPs searching in Shodan {total}')
        i = 1
        self.progress_bar(i, total)

        for host in self.SRC_IP_LIST:
            this = self.get_host(host)
            self.progress_bar(i, total)
            i += 1
            # If I receive an error response, ensure that it is captured in the Other Hosts report
            for key in this.keys():
                if key == 'error':
                    q = {
                            'ip': host,
                            'domains': [this['error']]
                        }
                    self.OTHER_HOSTS.append(q)
            try:
                self.find_ip_by_domain(this, my_domain)
                
            except KeyError as e:
                # print(f'Error looking up {host}\n Shodan may have no data for this IP\n{e}')
                self.OTHER_HOSTS.append(host)
        return


    def shodan_persistant_query(self):
        '''
        A query that creates a persistant file of truncated shodan results
        :arg: str
        :return: boolean
        '''
        self.get_cred_json('shodan.json')
        my_dict = {}

        total = self.SRC_IP_LIST.__len__()
        p = 1

        print(f'Searching Shodan for {total} unique IPs')

        for host in self.SRC_IP_LIST:

            self.progress_bar(p, total)
            p += 1

            h = self.get_host(host)
            for key in h.keys():
                cert_cn = ''
                cert_san = ''
                if key == "error":
                    continue
                else:
                    domains = h['domains']
                    try:
                        cert_cn = h['data'][0]['ssl']['cert']['subject']['CN']
                        for i in h['data'][0]['ssl']['cert']['extensions']:
                            if i['name'] == 'subjectAltName':
                                cert_san = i['data']
                        my_dict[host] = {'domains': domains, 'cert_cn': cert_cn, 'cert_san': cert_san}
                        continue
                    except KeyError:
                        my_dict[host] = {'domains': domains}
            
        with open('shodanresult.json', 'w') as my_file:
             my_file.write(json.dumps(my_dict))
             return True


    def check_cert_cn(self, response):
        '''
        Check the response for a certificate - CN then SAN fields for a specific string
        This will match a string in the CN or SubjectAltName certificate fields that meet the required criteria
        :arg: dict - response from a host lookup call
        :return: boolean - True if string is found
        '''
        # match_string = ''
        # Check CN Field
        if self.CERT_STR != '':
            my_cn = response['data'][0]['ssl']['cert']['subject']['CN']
            if re.search(self.CERT_STR, my_cn):
                # print(f'CN match found for {my_cn}')
                return True
            else:
                is_found = False
                # check SAN fields of cert for your string
                is_found = self.check_cert_san(response)
                return is_found
        else:
            return


    def check_cert_san(self, response):
        '''
        Look up the SAN fields in the certs for your designated string
        :return: boolean - true if found
        '''
        for i in response['data'][0]['ssl']['cert']['extensions']:
            if i['name'] == 'subjectAltName':
                # print(f'Name: {i["name"]}\nData: {i["data"]}')
                if re.search(self.CERT_STR, i['data']):
                    # print('SAN match found')
                    return True
                else:
                    # print('SAN match not found')
                    return False
        
        return False


    def set_cert_str(self, cert_str):
        '''
        Pulls in the cert match str and sets the corresponding global variable
        This string is regex that matches a CN or SAN field entry for a sites certificate.
        This is an additional check you can run against Shodan to help accurately identify
        internet hosts
        :arg: str
        :return:
        '''
        self.CERT_STR = cert_str
        return


if __name__ == "__main__":
    sq = ShodanQuery()
    sq.get_cred_json("shodan.json")
    start_time = datetime.now()

    # Comment this line out for testing
    # sq.get_ip_list()

    #sq.shodan_query('ring.com')
    sq.shodan_persistant_query()
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
    print('---- PRINTING OTHER HOSTS DICTIONARY----')
    print(json.dumps(sq.OTHER_HOSTS, indent=4))
