[1] First export the DCI environment variables:

     $ export DCI_CS_URL='http://127.0.0.1'
     $ export DCI_LOGIN='admin'
     $ export DCI_PASSWORD='password'

[2] The user must be a super admin user of dci control server.

[3] Then run the script:

     $ ./gstatus.py

[4] The script could use a json file to filter which result to print or not:

     $ ./gstatus.py ./filter.json

[5] The json file must looks like something like the following:

{
"black_teams": ["dsavinea", "yaya", "test", "goneri", "spredzy"],
"white_topics": ["RDO-Ocata","RDO-Newton"]
}

- The 'black_teams' is a list which correspond to the teams that we don't want
to print their corresponding remoteci results.

- The 'white_topics' is a list of topics that we don't want to filter the
teams on them.
