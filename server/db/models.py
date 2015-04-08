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

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import MetaData
from sqlalchemy.orm import Session

# TODO(Gonéri): Load the value for a configuration file
engine = create_engine(os.environ['OPENSHIFT_POSTGRESQL_DB_URL'])

metadata = MetaData()

metadata.reflect(engine)

Base = automap_base(metadata=metadata)
Base.prepare()
Job = Base.classes.jobs
File = Base.classes.files
Environment = Base.classes.environments
Platform = Base.classes.platforms
Scenario = Base.classes.scenarios
Jobstate = Base.classes.jobstates
session = Session(engine)
