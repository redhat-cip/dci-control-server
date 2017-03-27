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


class Store(object):

    def __init__(self, conf):
        pass

    def delete(self):
        pass

    def get(self):
        pass

    def list(self):
        pass

    def upload(self):
        pass

    def build_file_path(self, root, middle, file_id):
        root = str(root)
        middle = str(middle)
        file_id = str(file_id)
        return "%s/%s/%s" % (root, middle, file_id)
