#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Red Hat, Inc
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

from sqlalchemy.ext.declarative import declarative_base
from dci.db import models

Base = declarative_base()


class Role(Base):
    __table__ = models.ROLES


class Team(Base):
    __table__ = models.TEAMS


class User(Base):
    __table__ = models.USERS


class Product(Base):
    __table__ = models.PRODUCTS


class Topic(Base):
    __table__ = models.TOPICS
