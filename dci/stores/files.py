# Copyright 2016 Yanis Guenane <yguenane@redhat.com>
# Author: Yanis Guenane <yguenane@redhat.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dci import stores
from dci.common import exceptions
from dci.stores import files_utils

import os


class File(stores.Store):

    def __init__(self, conf):
        self.path = conf['path']
        self.container = conf['container']

    def _file_path(filename):
        return '%s/%s/%s' % (self.path, self.container, filename)

    def delete(self, filename):
        try:
            os.remove(_file_path(filename))
        except:
            raise exceptions.StoreExceptions('An error occured while '
                                             'deleting %s' % filename)

    def get(self, filename):
        return ([], open(_file_path(filename)))

    def head(self, filename):
        file_size = os.path.getsize(_file_path(filename))
        md5 = files_utils.md5Checksum(_file_path(filename))
        return {'content-length': file_size, 'etag': md5,
                'content-type': 'test'}

    def upload(self, filename, iterable, pseudo_folder=None,
               create_container=True):
        path = os.path.join(self.path, self.container,
                            os.path.dirname(filename))
        if not os.path.exists(path):
            os.makedirs(path)

        with open(_file_path(filename), 'wb') as f:
            for lines in iterable.readlines():
                f.write(lines)
