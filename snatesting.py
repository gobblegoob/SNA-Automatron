from SnaAPISession import SnaAPISession
from SnaQuery import SnaQuery

if __name__ == '__main__':
    api = SnaAPISession()
    query = SnaQuery()


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
    query.run_flow_query(api)

    quit()