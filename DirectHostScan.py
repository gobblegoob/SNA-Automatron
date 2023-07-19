'''
    Directly queries websites for their certificates
    The certificate CN and SAN fields are used to identify
    external hosts that are connected to by local hosts.
'''

from SnaAPISession import SnaAPISession
from SnaQuery import SnaQuery
from SnaTagAdd import SnaTagAdd
from OpenSSL import crypto
import ssl, socket
from colorama import Fore, Style
import re
import pprint
import json

undesignated_hosts = [] # A list of hosts and host data that is not assigned to a designated hostgroup

def get_certificate(host, port=443, timeout=2):
    # Need to use an unverified context.
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

def peer_ip_list(query_results):
    '''
    Send a flow query result, return a deduplicated list of IP addresses of peers
    :arg: dict
    :return: list
    '''
    peer_ip_list = []
    my_dict = {}
    for key in query_results:
        my_dict[key["peer"]["ipAddress"]] = ''
    
    for i in my_dict:
        peer_ip_list.append(i)
    
    return peer_ip_list


def print_results(url_dict):
    '''
    Neatly prints your URL dictionary of results.
    :arg: dict
    :return:
    '''
    for key in url_dict:
        print(f' Host: {key}')
        print(url_dict[key]['subject'][b'CN'])
        print(url_dict[key][b'subjectAltName'])
        print(url_dict[key]['serialNumber'])
        print('=' * 80)
    return


def parse_data(url_dict):
    '''
    Parses the data in the url dict and updates hosts.  Updates the tags 
    :arg: dictionary
    :return:
    '''
    tags = SnaTagAdd()
    global undesignated_hosts

    for hg in search_data:
        tags.get_my_tag_id(hg, api.SNA_TAGS)
        ip_list = []
        for host in url_dict:
            try:
                host_cn = str(url_dict[host]['subject'][b'CN'])
                host_san = str(url_dict[host][b'subjectAltName'])
                #print(f'{host_cn} is a {type(host_cn)}')
                #print(f'{host_san} is a {type(host_san)}')
            except KeyError as e:
                undesignated_hosts.append(
                    {
                        'host': host,
                        'error': e
                    }
                )
                continue

            if re.search(search_data[hg]['url'], host):
                print(f'Add host {host} to hostgroup {hg}')
                ip_list.append(host)
                continue
            elif re.search(search_data[hg]['search_string'], host_cn):
                print(f'Cert CN Match! Add {host} to hostgroup {hg}')
                ip_list.append(host)
                continue
            elif re.search(search_data[hg]['search_string'], host_san):
                print(f'Cert SAN match! Add {host} to hostgroup {hg}')
                ip_list.append(host)
                continue
            else: 
                undesignated_hosts.append(
                    {
                        'host': host,
                        'host_cn': host_cn,
                        'host_san': host_san
                    }
                )
                continue
        # update the tags
        print(f'Updating {hg} with {ip_list.__len__()} values...')
        tags.update_tags(ip_list, api)
    return


def excel_report():
    '''
    Print a report of a series of hosts to an outlook file for review
    :arg:
    :return:
    '''
    return

if __name__ == '__main__':
    # Hostgroups and search strings
    search_data = {
        'Dynamic Ring IPs': {
            'url': 'ring.com',
            'search_string': 'ring.devices'
        },
        'Webex': {
            'url': 'webex.com',
            'search_string': 'webex'
        },
        'FlexnetOperations': {
            'url': 'flexnetoperations.barf',
            'search_string': 'Flexera.Software'
        },
        'Duo Security': {
            'url': 'duosecurity.com',
            'search_string': 'duosecurity'
        },
        'Trusted Internet Hosts': {
            'url': 'code42.com',
            'search_string': 'code42.com'
        }
    }
    
    # initialize classes
    api = SnaAPISession()
    query = SnaQuery()
    
    try:
        api.sna_session_init('directscan-config.json')
    except Exception as e:
        print(e)

    # I need to create a custom query for this - 
    query.set_sna_json('directscan-config.json')
    query.FLOW_QUERY_FILE = 'directscan-flowquery.json'
    query.QUERY_NAME = 'Direct Scan Flow Query'
    query.QUERY_TIME = 500 # Query time in minutes
    query.init_query(api.SNA_TAGS)
    

    query_results = query.run_flow_query(api)
    peer_list = peer_ip_list(query_results)

    url_dict = {}
  

    for i in peer_list:
        try:
            print(f'{Fore.CYAN}Looking up URL: {Fore.LIGHTGREEN_EX}{i}{Style.RESET_ALL}')
            certificate = get_certificate(i)
        except socket.gaierror as e:
            print(f'{Fore.RED}Could not retrieve {i}; Error\n{e}{Style.RESET_ALL}')

        except socket.timeout as e:
            print(f'{Fore.LIGHTYELLOW_EX}{i} has timed out.{Style.RESET_ALL}')
            pass
        except Exception as e: 
            print(f'{Fore.LIGHTRED_EX}Host {i}{e}{Style.RESET_ALL}')
            
            pass
        
        try:
            if certificate is not None:
                url_dict[i] = get_cert_components(certificate)
                certificate = None
        except NameError:
            pass
    

    parse_data(url_dict)
    # print_results(url_dict)
    print('=-' * 80)
    #pprint.pprint(undesignated_hosts)
    f = open("results.txt", "w")
    for i in undesignated_hosts:
        tab = ''
        for key in i:
            stuff = f'{key} {i[key]}\n{tab}'
            f.write(stuff)
            tab = '\t'
            #print(i[key])
        

    f.close()
    print('=-' * 80)
    quit()