# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
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

import os
import re

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import MetaData
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session

# TODO(Gonéri): Load the value for a configuration file
engine = create_engine(os.environ.get(
    'OPENSHIFT_POSTGRESQL_DB_URL',
    'postgresql://boa:boa@127.0.0.1:5432/dci_control_server'))

metadata = MetaData()

metadata.reflect(engine)

for table in metadata.tables:
    print(table)

Base = automap_base(metadata=metadata)
Base.prepare()
Job = Base.classes.jobs
File = Base.classes.files
Notification = Base.classes.notifications
Product = Base.classes.products
Remoteci = Base.classes.remotecis
Test = Base.classes.tests
Jobstate = Base.classes.jobstates
Version = Base.classes.versions
TestVersion = Base.classes.testversions
session = Session(engine)

# engine.echo = True

# NOTE(Gonéri): Create the foreign table attribue to be able to
# do job.remoteci.name
for table in metadata.tables:
    cur_db = getattr(Base.classes, table)
    for column in cur_db.__table__.columns:
        m = re.search(r"\.(\w+)_id$", str(column))
        if not m:
            continue
        foreign_table_name = m.group(1)
        foreign_table_object = getattr(Base.classes, foreign_table_name + 's')
        remote_side = None
        remote_side = [foreign_table_object.id]
        setattr(cur_db, foreign_table_name, relationship(
            foreign_table_object, uselist=False, remote_side=remote_side))

setattr(Product, 'versions', relationship(
    Version, uselist=True, lazy='dynamic'))
setattr(Version, 'notifications', relationship(
    Notification, uselist=True, lazy='dynamic'))
