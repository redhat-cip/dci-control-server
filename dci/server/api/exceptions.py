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


class DciError(Exception):
    """DCI base exception."""
    _STATUS_CODE = 400

    def __init__(self, message, status_code=None):
        super(Exception, self).__init__(self)
        self._error = {'_error': {'code': self._STATUS_CODE,
                                  'message': message}}
        self.status_code = self._STATUS_CODE
        if status_code is not None:
            self.status_code = status_code
            self._error['_error']['code'] = status_code

    def get_error(self):
        return self._error


class InvalidAPIUsage(DciError):
    """Invalid api usage exception."""
    _STATUS_CODE = 422

    def __init__(self, *args, **kwargs):
        super(InvalidAPIUsage, self).__init__(*args, **kwargs)


class NotFound(DciError):
    """Not found exception."""
    _STATUS_CODE = 404

    def __init__(self, *args, **kwargs):
        super(NotFound, self).__init__(*args, **kwargs)


class InternalError(DciError):
    """Internal Error."""
    _STATUS_CODE = 500

    def __init__(self, *args, **kwargs):
        super(InternalError, self).__init__(*args, **kwargs)


class ConflictError(DciError):
    """Conflict Error."""
    _STATUS_CODE = 409

    def __init__(self, *args, **kwargs):
        super(ConflictError, self).__init__(*args, **kwargs)
