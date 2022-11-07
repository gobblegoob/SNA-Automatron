from SnaAPISession import SnaAPISession
from SnaQuery import SnaQuery
from ShodanQuery import ShodanQuery
from SnaTagAdd import SnaTagAdd

# This is the domain name you want to search Shodan for
MY_DOMAIN = ''

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


if __name__ == '__main__':
    # initialize our classes
    api = SnaAPISession()
    query = SnaQuery()
    shodan = ShodanQuery()
    tag = SnaTagAdd()

    # set my destination tag name.
    tag_update = ['Dynamic Ring IPs']

    api.sna_session_init('sna.json')
    query.set_sna_json('sna.json')
    query.init_query()

    # pass the tags/hostgroups from the SnaAPISession to the query
    query.set_tag_ids(api.SNA_TAGS)
    # Pull in query json file
    query.get_flow_query()
    # add our tag id's and timestamps to the query
    query.create_flow_query()
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
    print('Generating Unknown Hosts Spreadsheet')
    shodan.unknown_host_to_spreadsheet()
    
    # Get my destination tag ID from SNA
    target_tag = tag.get_my_tag_id(tag_update, api.SNA_TAGS)
    print(target_tag)

    # Update tags in SNA
    print(' -- Updating Tags -- ')
    # ip_list = ['34.234.171.45', '52.70.61.48', '52.20.195.83', '34.193.202.53']
    # tag.update_tags(ip_list, api)
    #tag.update_tags(shodan.OUTPUT_LIST, api)

    quit()