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


import logging
import hashlib

logger = logging.getLogger(__name__)


def get_stream_or_content_from_request(request):
    """Ensure the proper content is uploaded.

    Stream might be already consumed by authentication process.
    Hence flask.request.stream might not be readable and return improper value.

    This methods checks if the stream has already been consumed and if so
    retrieve the data from flask.request.data where it has been stored.
    """

    if request.stream.tell():
        logger.info(
            "Request stream already consumed. "
            "Storing file content using in-memory data."
        )
        return request.data

    else:
        logger.info("Storing file content using request stream.")
        return request.stream


def build_file_path(root, middle, file_id):
    root = str(root)
    middle = str(middle)
    file_id = str(file_id)
    return "%s/%s/%s" % (root, middle, file_id)


def md5Checksum(filePath):
    with open(filePath, "rb") as fh:
        m = hashlib.md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()
