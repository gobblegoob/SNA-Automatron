'''
Takes multiple domains and cert strings
- runs one query so shodan and SNA only need to be queried one time
'''

from SnaAPISession import SnaAPISession
from SnaQuery import SnaQuery
from ShodanQuery import ShodanQuery
from SnaTagAdd import SnaTagAdd
from datetime import datetime
from colorama import Fore, Style
import os
import json
import re
import argparse
import pandas as pd

# Your search info.
'''
certstr = CN or SAN text to match with regex
destinationtag = Your destination hostgroup
'''
MY_DATA = {
    'domain1.com': {
        'certstr': 'Cert CN or SAN Regex',
        'destinationtag': 'Name of Hostgroup'
    },
    'domain2.com': {
        'certstr': 'Cert CN or SAN regex',
        'destinationtag': 'Name of another Hostgroup'
    }
}

OTHER_HOSTS = []
CLEANUP_HOSTS = [] # IP's to clear from other hosts report


def list_domains():
    '''
    Print a list of domains and destination tags
    '''
    print(json.dumps(MY_DATA, indent=4))
    quit()
    

def get_friendly_date():
    '''
    Prints the time to the console
    :return: str for printing
    '''
    d = datetime.now()
    time = d.strftime('%a, %b %d %Y %H:%M:%S %p')
    return time


def shodan_lookup_list(query_results):
    '''
    Get a list of peer IP addresses.  This will be the source for the shodan query
    :return: list - ip addresses for shodan lookup
    '''
    lookup_list = []
    for i in query_results:
        lookup_list.append(i['peer']['ipAddress'])

    dedup_list = list(dict.fromkeys(lookup_list))
    return dedup_list

def cert_check(host, certstr):
    '''
    Checks for a cert cn or san field, if present and matches our cert
    returns true
    :arg: dict
    :return: boolean
    '''
    if host['cert_cn']:
        #print(f'Trying to match cn: {host["cert_cn"]} with string {certstr}')
        if re.search(certstr, re.escape(host['cert_cn'])) is not None:
            #print(f'CN match found for {host["cert_cn"]}')
            return True
    if host['cert_san']:
        if re.search(certstr, re.escape(host['cert_san'])) is not None:
            # print(f'{Fore.GREEN}SAN match found for {host["cert_san"]}{Style.RESET_ALL}')
            return True
    return False


def delete_file(f):
    '''
    :arg: str - filename
    :return: boolean
    '''
    try:
        os.remove(f)
        return True
    except FileNotFoundError as e:
        print(f'{Fore.LIGHTRED_EX}Unable to delete {f}\n{e}{Style.RESET_ALL}')
        return


def cleanup_report(df):
    '''
    Identified hosts will be removed from the other domain reports
    :arg: Pandas Dataframe
    :return: DataFrame
    '''
    for i in CLEANUP_HOSTS:
        row = df.loc[df['ip'] == i]
        df = df.drop(row.index, axis = 0)
    return df


if __name__ == '__main__':
    # initialize our classes
    api = SnaAPISession()
    query = SnaQuery()
    shodan = ShodanQuery()
    addtag = SnaTagAdd()

    print(f'{Fore.CYAN}SNA Multidomain Hostgroup Updater' + '-' * 60)
    print(get_friendly_date())
    print(Style.RESET_ALL)
    starttime = datetime.now()
    delete_file('shodanresult.json')

    helptext = (
        'Get domain info from Shodan and update hostgroups in Secure Network Analytics automatically'
    )

    parser = argparse.ArgumentParser(description=helptext)

    parser.add_argument('-l', '--log', action='store_true', help='Add output to log file')
    parser.add_argument('-rx', '--reportxlsx', action='store_true', help='Output Unidentified Domain data to xlsx report file')
    parser.add_argument('-t', '--time', type=int, help='Report time in minutes.  Default is 1440 (24 hours)')
    parser.add_argument('-ld', '--listdomains', action='store_true', help='List domains and destination host groups')

    args = parser.parse_args()
    if args.log:
        logging = True
        print('Unable to support logging at this time')

    if args.time:
        QUERY_TIME = args.time
        print('Unable to set query time in this version')

    # Start API session on SNA
    api.sna_session_init('sna.json')
    query.set_sna_json('sna.json')
    query.init_query(api.SNA_TAGS)

    query_results  = query.run_flow_query(api)

    print(' -- Begining Shodan Lookups -- ')
    lookup_list = shodan_lookup_list(query_results)
    shodan.set_ip_list(lookup_list)

    # execute query and create json file with query results for reuse
    if shodan.shodan_persistant_query() is True:
    #if True is True:
        with open('shodanresult.json', 'r') as file:
            r = json.load(file)

        # Iterate my source data
        for k in MY_DATA:
            HOST_LIST = []
            DOMAIN = k # str
            CERT_STR = MY_DATA[k]['certstr'] # str
            DEST_TAG = MY_DATA[k]['destinationtag']

            # Look for your domain/cert string
            for key in r.keys():
                try:
                    HOST_IP = key
                    dlist = r[HOST_IP]['domains']
                    
                    q = {
                        'ip': HOST_IP,
                        'domains': dlist
                    }

                    OTHER_HOSTS.append(q)

                    for d in dlist:
                        if d == DOMAIN:
                            HOST_LIST.append(HOST_IP)
                            OTHER_HOSTS.remove(q)
                            break
                        else:
                            continue
                    if cert_check(r[HOST_IP], CERT_STR) is True:
                        HOST_LIST.append(HOST_IP)
                        OTHER_HOSTS.remove(q)
                    else:
                        continue
                except KeyError as e:
                    continue

            print(f'{Fore.LIGHTYELLOW_EX}{DOMAIN} Host List:\n{HOST_LIST}{Style.RESET_ALL}')

            if DEST_TAG == '':
                print(f'No destination tag designated for {DOMAIN}')
                continue

            target_tag_id = addtag.get_my_tag_id(DEST_TAG, api.SNA_TAGS)
            print(f'{Fore.GREEN}-- Updating tag: {DEST_TAG} ID: {target_tag_id} with {HOST_LIST.__len__()} values.{Style.RESET_ALL} ')

            # Update the desetination tag - Reauthenticate if SNA session cookie is expired.
            if addtag.update_tags(HOST_LIST, api) is False:
                api.session_authc()
                addtag.update_tags(HOST_LIST, api)
                
            for i in HOST_LIST:
                    CLEANUP_HOSTS.append(i)


    else:
        print('Unable to locate shodan result file')
        
    api.end_api_session()
    delete_file('shodanresult.json')

    if args.reportxlsx == True:
        today = datetime.today()
        filename = f'{str(today.year)}_{str(today.month)}_{str(today.day)}_OtherDomainsReport.xlsx'
        df = pd.DataFrame.from_dict(OTHER_HOSTS)
        df = df.drop_duplicates(subset=['ip'], keep='first')
        df = cleanup_report(df)
        df.to_excel(filename, index=False, freeze_panes=(1,0))
        pass

    print(f'\nTask Completed: {get_friendly_date()}')
    endtime = datetime.now()
    print(f'Time Elapesed: {endtime - starttime}\n')