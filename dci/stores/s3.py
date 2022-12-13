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

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from dci import stores
from dci.common import exceptions

logger = logging.getLogger(__name__)


class S3(stores.Store):
    def __init__(self, conf):
        super(S3, self).__init__(conf)
        self.aws_access_key_id = conf.get("aws_access_key_id")
        self.aws_secret_access_key = conf.get("aws_secret_access_key")
        self.aws_region = conf.get("aws_region")
        self.endpoint_url = conf.get("endpoint_url")
        self.signature_version = conf.get("signature_version")

        self.buckets = conf.get("buckets")
        self.s3_config = self.get_s3_config()
        self.s3 = self.get_s3()

    def get_s3_config(self):
        s3_config = Config()
        if self.aws_region:
            s3_config = s3_config.merge(Config(region_name=self.aws_region))
        if self.signature_version:
            s3_config = s3_config.merge(
                Config(signature_version=self.signature_version)
            )
        return s3_config

    def get_s3(self):
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            config=self.s3_config,
        )

    def delete(self, container_name, filename):
        bucket = self._get_container(container_name)
        try:
            self.s3.delete_object(Bucket=bucket, Key=filename)
        except ClientError as e:
            if int(e.response["Error"]["Code"]) == 404:
                logger.warning(
                    "file '%s' not found in s3 bucket '%s'" % (filename, bucket)
                )
                return
            raise exceptions.StoreException(
                "Error while deleting file '%s'from bucket '%s': %s"
                % (filename, bucket, e),
                status_code=e.response["Error"]["Code"],
            )

    def get(self, container_name, filename):
        bucket = self._get_container(container_name)
        try:
            # TODO(fc): try redirect to:
            # self.s3.Client.generate_presigned_url("get_object", Params={'Bucket': bucket, "Key": filename}, ExpiresIn=120)
            obj = self.s3.get_object(Bucket=bucket, Key=filename)
            return obj, obj["Body"]
        except ClientError as e:
            raise exceptions.StoreException(
                "Error while getting file '%s': %s" % (filename, e),
                status_code=e.response["Error"]["Code"],
            )

    def get_presigned_url(self, method, container_name, filepath):
        bucket = self._get_container(container_name)
        try:
            return self.s3.generate_presigned_url(
                ClientMethod=method,
                Params={"Bucket": bucket, "Key": filepath},
                ExpiresIn=600,
            )
        except ClientError as e:
            raise exceptions.StoreException(
                "Error while getting file '%s': %s" % (filepath, e),
                status_code=e.response["Error"]["Code"],
            )

    def head(self, container_name, filename):
        bucket = self._get_container(container_name)
        try:
            return self.s3.head_object(Bucket=bucket, Key=filename)
        except ClientError as e:
            raise exceptions.StoreException(
                "Error while heading file '%s': %s" % (filename, e),
                status_code=e.response["Error"]["Code"],
            )

    def upload(self, container_name, filename, iterable):
        bucket = self._get_container(container_name)
        try:
            self.s3.head_bucket(Bucket=bucket)
        except ClientError as e:
            logger.warning(e.response)
            if int(e.response["Error"]["Code"]) == 404:
                try:
                    self.s3.create_bucket(Bucket=bucket)
                except ClientError as exc:
                    raise exceptions.StoreException(
                        "Error while creating bucket '%s' for file '%s': %s"
                        % (bucket, filename, exc),
                        status_code=int(e.response["Error"]["Code"]),
                    )
            else:
                raise exceptions.StoreException(
                    "Error while creating bucket for file '%s': %s" % (filename, e),
                    status_code=int(e.response["Error"]["Code"]),
                )

        self.s3.upload_fileobj(iterable, bucket, filename)
