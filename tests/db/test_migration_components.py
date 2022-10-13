# -*- encoding: utf-8 -*-
#
# Copyright 2023 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from dci.db.migration_components import (
    get_new_component_info,
)


def test_partner_product():
    assert get_new_component_info(
        {
            "name": "amazing-product:20.07.1",
            "canonical_project_name": "Partner amazing-product:20.07.1",
        }
    ) == {
        "display_name": "Partner amazing-product:20.07.1",
        "version": "20.07.1",
        "uid": "",
    }


def test_another_partner_product():
    assert get_new_component_info(
        {
            "name": "partner/product:14.7.0.4-0.71.7N0LIC",
            "canonical_project_name": "partner/product:14.7.0.4-0.71.7N0LIC",
        }
    ) == {
        "display_name": "partner/product:14.7.0.4-0.71.7N0LIC",
        "version": "14.7.0.4-0.71.7N0LIC",
        "uid": "",
    }


def test_operator():
    assert get_new_component_info(
        {
            "name": "registry.abcdef.lab:4443/redhat/redhat-operator-index:v4.9",
            "canonical_project_name": "registry.abcdef.lab:4443/redhat/redhat-operator-index:v4.9",
        }
    ) == {
        "display_name": "registry.abcdef.lab:4443/redhat/redhat-operator-index:v4.9",
        "version": "v4.9",
        "uid": "",
    }


def test_RHEL_compose():
    assert get_new_component_info(
        {
            "name": "RHEL-9.1.0-20220812.1",
            "canonical_project_name": "RHEL-9.1.0-20220812.1",
        }
    ) == {
        "display_name": "RHEL-9.1.0-20220812.1",
        "version": "9.1.0-20220812.1",
        "uid": "",
    }


def test_RHOS_compose():
    assert get_new_component_info(
        {
            "name": "RHOS-17.0-RHEL-9-20220816.n.2",
            "canonical_project_name": "17.0-RHEL-9",
        }
    ) == {
        "display_name": "RHOS-17.0-RHEL-9-20220816.n.2",
        "version": "17.0-RHEL-9-20220816.n.2",
        "uid": "",
    }


def test_RHOS_10_compose():
    assert get_new_component_info(
        {
            "name": "RH7-RHOS-10.0 2017-05-23.4",
            "canonical_project_name": "RH7-RHOS-10.0",
        }
    ) == {
        "display_name": "RH7-RHOS-10.0 2017-05-23.4",
        "version": "10.0 2017-05-23.4",
        "uid": "",
    }


def test_CNF_image():
    assert get_new_component_info(
        {
            "name": "CNF image nrf-expiration 10.1.0-4757-ubi-1-0",
            "canonical_project_name": "CNF image nrf-expiration 10.1.0-4757-ubi-1-0",
        }
    ) == {
        "display_name": "CNF image nrf-expiration 10.1.0-4757-ubi-1-0",
        "version": "10.1.0-4757-ubi-1-0",
        "uid": "",
    }


def test_CNF_image2():
    assert get_new_component_info(
        {
            "name": "CNF img ocp-v4.0-art-dev@sha256 0.0.0+nil",
            "canonical_project_name": "CNF img ocp-v4.0-art-dev@sha256 0.0.0+nil",
        }
    ) == {
        "display_name": "CNF img ocp-v4.0-art-dev@sha256 0.0.0+nil",
        "version": "sha256 0.0.0+nil",
        "uid": "",
    }


def test_dci_openshift_agent():
    assert get_new_component_info(
        {
            "name": "d2ebdc12ee3fd9325f501c30a5f3982512a17da7",
            "canonical_project_name": "dci-openshift-agent d2ebdc1",
        }
    ) == {
        "display_name": "dci-openshift-agent d2ebdc1",
        "version": "d2ebdc1",
        "uid": "d2ebdc12ee3fd9325f501c30a5f3982512a17da7",
    }


def test_dci_openshift_app_agent():
    assert get_new_component_info(
        {
            "name": "dci-openshift-app-agent 0.5.1-1.202209291912git8520aea2.el8",
            "canonical_project_name": "dci-openshift-app-agent 0.5.1",
        }
    ) == {
        "display_name": "dci-openshift-app-agent 0.5.1",
        "version": "0.5.1-1.202209291912git8520aea2.el8",
        "uid": "",
    }


def test_oc_client():
    assert get_new_component_info(
        {
            "name": "oc client 4.11.7",
            "canonical_project_name": "oc client 4.11.7",
        }
    ) == {
        "display_name": "oc client 4.11.7",
        "version": "4.11.7",
        "uid": "",
    }


def test_rhcos_kernel():
    assert get_new_component_info(
        {
            "name": "4.18.0-305.65.1.el8_4.x86_64",
            "canonical_project_name": "rhcos_kernel 4.18.0-305.65.1.el8_4.x86_64",
        }
    ) == {
        "display_name": "rhcos_kernel 4.18.0-305.65.1.el8_4.x86_64",
        "version": "4.18.0-305.65.1.el8_4.x86_64",
        "uid": "",
    }


def test_openshift_nightly_412():
    assert get_new_component_info(
        {
            "name": "4.11.0-0.nightly-2022-05-09-224745",
            "canonical_project_name": "OpenShift 4.11.0 2022-05-09",
        }
    ) == {
        "display_name": "OpenShift 4.11.0 2022-05-09",
        "version": "4.11.0-0.nightly-2022-05-09-224745",
        "uid": "",
    }


def test_openshift_nightly_413():
    assert get_new_component_info(
        {
            "name": "4.13.0-0.nightly-2023-01-07-013625",
            "canonical_project_name": "OpenShift 4.13 nightly 2023-01-07 01:38",
        }
    ) == {
        "display_name": "OpenShift 4.13 nightly 2023-01-07 01:38",
        "version": "4.13.0-0.nightly-2023-01-07-013625",
        "uid": "",
    }


def test_openshift_rc():
    assert get_new_component_info(
        {
            "name": "4.6.53-2022-01-05-190946",
            "canonical_project_name": "OpenShift 4.6.53 RC 2022-01-05",
        }
    ) == {
        "display_name": "OpenShift 4.6.53 RC 2022-01-05",
        "version": "4.6.53-2022-01-05-190946",
        "uid": "",
    }


def test_openshift_ga():
    assert get_new_component_info(
        {
            "name": "4.8.38",
            "canonical_project_name": "OpenShift 4.8.38",
        }
    ) == {
        "display_name": "OpenShift 4.8.38",
        "version": "4.8.38",
        "uid": "",
    }


def test_openshift_old_ga():
    assert get_new_component_info(
        {
            "name": "OpenShift 4.6.53",
            "canonical_project_name": None,
        }
    ) == {
        "display_name": "OpenShift 4.6.53",
        "version": "4.6.53",
        "uid": "",
    }


def test_python3_openshift():
    assert get_new_component_info(
        {
            "name": "python3-openshift 0.11.2-1.el8",
            "canonical_project_name": "python3-openshift 0.11.2-1.el8",
        }
    ) == {
        "display_name": "python3-openshift 0.11.2-1.el8",
        "version": "0.11.2-1.el8",
        "uid": "",
    }


def test_dci_auth():
    assert get_new_component_info(
        {
            "name": "6f5e6bab273e5c41e675e1420b68c616471ec2bf",
            "canonical_project_name": "python-dciauth 6f5e6ba",
        }
    ) == {
        "display_name": "python-dciauth 6f5e6ba",
        "version": "6f5e6ba",
        "uid": "6f5e6bab273e5c41e675e1420b68c616471ec2bf",
    }


def test_dci_client():
    assert get_new_component_info(
        {
            "name": "0bd6b97e92bd03df09c44ed9e6c851881e79f0dc",
            "canonical_project_name": "python-dciclient 0bd6b97",
        }
    ) == {
        "display_name": "python-dciclient 0bd6b97",
        "version": "0bd6b97",
        "uid": "0bd6b97e92bd03df09c44ed9e6c851881e79f0dc",
    }


def test_partner():
    assert get_new_component_info(
        {
            "name": "v1.6.0",
            "canonical_project_name": "F5 Partner:v1.6.0 v1.6.0",
        }
    ) == {
        "display_name": "F5 Partner:v1.6.0 v1.6.0",
        "version": "v1.6.0 v1.6.0",
        "uid": "",
    }


def test_foo():
    assert get_new_component_info(
        {
            "name": "0bd6b97e92bd03df09c44ed9e6c851881e79f0dc",
            "canonical_project_name": "n3-foo-config 0bd6b97",
        }
    ) == {
        "display_name": "n3-foo-config 0bd6b97",
        "version": "0bd6b97",
        "uid": "0bd6b97e92bd03df09c44ed9e6c851881e79f0dc",
    }


def test_bar():
    assert get_new_component_info(
        {
            "name": "12.1.0.1",
            "canonical_project_name": "p2 bar-re 12.1.0.1",
        }
    ) == {
        "display_name": "p2 bar-re 12.1.0.1",
        "version": "12.1.0.1",
        "uid": "",
    }


def test_ansible():
    assert get_new_component_info(
        {
            "name": "ansible 2.9.18-1.el8ae",
            "canonical_project_name": "ansible 2.9.18-1.el8ae",
        }
    ) == {
        "display_name": "ansible 2.9.18-1.el8ae",
        "version": "2.9.18-1.el8ae",
        "uid": "",
    }
