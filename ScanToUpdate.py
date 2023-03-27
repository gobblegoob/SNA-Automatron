from SnaAPISession import SnaAPISession
from SnaQuery import SnaQuery
from ShodanQuery import ShodanQuery
from SnaTagAdd import SnaTagAdd
from datetime import datetime
import argparse
'''
    Run this script to:
        1. Execute an SNA Flow Query based on your parameters
        2. Query Shodan for identified IP addresses for a public domain name
        3. Update a designated host group.

        Get Domain info from Shodan and update hostgroups in Secure Network Analytics automatically

        optional arguments:
            -h, --help            show this help message and exit
            -d DOMAIN, --domain DOMAIN
                        Domain you wish to search for
            -t TAG, --tag TAG     What tag or hostrgroup to you wish to update for the given domain
            -c CERTSTRING, --certstring CERTSTRING
                        Enter a regex match string for cert CN and SAN fields
            -rx, --reportxlsx     Output unknown domains to an excel file

'''
# This is the domain name you want to search Shodan for
MY_DOMAIN = ''
# Add the tag name you wish this script to update.  Only one name is supported at the moment.  Don't put in more than one value!
MY_TAG_TO_UPDATE = []
# Enter a partial match string for a certificate CN or SAN based on your search.
# This can help pull more accurate results if domain info is unavailable in Shodan
CERT_STR = ''

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
    return lookup_list

def input_my_domain():
    '''
    Text prompt for destination domain as seen in Shodan result. IE: ring.com
    :return: str - my_domain
    '''
    my_domain = input('Enter the domain you wish to search: ')
    return my_domain


def input_my_tag():
    '''
    This is the dynamically updated tag we will put our designated hosts into
    :return: my_tag
    '''
    tag_list = []
    my_tag = input('Enter the hostgroup you wish to update: ')
    tag_list.append(my_tag)
    return tag_list


if __name__ == '__main__':
    # initialize our classes
    api = SnaAPISession()
    query = SnaQuery()
    shodan = ShodanQuery()
    tag = SnaTagAdd()

    print('Starting SNA Query Script' + '-' * 60)
    print(get_friendly_date())
    starttime = datetime.now()

    helptext = (
        'Get Domain info from Shodan and update hostgroups in Secure Network Analytics automatically'
    )

    parser = argparse.ArgumentParser(description=helptext)

    parser.add_argument('-d', '--domain', type=str, help = 'Domain you wish to search for')
    parser.add_argument('-t', '--tag', type=str, help='What tag or hostrgroup to you wish to update for the given domain')
    parser.add_argument('-c', '--certstring', type=str, help='Enter a regex match string for cert CN and SAN fields')
    parser.add_argument('-rx', '--reportxlsx', action="store_true", help='Output unknown domains to an excel file')
    #parser.add_argument('-r', '--report', action="store_true", help = 'Unknown hosts report will be printed to the terminal')

    args = parser.parse_args()
    if args.domain is not None:
        MY_DOMAIN = args.domain
        print(f'Searching {MY_DOMAIN}')

    if args.tag is not None:
        MY_TAG_TO_UPDATE.append(args.tag)
        print(f'To update tag {MY_TAG_TO_UPDATE[0]}')

    if args.certstring is not None:
        CERT_STR = args.certstring
        print(f'Cert string match is {args.certstring}')

    # set my destination tag name.
    if MY_TAG_TO_UPDATE == []:
        MY_TAG_TO_UPDATE = input_my_tag()

    # if the cert search string is set in CERT_STR, pass that to the Shodan object
    if CERT_STR != '':
        shodan.set_cert_str(CERT_STR)


    api.sna_session_init('sna.json')
    query.set_sna_json('sna.json')
    qname = f'{MY_DOMAIN} Flow Query'
    query.set_query_name(qname)
    query.init_query(api.SNA_TAGS)

    # execute the query - needs the api object we created to complete this
    query_results = query.run_flow_query(api)

    # create a peer list to query at shodan - deduplicated
    print(' -- Beginning Shodan Lookups -- ')
    lookup_list = shodan_lookup_list(query_results)
    shodan.set_ip_list(lookup_list)

    # Search for your targeted domain in Shodan if the MY_DOMAIN global variable is not set above
    if MY_DOMAIN == '':
        MY_DOMAIN = input_my_domain()
        shodan.shodan_query(MY_DOMAIN)
    else:
        shodan.shodan_query(MY_DOMAIN)

    print(shodan.OUTPUT_LIST)

    # Get my destination tag ID from SNA
    target_tag = tag.get_my_tag_id(MY_TAG_TO_UPDATE, api.SNA_TAGS)
    print('\n')

    # Update tags in SNA
    print(f'\n -- Updating {MY_TAG_TO_UPDATE[0]} ID:{target_tag} with {shodan.OUTPUT_LIST.__len__()} Values -- \n')

    # Before attempting to update tags, validate that a session cookie is still valid
    if tag.update_tags(shodan.OUTPUT_LIST, api) is False:
        api.session_authc()
        tag.update_tags(shodan.OUTPUT_LIST, api)

    if args.reportxlsx:
        print('\t------\nGenerating Unknown Hosts Spreadsheet\n\t------')
        shodan.unknown_host_to_spreadsheet()

    # End API Session
    api.end_api_session()
    print(f'\nTask Completed: {get_friendly_date()}')
    endtime = datetime.now()
    print(f'Time Elapsed: {endtime - starttime}\n')

    quit()
