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

import os
import swiftclient


class File(stores.Store):

    def __init__(self, conf):
        self.path = conf['path']
        self.container = conf['container']

    def delete(self, filename):
        try:
            os.remove("%s/%s/%s" % (self.path, self.container, filename))
        except:
            raise exceptions.StoreExceptions('An error occured while '
                                             'deleting %s' % filename)

    def get(self, filename):
        file_path = "%s/%s/%s" % (self.path, self.container, filename)
        chunk_size = 1024 ** 2
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size) or None, None):
                yield chunk

    def head(self, filename):
        file_path = "%s/%s/%s" % (self.path, self.container, filename)
        file_size = os.path.getsize(file_path)
        return {'content-length': file_size}

    def upload(self, filename, iterable, pseudo_folder=None,
               create_container=True):
        os.makedirs(os.path.join(self.path, self.container, filename))
        file_path = "%s/%s/%s" % (self.path, self.container, filename)

        with open(file_path, 'wb') as f:
            chunk_size = 4096
            for chunk in iter(lambda: iterable(chunk_size) or None, None):
                f.write(chunk)
