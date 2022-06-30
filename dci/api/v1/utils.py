# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import datetime
from OpenSSL import crypto

from dci.common import utils
from dci.db import models2


def createKeyPair(type=crypto.TYPE_RSA, bits=2048):
    """
    Create a public/private key pair.
    Arguments: type - Key type, must be one of TYPE_RSA and TYPE_DSA
               bits - Number of bits to use in the key
    Returns:   The public/private key pair in a PKey object
    """
    pkey = crypto.PKey()
    pkey.generate_key(type, bits)
    return pkey


def createCertRequest(pkey, digest="sha256"):
    """
    Create a certificate request.
    Arguments: pkey   - The key to associate with the request
               digest - Digestion method to use for signing, default is sha256
               **name - The name of the subject of the request, possible
                        arguments are:
                          C     - Country name
                          ST    - State or province name
                          L     - Locality name
                          O     - Organization name
                          OU    - Organizational unit name
                          CN    - Common name
                          emailAddress - E-mail address
    Returns:   The certificate request in an X509Req object
    """
    req = crypto.X509Req()

    req.get_subject().C = "FR"
    req.get_subject().ST = "IDF"
    req.get_subject().L = "Paris"
    req.get_subject().O = "RedHat"  # noqa
    req.get_subject().OU = "DCI"
    req.get_subject().CN = "DCI-remoteCI"

    req.set_pubkey(pkey)
    req.sign(pkey, digest)
    return req


def get_key_and_cert_signed(pkey_path, cert_path, digest="sha256"):
    key = createKeyPair()
    csr = createCertRequest(key)
    CAprivatekey = crypto.load_privatekey(
        crypto.FILETYPE_PEM, open(pkey_path, "rb").read()
    )
    caCert = crypto.load_certificate(crypto.FILETYPE_PEM, open(cert_path, "rb").read())

    cert = crypto.X509()
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
    cert.set_issuer(caCert.get_subject())
    cert.set_subject(csr.get_subject())
    cert.set_pubkey(csr.get_pubkey())
    cert.sign(CAprivatekey, digest)

    return key, cert


def user_topic_ids(session, user):
    """Retrieve the list of topics IDs a user has access to."""
    if (
        user.is_super_admin()
        or user.is_read_only_user()
        or user.is_epm()
        or user.is_feeder()
    ):
        query = session.query(models2.Topic.id)
    else:
        query = (
            session.query(models2.Topic.id)
            .join(models2.Topic.teams)
            .filter(models2.Team.state != "archived")
            .filter(models2.Team.id.in_(user.teams_ids))
        )
    return [str(t.id) for t in query.all()]


def common_values_dict():
    """Build a basic values object used in every create method.

    All our resources contain a same subset of value. Instead of
    redoing this code everytime, this method ensures it is done only at
    one place.
    """
    now = datetime.datetime.utcnow().isoformat()
    etag = utils.gen_etag()
    values = {
        "id": utils.gen_uuid(),
        "created_at": now,
        "updated_at": now,
        "etag": etag,
    }

    return values
