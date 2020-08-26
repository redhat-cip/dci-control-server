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
from __future__ import unicode_literals


class DCIException(Exception):
    def __init__(self, message, payload=None, status_code=400):
        super(DCIException, self).__init__()
        self.status_code = status_code
        self.message = message
        self.payload = payload

    def to_dict(self):
        return {
            "status_code": self.status_code,
            "message": self.message,
            "payload": self.payload or {},
        }

    def __str__(self):
        return str(self.to_dict())


class DCIConflict(DCIException):
    def __init__(self, resource_name, resource_value):
        msg = 'conflict on %s "%s" or etag not matched' % (
            resource_name,
            resource_value,
        )
        super(DCIConflict, self).__init__(msg, status_code=409)


class DCIDeleteConflict(DCIException):
    def __init__(self, resource_name, resource_value):
        msg = '%s "%s" already deleted or etag not matched.' % (
            resource_name,
            resource_value,
        )
        super(DCIDeleteConflict, self).__init__(msg, status_code=400)


class DCINotFound(DCIException):
    def __init__(self, resource_name, resource_value):
        msg = '%s "%s" not found.' % (resource_name, resource_value)
        super(DCINotFound, self).__init__(msg, status_code=404)


class DCICreationConflict(DCIException):
    def __init__(self, resource_name, field_name):
        msg = "conflict on %s" % resource_name
        payload = {"error": {field_name: "already_exists"}}
        super(DCICreationConflict, self).__init__(msg, payload, 409)


class StoreExceptions(DCIException):
    def __init__(self, message, status_code=400):
        super(StoreExceptions, self).__init__(message, status_code=status_code)


class Unauthorized(DCIException):
    def __init__(self):
        msg = "Operation not authorized."
        super(Unauthorized, self).__init__(msg, status_code=401)


class Forbidden(DCIException):
    def __init__(self):
        msg = "Operation forbidden."
        super(Forbidden, self).__init__(msg, status_code=403)
