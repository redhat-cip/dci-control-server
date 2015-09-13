# -*- encoding: utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import bcrypt

import argparse
import os
import sys

import client


def _get_credentials():
    login = os.environ.get("DCI_LOGIN")
    password = os.environ.get("DCI_PASSWORD")
    dci_cs_url = os.environ['DCI_CS_URL']

    if dci_cs_url and login and password:
        return dci_cs_url, login, password
    else:
        print("Credentials missing:\n"
              "dci-cs-url '%s', login '%s', password '%s'" % (dci_cs_url,
                                                              login,
                                                              password))
        sys.exit(1)


def _init_args():
    parser = argparse.ArgumentParser(description='DCI cli.')
    command_subparser = parser.add_subparsers(help='commands',
                                              dest='command')
    # create user
    create_node_parser = command_subparser.add_parser(
        'create_user', help='create a user')
    create_node_parser.add_argument('username', action='store',
                                    help='the user name')
    create_node_parser.add_argument('password', action='store',
                                    help='the user password')

    # list users
    command_subparser.add_parser('list_users', help='list users')

    # delete user
    create_node_parser = command_subparser.add_parser(
        'delete_user', help='delete a user')
    create_node_parser.add_argument('username', action='store',
                                    help='the user name to delete')

    return parser.parse_args()


def main():
    args = _init_args()
    dci_cs_url, login, password = _get_credentials()
    dci_client = client.DCIClient(end_point=dci_cs_url, login=login,
                                  password=password)

    if args.command == 'create_user':
        password_hash = bcrypt.hashpw(args.password, bcrypt.gensalt())

        dci_client.post("/api/users", {"name": args.username,
                                       "password": password_hash})
        print("User '%s' created." % args.username)
    elif args.command == 'list_users':
        dci_users = dci_client.get("/api/users").json()
        for dci_user in dci_users["_items"]:
            print("    - %s" % dci_user["name"])
    elif args.command == 'delete_user':
        dci_user = dci_client.get("/api/users/%s" % args.username)
        if dci_user.status_code != 200:
            print("User '%s' does not exist." % args.username)
            sys.exit(1)
        dci_user = dci_user.json()
        print(dci_client.delete("/api/users/%s" % args.username,
                                etag=dci_user["etag"]).json())

if __name__ == '__main__':
    main()
