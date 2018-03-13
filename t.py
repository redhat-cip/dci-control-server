import base64
from xmlrpclib import ServerProxy

with open('tests/data/certification.xml.tar.gz', 'rb') as f:
    
    proxy = ServerProxy('https://access.stage.redhat.com/hydra/rest/cwe/xmlrpc/v2')

    certification_details=proxy.Cert.getOpenStack_4_7({
        'username': 'cwetestuser',
        'password': 'redhat',
        'certification_id': '1775'
    })
    c = {
        'username': 'cwetestuser',
        'password': 'redhat',
        'id': certification_details['cert_nid'],
        'type': 'certification',
        'data': base64.b64encode(f.read()),
        'description': 'DCI automatic upload test log',
        'filename': 'certification.xml.tar.gz'
    }
    r=proxy.Cert.uploadTestLog(c)
    print(r)
