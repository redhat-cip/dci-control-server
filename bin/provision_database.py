#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Red Hat, Inc
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

from dci.db import models
from dci import dci_config
from init_database import main as init_db


def provision_db(engine):
    admin_team = dict(engine.execute(models.TEAMS.select().where(models.TEAMS.c.name == 'admin')).fetchone())
    teams = [
        {
            'id': '9396e0b6-190d-48cb-a3b3-f330247f6c03',
            'name': 'OpenStack',
            'parent_id': admin_team['id']
        },
        {
            'id': '9f9a7782-752f-4577-908a-88a1820ab4e5',
            'name': 'Ansible',
            'parent_id': admin_team['id']
        },
        {
            'id': '3ae3c802-d2be-42a9-9464-8a3253189757',
            'name': 'RHEL',
            'parent_id': admin_team['id']
        },
        {
            'id': '1dddf476-89f3-4a5a-ab13-99470b8eb941',
            'name': 'Dell',
            'parent_id': '9396e0b6-190d-48cb-a3b3-f330247f6c03'
        },
        {
            'id': '708a8292-7e7d-4ece-b516-dd3c6461150a',
            'name': 'HP',
            'parent_id': '9396e0b6-190d-48cb-a3b3-f330247f6c03'
        },
        {
            'id': '352abbc9-0d6c-41e7-abb6-d74af5351e63',
            'name': 'Cisco',
            'parent_id': '9f9a7782-752f-4577-908a-88a1820ab4e5'
        },
        {
            'id': '8606eb09-394f-40e0-82d0-f02c5c9f7ef1',
            'name': 'Veritas',
            'parent_id': '3ae3c802-d2be-42a9-9464-8a3253189757'
        },
    ]
    for team in teams:
        engine.execute(models.TEAMS.insert().values(**team))

    remotecis = [
        {
            'id': 'f4454189-698f-4bcc-8b73-b5366eee5400',
            'name': 'Remoteci openstack',
            'team_id': '9396e0b6-190d-48cb-a3b3-f330247f6c03'
        },
        {
            'id': 'e518489e-722e-4037-8bd8-5a62a4424673',
            'name': 'Remoteci ansible',
            'team_id': '9f9a7782-752f-4577-908a-88a1820ab4e5'
        },
        {
            'id': 'e85c6cd9-9e2e-4c18-8252-b3a2f0bb4d05',
            'name': 'Remoteci rhel',
            'team_id': '3ae3c802-d2be-42a9-9464-8a3253189757'
        },
        {
            'id': '63608c88-eca6-45fc-aa1c-0548512405f0',
            'name': 'Remoteci dell',
            'team_id': '1dddf476-89f3-4a5a-ab13-99470b8eb941'
        },
        {
            'id': 'de3cbd03-9af8-48a4-ae88-c95eb35cb741',
            'name': 'Remoteci hp',
            'team_id': '708a8292-7e7d-4ece-b516-dd3c6461150a'
        },
        {
            'id': 'abfbf11b-58d4-4eb5-a2bb-50f78975ec9d',
            'name': 'Remoteci cisco',
            'team_id': '352abbc9-0d6c-41e7-abb6-d74af5351e63'
        },
        {
            'id': '2bc7cc27-357f-4028-a7bb-720acc0901fc',
            'name': 'Remoteci veritas',
            'team_id': '8606eb09-394f-40e0-82d0-f02c5c9f7ef1'
        },
    ]

    for remoteci in remotecis:
        engine.execute(models.REMOTECIS.insert().values(**remoteci))

    roles = list(engine.execute(models.ROLES.select()).fetchall())
    roles = {dict(role)['name']: str(dict(role)['id']) for role in roles}

    users = [
        {
            'name': 'ansible_po',
            'role_id': roles['Product Owner'],
            'team_id': '9f9a7782-752f-4577-908a-88a1820ab4e5',
            'fullname': 'Ansible PO',
            'password': '$6$rounds=656000$ba7CMHSfOSJ94Zh.$NwCs43eYdPhNs9CuMezt3kTohHXq9W.FameK5/G7G6wBIEQV/C6bt3KNNHejP3F4JL79WHOGD93Mqa59V1CHa1',
            'email': 'ansible_po@example.org'
        },
        {
            'name': 'openstack_po',
            'role_id': roles['Product Owner'],
            'team_id': '9396e0b6-190d-48cb-a3b3-f330247f6c03',
            'fullname': 'OpenStack PO',
            'password': '$6$rounds=656000$IFz/d/Cpf45.qKbx$pm9TpaddZVCmsNRXOiCp9OvhZad0hpQ4XyWrj92WaLirD4I61abgHLj9mLVcIc86s02Y5oHpEuqsd60Sv84vQ1',
            'email': 'openstack_po@example.org'
        },
        {
            'name': 'rhel_po',
            'role_id': roles['Product Owner'],
            'team_id': '3ae3c802-d2be-42a9-9464-8a3253189757',
            'fullname': 'RHEL PO',
            'password': '$6$rounds=656000$lTflYTMj41ne8vef$r1YjwQnmB4a.Dd4u0JWzR/q4owkrt0uNuI1bCQuQjPiU.SHqYyx8LrjfD/k.FpFAgcHskWqFzOQ9SeE8tVRjd1',
            'email': 'rhel_po@example.org'
        },
        {
            'name': 'admin_cisco',
            'role_id': roles['Admin'],
            'team_id': '352abbc9-0d6c-41e7-abb6-d74af5351e63',
            'fullname': 'Admin Cisco',
            'password': '$6$rounds=656000$7JPDlsoVVwo8a/mz$ZAA5juyr7C65GxZvpJ1pyS9Cz9zqEhh7bXnTYykbQaY6J33sdA0yJ4OxTG5U6hXkKTADvmT5jJRJ0SpbzukMh.',
            'email': 'admin_cisco@example.org'
        },
        {
            'name': 'admin_hp',
            'role_id': roles['Admin'],
            'team_id': '708a8292-7e7d-4ece-b516-dd3c6461150a',
            'fullname': 'Admin HP',
            'password': '$6$rounds=656000$oGh/2FhjbhpaMyFp$rKcf9QTBa2WIVzdgc1IfmrzJ5feiKkKPcGKQX9/FakhiDpZsL9iYHSTsLlNwNphlLN2wjrcK.82VdONxuGc6u/',
            'email': 'admin_hp@example.org'
        },
        {
            'name': 'admin_dell',
            'role_id': roles['Admin'],
            'team_id': '1dddf476-89f3-4a5a-ab13-99470b8eb941',
            'fullname': 'Admin Dell',
            'password': '$6$rounds=656000$VqaSW7to.FQ8LK9q$6MfA9B4hrBekZlwTXnKWObjYADU3p2ilkm6tf5M4Smq8YEsMHIFjH18O6ny009CVgRI204xZ6C2QcVar73XCw/',
            'email': 'admin_dell@example.org'
        },
        {
            'name': 'user_cisco',
            'role_id': roles['User'],
            'team_id': '352abbc9-0d6c-41e7-abb6-d74af5351e63',
            'fullname': 'User Cisco',
            'password': '$6$rounds=656000$htQcbQB3WYyTrvc4$zNzn4u6AF80Rdzw4.SyDEaG3N60f4UxDQm1n.iFkMXpKh2VEZXOs9WLmsgwofhSnrrYbAdxruD9SfQzdGvt3i/',
            'email': 'user_cisco@example.org'
        },
        {
            'name': 'user_hp',
            'role_id': roles['User'],
            'team_id': '708a8292-7e7d-4ece-b516-dd3c6461150a',
            'fullname': 'User HP',
            'password': '$6$rounds=656000$eizh7DnxD/4Mglg4$S8KHQ0ktfQOoEU/6b2.iZe44AbOLkZp6Kk9BEdk5ka/X1fnhcixeWeOFd2YNmaD2JCPNHdXTQO3D1En34g3Oh0',
            'email': 'user_hp@example.org'
        },
        {
            'name': 'user_dell',
            'role_id': roles['User'],
            'team_id': '1dddf476-89f3-4a5a-ab13-99470b8eb941',
            'fullname': 'User Dell',
            'password': '$6$rounds=656000$O.SyyWK5Jt3lbdpK$ccGePPlPXLC/OWCBIYofmqXxPH8crNFSFgAdA7x0uL5tIvMAdk2sT0HJ7iv65pFGObR/tVFVAq65ONHmM8Sdj.',
            'email': 'user_dell@example.org'
        },
        {
            'name': 'admin_veritas',
            'role_id': roles['Admin'],
            'team_id': '8606eb09-394f-40e0-82d0-f02c5c9f7ef1',
            'fullname': 'Admin Veritas',
            'password': '$6$rounds=656000$EIN.1QcJizcg6bL8$mNog7SGDXmp1WwtOGHv7r7a9.swfVJcE15cnvUJLVzd7lDMu78hnsiUblU5U2Kjs.f6o5aMEWNmSk5ZY.EDei0',
            'email': 'admin_veritas@example.org'
        },
        {
            'name': 'user_veritas',
            'role_id': roles['User'],
            'team_id': '8606eb09-394f-40e0-82d0-f02c5c9f7ef1',
            'fullname': 'User Veritas',
            'password': '$6$rounds=656000$Iwd6qSNE1PIn2Si4$aMlv2ie3.lbSJXmXuAw9/UvJgzXrOCLupa4oUcBrUlqHnGpvRgkYYhu/dfQuSOJsfb6GEX5XjutfYIJkmPB7L1',
            'email': 'user_veritas@example.org'
        }
    ]
    for user in users:
        engine.execute(models.USERS.insert().values(**user))

    products = [
        {
            'id': '1ceb6cef-b8f4-4999-90c0-1c1de76330df',
            'name': 'OpenStack',
            'label': 'OPENSTACK'.upper(),
            'description': 'description for OpenStack',
            'team_id': '9396e0b6-190d-48cb-a3b3-f330247f6c03'
        },
        {
            'id': 'de422eb1-c9bf-40ce-b5d3-f3659c210389',
            'name': 'Ansible',
            'label': 'ANSIBLE'.upper(),
            'description': 'description for Ansible',
            'team_id': '9f9a7782-752f-4577-908a-88a1820ab4e5'
        },
        {
            'id': 'f4454189-698f-4bcc-8b73-b5366eee5400',
            'name': 'RHEL',
            'label': 'RHEL'.upper(),
            'description': 'description for RHEL',
            'team_id': '3ae3c802-d2be-42a9-9464-8a3253189757'
        }

    ]
    for product in products:
        engine.execute(models.PRODUCTS.insert().values(**product))

    topics = [
        {
            'id': '1ceb6cef-b8f4-4999-90c0-1c1de76330df',
            'name': 'OSP12',
            'component_types': ['puddle'],
            'product_id': '1ceb6cef-b8f4-4999-90c0-1c1de76330df'
        },
        {
            'id': 'ed8ba77f-518d-42f5-806a-4c8721c2ab06',
            'name': 'OSP11',
            'component_types': ['puddle'],
            'product_id': '1ceb6cef-b8f4-4999-90c0-1c1de76330df',
            'next_topic_id': '1ceb6cef-b8f4-4999-90c0-1c1de76330df'
        },
        {
            'id': '753874b2-942b-45bc-9720-db66d439c40e',
            'name': 'OSP10',
            'component_types': ['puddle'],
            'product_id': '1ceb6cef-b8f4-4999-90c0-1c1de76330df',
            'next_topic_id': 'ed8ba77f-518d-42f5-806a-4c8721c2ab06'
        },
        {
            'id': 'ae974e18-a5b8-4068-9ae9-10e0044ca6b0',
            'name': 'ansible-devel',
            'component_types': ['snapshot_ansible'],
            'product_id': 'de422eb1-c9bf-40ce-b5d3-f3659c210389'
        },
        {
            'id': 'e5dcec7d-5184-4d38-bfd9-e241b0be0a41',
            'name': 'ansible-2.4',
            'component_types': ['snapshot_ansible'],
            'product_id': 'de422eb1-c9bf-40ce-b5d3-f3659c210389',
            'next_topic_id': 'ae974e18-a5b8-4068-9ae9-10e0044ca6b0'
        },
        {
            'id': '99ccee6a-d544-4d81-8177-4c87c87e4216',
            'name': 'RHEL-8',
            'component_types': ['Compose'],
            'product_id': 'f4454189-698f-4bcc-8b73-b5366eee5400'
        },
        {
            'id': '017d161f-6c92-4873-99fa-34662a2c81f5',
            'name': 'RHEL-7',
            'component_types': ['Compose'],
            'product_id': 'f4454189-698f-4bcc-8b73-b5366eee5400',
            'next_topic_id': '99ccee6a-d544-4d81-8177-4c87c87e4216'
        },
    ]
    for topic in topics:
        engine.execute(models.TOPICS.insert().values(**topic))

    topics_teams = [
        # OSP 12 11 10 <-> Team OpenStack
        {'topic_id': '1ceb6cef-b8f4-4999-90c0-1c1de76330df', 'team_id': '9396e0b6-190d-48cb-a3b3-f330247f6c03'},
        {'topic_id': 'ed8ba77f-518d-42f5-806a-4c8721c2ab06', 'team_id': '9396e0b6-190d-48cb-a3b3-f330247f6c03'},
        {'topic_id': '753874b2-942b-45bc-9720-db66d439c40e', 'team_id': '9396e0b6-190d-48cb-a3b3-f330247f6c03'},
        # OSP 12 11 10 <-> Team Dell
        {'topic_id': '1ceb6cef-b8f4-4999-90c0-1c1de76330df', 'team_id': '1dddf476-89f3-4a5a-ab13-99470b8eb941'},
        {'topic_id': 'ed8ba77f-518d-42f5-806a-4c8721c2ab06', 'team_id': '1dddf476-89f3-4a5a-ab13-99470b8eb941'},
        {'topic_id': '753874b2-942b-45bc-9720-db66d439c40e', 'team_id': '1dddf476-89f3-4a5a-ab13-99470b8eb941'},
        # OSP 10 <-> Team HP
        {'topic_id': '753874b2-942b-45bc-9720-db66d439c40e', 'team_id': '708a8292-7e7d-4ece-b516-dd3c6461150a'},
        # Ansible devel 2.4 <-> Team Ansible
        {'topic_id': 'ae974e18-a5b8-4068-9ae9-10e0044ca6b0', 'team_id': '9f9a7782-752f-4577-908a-88a1820ab4e5'},
        {'topic_id': 'e5dcec7d-5184-4d38-bfd9-e241b0be0a41', 'team_id': '9f9a7782-752f-4577-908a-88a1820ab4e5'},
        # Ansible 2.4 <-> Team Cisco
        {'topic_id': 'e5dcec7d-5184-4d38-bfd9-e241b0be0a41', 'team_id': '352abbc9-0d6c-41e7-abb6-d74af5351e63'},
        # RHEL 8 7 <-> Team RHEL
        {'topic_id': '99ccee6a-d544-4d81-8177-4c87c87e4216', 'team_id': '3ae3c802-d2be-42a9-9464-8a3253189757'},
        {'topic_id': '017d161f-6c92-4873-99fa-34662a2c81f5', 'team_id': '3ae3c802-d2be-42a9-9464-8a3253189757'},
        # RHEL 7 <-> Team Veritas
        {'topic_id': '017d161f-6c92-4873-99fa-34662a2c81f5', 'team_id': '8606eb09-394f-40e0-82d0-f02c5c9f7ef1'},
    ]
    for topic_team in topics_teams:
        engine.execute(models.JOINS_TOPICS_TEAMS.insert().values(**topic_team))

    components = [
        {
            'id': 'fcfa0d37-7521-4ead-aa9e-b2b4aec04119',
            'name': 'RH7-RHOS-10.0 2016-10-28.1',
            'type': 'puddle',
            'topic_id': '753874b2-942b-45bc-9720-db66d439c40e',
            'export_control': True
        },
        {
            'id': '18216443-1bd0-4195-badf-36d9a57446ca',
            'name': 'RH7-RHOS-10.0 2016-11-12.1',
            'type': 'puddle',
            'topic_id': '753874b2-942b-45bc-9720-db66d439c40e',
            'export_control': True
        },
        {
            'id': 'de422eb1-c9bf-40ce-b5d3-f3659c210389',
            'name': 'RH7-RHOS-11.0 2016-11-11.1',
            'type': 'puddle',
            'topic_id': 'ed8ba77f-518d-42f5-806a-4c8721c2ab06',
            'export_control': True
        },
        {
            'id': '3f4ff66b-0d64-42db-9939-f004c02312cc',
            'name': 'RH7-RHOS-12.0 2016-11-12.1',
            'type': 'puddle',
            'topic_id': '1ceb6cef-b8f4-4999-90c0-1c1de76330df',
            'export_control': True
        },
        {
            'id': '22fbac0e-6ed7-4311-8c9c-3547e446abf9',
            'name': 'Ansible devel',
            'type': 'snapshot_ansible',
            'topic_id': 'ae974e18-a5b8-4068-9ae9-10e0044ca6b0',
            'export_control': True
        },
        {
            'id': '047885b3-3e52-4e0f-b947-ed21ea69313e',
            'name': 'Ansible 2.4',
            'type': 'snapshot_ansible',
            'topic_id': 'e5dcec7d-5184-4d38-bfd9-e241b0be0a41',
            'export_control': True
        },
        {
            'id': '3dd47bf7-5f2e-498d-a0b7-10ab4a97443f',
            'name': 'RHEL-7.6-20180513.n.0',
            'type': 'Compose',
            'topic_id': '017d161f-6c92-4873-99fa-34662a2c81f5',
            'export_control': True
        },
        {
            'id': '656b8151-b24d-4049-a343-1a15849fc2b3',
            'name': 'RHEL-8.0-20180503.n.2',
            'type': 'Compose',
            'topic_id': '99ccee6a-d544-4d81-8177-4c87c87e4216',
            'export_control': True
        },
    ]
    for component in components:
        engine.execute(models.COMPONENTS.insert().values(**component))

    jobs = [
        {
            'id': 'c8fb99a4-d41b-44af-9cec-cd5094c36021',
            'remoteci_id': '63608c88-eca6-45fc-aa1c-0548512405f0',
            'status': 'error',
            'team_id': '1dddf476-89f3-4a5a-ab13-99470b8eb941',
            'topic_id': '753874b2-942b-45bc-9720-db66d439c40e',
            'created_at': '2018-07-15T06:31:02.000000',
            'updated_at': '2018-07-15T06:36:03.000000'

        },
        {
            'id': 'dffc397a-ae48-4dbd-8922-499e3c0786b1',
            'remoteci_id': '63608c88-eca6-45fc-aa1c-0548512405f0',
            'status': 'failure',
            'team_id': '1dddf476-89f3-4a5a-ab13-99470b8eb941',
            'topic_id': '753874b2-942b-45bc-9720-db66d439c40e',
            'created_at': '2018-07-17T10:05:03.000000',
            'updated_at': '2018-07-17T12:40:32.000000'
        },
        {
            'id': 'f182a8bc-bf50-4abf-91bc-a8f96987d6f8',
            'remoteci_id': '63608c88-eca6-45fc-aa1c-0548512405f0',
            'status': 'success',
            'team_id': '1dddf476-89f3-4a5a-ab13-99470b8eb941',
            'topic_id': '753874b2-942b-45bc-9720-db66d439c40e',
            'created_at': '2018-07-17T12:50:15.000000',
            'updated_at': '2018-07-17T16:26:06.000000'
        },
        {
            'id': '89d41663-8935-4ab2-9391-6844d27bd7b7',
            'remoteci_id': '63608c88-eca6-45fc-aa1c-0548512405f0',
            'status': 'running',
            'team_id': '1dddf476-89f3-4a5a-ab13-99470b8eb941',
            'topic_id': 'ed8ba77f-518d-42f5-806a-4c8721c2ab06',
            'created_at': '2018-07-17T12:50:15.000000',
            'updated_at': '2018-07-17T12:50:15.000000'
        },
        {
            'id': 'b6b5873e-4604-49eb-a41b-0d9311f17627',
            'remoteci_id': '63608c88-eca6-45fc-aa1c-0548512405f0',
            'status': 'success',
            'team_id': '1dddf476-89f3-4a5a-ab13-99470b8eb941',
            'topic_id': '1ceb6cef-b8f4-4999-90c0-1c1de76330df',
            'created_at': '2018-07-17T20:53:15.000000',
            'updated_at': '2018-07-17T22:43:06.000000'
        },
    ]

    for job in jobs:
        engine.execute(models.JOBS.insert().values(**job))

    jobs_components = [
        {'job_id': 'c8fb99a4-d41b-44af-9cec-cd5094c36021', 'component_id': 'fcfa0d37-7521-4ead-aa9e-b2b4aec04119'},
        {'job_id': 'dffc397a-ae48-4dbd-8922-499e3c0786b1', 'component_id': '18216443-1bd0-4195-badf-36d9a57446ca'},
        {'job_id': 'f182a8bc-bf50-4abf-91bc-a8f96987d6f8', 'component_id': '18216443-1bd0-4195-badf-36d9a57446ca'},
        {'job_id': '89d41663-8935-4ab2-9391-6844d27bd7b7', 'component_id': 'de422eb1-c9bf-40ce-b5d3-f3659c210389'},
        {'job_id': 'b6b5873e-4604-49eb-a41b-0d9311f17627', 'component_id': '3f4ff66b-0d64-42db-9939-f004c02312cc'},
    ]

    for job_component in jobs_components:
        engine.execute(models.JOIN_JOBS_COMPONENTS.insert().values(**job_component))

    jobs_states = [
        {'job_id': 'c8fb99a4-d41b-44af-9cec-cd5094c36021', 'team_id': '1dddf476-89f3-4a5a-ab13-99470b8eb941',
         'status': 'new', 'created_at': '2018-07-15T06:31:02.000000'},
        {'job_id': 'c8fb99a4-d41b-44af-9cec-cd5094c36021', 'team_id': '1dddf476-89f3-4a5a-ab13-99470b8eb941',
         'status': 'error', 'created_at': '2018-07-15T06:36:03.000000'},
    ]

    for job_state in jobs_states:
        engine.execute(models.JOBSTATES.insert().values(**job_state))


def empty_database(engine):
    for table in reversed(models.metadata.sorted_tables):
        engine.execute(table.delete())


if __name__ == '__main__':
    conf = dci_config.generate_conf()
    engine = dci_config.get_engine(conf).connect()
    empty_database(engine)
    init_db(conf)
    provision_db(engine)
