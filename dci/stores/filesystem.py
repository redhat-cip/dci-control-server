# -*- coding: utf-8 -*-
#
# Copyright (C) Red Hat, Inc
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

from dci import stores
from dci.common import exceptions
from dci.stores import files_utils

import logging
import os
import errno

logger = logging.getLogger(__name__)


class FileSystem(stores.Store):
    def __init__(self, conf):
        super(FileSystem, self).__init__(conf)
        self.path = conf["path"]
        self.container = conf["container"]
        self._root_directory = os.path.join(self.path, self.container)

    def delete(self, filename):
        file_path = os.path.join(self._root_directory, filename)
        try:
            os.remove(file_path)
        except OSError as e:
            status_code = 400
            if e.errno == errno.ENOENT:
                logger.warn("file %s not found in local filesystem" % file_path)
                return
            raise exceptions.StoreExceptions(
                "Error while deleting file " "%s: %s" % (filename, str(e)),
                status_code=status_code,
            )

    def get(self, filename):
        file_path = os.path.join(self._root_directory, filename)
        try:
            return ([], open(file_path, "r"))
        except IOError as e:
            status_code = 400
            if e.errno == errno.ENOENT:
                status_code = 404
            raise exceptions.StoreExceptions(
                "Error while accessing file " "%s: %s" % (filename, str(e)),
                status_code=status_code,
            )

    def head(self, filename):
        file_path = os.path.join(self._root_directory, filename)
        try:
            file_size = os.path.getsize(file_path)
        except IOError as e:
            status_code = 400
            if e.errno == errno.ENOENT:
                status_code = 404
            raise exceptions.StoreExceptions(
                "Error while accessing file " "%s: %s" % (filename, str(e)),
                status_code=status_code,
            )
        md5 = files_utils.md5Checksum(file_path)
        return {
            "content-length": file_size,
            "etag": md5,
            "content-type": "application/octet-stream",
        }

    def upload(self, filename, iterable, pseudo_folder=None, create_container=True):
        file_path = os.path.join(self._root_directory, filename)
        path = os.path.dirname(file_path)
        if not os.path.exists(path):
            os.makedirs(path)

        with open(file_path, "wb") as f:
            if hasattr(iterable, "read"):
                while True:
                    data = iterable.read(1024)
                    if not data:
                        break
                    f.write(data)
            else:
                f.write(iterable)
