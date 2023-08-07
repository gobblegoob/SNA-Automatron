'''
    Take a given hostgroup and re-query those IP addresses 
    to see if they still belong in the hostgroup.

    Update the hostgroup haveing removed HG's that no longer 
    belong there
'''

from SnaAPISession import SnaAPISession
from SnaTagAdd import SnaTagAdd
from OpenSSL import crypto
import ssl, socket
from colorama import Fore, Style
from datetime import datetime
import re
import argparse

IP_LIST_TO_REMOVE = []
IP_LIST_TO_ADD = []

def input_target_tag():
    '''
    get and set the target hostgroup name
    :return: str hostgroup
    '''
    thg = input('Enter target hostgroup: ')
    return thg 


def get_target_tag_id(target_tag):
    '''
    Get the target tag ID
    :arg: str - Tag name
    :retrun: str - tag ID
    '''
    for key in api.SNA_TAGS:
        if key['name'] ==  target_tag:
            target_tag_id = key['id']
    
    if target_tag_id is not None:
        return target_tag_id


def get_certificate(host, port=443, timeout=2):
    '''
    Pull a websites certificate
    :arg:
    :return: object - pem certificate
    '''
    context = ssl._create_unverified_context()
    conn = socket.setdefaulttimeout(2)
    conn = socket.create_connection((host, port))
    sock = context.wrap_socket(conn, server_hostname=host)
    try:
        der_cert = sock.getpeercert(True)
    finally:
        sock.close()
    return ssl.DER_cert_to_PEM_cert(der_cert)


def get_cert_components(der_cert):
    x509 = crypto.load_certificate(crypto.FILETYPE_PEM, der_cert)

    result = {
        'subject': dict(x509.get_subject().get_components()),
        'signature': x509.get_signature_algorithm(),
        'issuer': x509.get_issuer().get_components(),
        'serialNumber': x509.get_serial_number()
    }

    extensions = (x509.get_extension(i) for i in range(x509.get_extension_count()))

    try:
        extension_data = {e.get_short_name(): str(e) for e in extensions}
        result.update(extension_data)
    except:
        return result
    return result


def parse_data(url_dict, search_string):
    '''
    Parse the results of the scan, search for certificates that mach our 
    regex strings and return a list of matching IP's
    :arg: dict
    :return: list
    '''
    global IP_LIST_TO_ADD
    global IP_LIST_TO_REMOVE

    for key in url_dict:
        try:
            host_cn = str(url_dict[key]['subject'][b'CN'])
        except KeyError:
            continue
        try:
            host_san = str(url_dict[key][b'subjectAltName'])
        except KeyError:
            continue
        
        if re.search(search_string, host_cn):
            IP_LIST_TO_ADD.append(key)
        elif re.search(search_string, host_san):
            IP_LIST_TO_ADD.append(key)
        else:
            IP_LIST_TO_REMOVE.append(key)

    print(f'Updating {TARGET_TAG}...')
    #print(f'Adding the following Hosts: {IP_LIST_TO_ADD}')
    print(f'The following hosts were removed from hostgroup {TARGET_TAG}: {IP_LIST_TO_REMOVE}')


def update_tag(updated_list):
    '''
    Takes a list of freshly verified IP addresses and updates the given tag
    Clearing out no longer valid IPs
    :arg: list
    :arg: 
    :return:
    '''
    tagupdate.update_tag_with_removals(updated_list, api)
    return

if __name__ == '__main__':
    api = SnaAPISession()
    tagupdate = SnaTagAdd()
    
    SEARCH_STRING = ''  #This is the search string that we want to validate in the certificates we check
    TARGET_TAG = ''  # Tag to clean up
    TARGET_TAG_ID= '' 

    print(f'{Fore.LIGHTYELLOW_EX}-' * 80)
    print(f'Host Group Cleanup Script\n{Style.RESET_ALL}')
    try:
        api.sna_session_init('directscan-config.json')
    except Exception as e:
        print(e)

    # Arguments and Script Options
    helptext = (
        'Validates that IP\'s in a Hostgroup still belong to the intended organziation.  Works by grabbing a designated Hostgroup, and checking the site certificates CN and SAN fields for designated search strings. Example:\n\tSearchstring is *.site.com'
        )
    parser = argparse.ArgumentParser(description=helptext)

    parser.add_argument('-t', '--tag', type=str, required=True, help='Designated hostgroup to clean up.')
    parser.add_argument('-s', '--searchstring', type=str, required=True, help='Regex search string to match in site certificate')
    #parser.add_argument('-l', '--log', action='store_true', help='Add logfile')

    args = parser.parse_args()

    if args.tag:
        TARGET_TAG = args.tag
        print(f'Hostgroup set to {Fore.GREEN}{TARGET_TAG}{Style.RESET_ALL}')

    if TARGET_TAG == '':
        TARGET_TAG = input_target_tag()
    
    TARGET_TAG_ID = tagupdate.get_my_tag_id(TARGET_TAG, api.SNA_TAGS)

    # Quit program if selected hostgroup does not exist.
    if TARGET_TAG_ID == '':
        print(f'{Fore.LIGHTRED_EX}Hostgroup {TARGET_TAG} does not exist.\nHost group names are case sensitive.\nExiting.')
        print(f'{Fore.LIGHTYELLOW_EX}-' * 80)
        quit()
    
    url_dict = {}
    # Get Tag IP'/ranges
    url = api.BASE_URL + '/smc-configuration/rest/v1/tenants/' + api.SNA_TENANT + '/tags/' + str(TARGET_TAG_ID)
    tag_data = tagupdate.get_tag_data(url, api.API_SESSION)
    # Scan IP, add matchers to a list
    ip_list = tag_data['ranges']
    for ip in ip_list:

        try:
            # This section looks for defined IP ranges.
            # IP ranges will not be removed in this script
            if re.search('\/\d{1,2}$', ip) is None:
                print(f'{Fore.CYAN}Lookup up URL: {Fore.LIGHTGREEN_EX}{ip}{Style.RESET_ALL}')
                certificate = get_certificate(ip)
            else:
                IP_LIST_TO_ADD.append(ip)
        except socket.gaierror as e:
            print(f'{Fore.RED}Could not retrieve {ip}; Error\n{e}{Style.RESET_ALL}')
            IP_LIST_TO_REMOVE.append(ip)

        except socket.timeout as e:
            print(f'{Fore.LIGHTYELLOW_EX}{ip} has timed out.{Style.RESET_ALL}')
            IP_LIST_TO_REMOVE.append(ip)
            pass
        except Exception as e:
            print(f'{Fore.LIGHTRED_EX}Host {ip}\n{e}{Style.RESET_ALL}')
            IP_LIST_TO_REMOVE.append(ip)
            pass

        try:
            if certificate is not None:
                url_dict[ip] = get_cert_components(certificate)
                certificate = None
        except NameError:
            pass

    parse_data(url_dict, SEARCH_STRING)

    # add matchers to the tag
    update_tag(IP_LIST_TO_ADD)
    print(f'{Fore.LIGHTYELLOW_EX}-' * 80)
    quit()