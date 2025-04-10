# -*- encoding: utf-8 -*-
#
# Copyright (C) 2024 Red Hat, Inc.
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

from dci.analytics import query_es_dsl as qed

import pyparsing as pp
import pytest


def test_parse_query_invalid():
    with pytest.raises(pp.ParseException):
        qed.parse("toto")

    with pytest.raises(pp.ParseException):
        qed.parse("(toto=titi) and (lol=mdr")


def test_parse_query_valid():
    ret = qed.parse("f1='v1'")
    assert ret == ["f1", "=", "v1"]

    ret = qed.parse("(f1='v1')")
    assert ret == [["f1", "=", "v1"]]

    ret = qed.parse("(f1='v1') and (f2='v2')")
    assert ret == [["f1", "=", "v1"], "and", ["f2", "=", "v2"]]

    ret = qed.parse("((f1='v1') and (f2='v2')) or (f3='v3')")
    assert ret == [
        [["f1", "=", "v1"], "and", ["f2", "=", "v2"]],
        "or",
        ["f3", "=", "v3"],
    ]

    ret = qed.parse("((f1='v1') and (f2='v2')) or ((f3='v3') and (f4='v4'))")
    assert ret == [
        [["f1", "=", "v1"], "and", ["f2", "=", "v2"]],
        "or",
        [["f3", "=", "v3"], "and", ["f4", "=", "v4"]],
    ]

    ret = qed.parse(
        "((f1='v1') and ((f2='v2') or (f2='v22'))) or ((f3='v3') and (f4='v4'))"
    )
    assert ret == [
        [["f1", "=", "v1"], "and", [["f2", "=", "v2"], "or", ["f2", "=", "v22"]]],
        "or",
        [["f3", "=", "v3"], "and", ["f4", "=", "v4"]],
    ]

    ret = qed.parse(
        "((f1='v1') and ((f2='v2') or (f2='v22'))) or ((f3='v3') and ((f4='v4') or (f4='v44')))"
    )
    assert ret == [
        [["f1", "=", "v1"], "and", [["f2", "=", "v2"], "or", ["f2", "=", "v22"]]],
        "or",
        [["f3", "=", "v3"], "and", [["f4", "=", "v4"], "or", ["f4", "=", "v44"]]],
    ]

    ret = qed.parse("(f1='v1') and (name not_in ['lol', 'kikoolol', 'lolipop'])")
    assert ret == [
        ["f1", "=", "v1"],
        "and",
        ["name", "not_in", ["lol", "kikoolol", "lolipop"]],
    ]


def test_build():
    ret = qed.build("f1='v1'")
    assert ret == {"term": {"f1": "v1"}}

    ret = qed.build("f1='v1/v11'")
    assert ret == {"term": {"f1": "v1/v11"}}

    ret = qed.build("f1='(v11)v2'")
    assert ret == {"term": {"f1": "(v11)v2"}}

    ret = qed.build("(f1='v1')")
    assert ret == {"term": {"f1": "v1"}}

    ret = qed.build("(f1='v1') and (f2='v2')")
    assert ret == {"bool": {"filter": [{"term": {"f1": "v1"}}, {"term": {"f2": "v2"}}]}}

    ret = qed.build("((f1='v1') and (f2='v2')) or (f3='v3')")
    assert ret == {
        "bool": {
            "should": [
                {"bool": {"filter": [{"term": {"f1": "v1"}}, {"term": {"f2": "v2"}}]}},
                {"term": {"f3": "v3"}},
            ]
        }
    }

    ret = qed.build("((f1='v1') and (f2='v2')) or ((f3='v3') and (f4='v4'))")
    assert ret == {
        "bool": {
            "should": [
                {"bool": {"filter": [{"term": {"f1": "v1"}}, {"term": {"f2": "v2"}}]}},
                {"bool": {"filter": [{"term": {"f3": "v3"}}, {"term": {"f4": "v4"}}]}},
            ]
        }
    }

    ret = qed.build(
        "((f1='v1') and ((f2='v2') or (f2='v22'))) or ((f3='v3') and (f4='v4'))"
    )
    assert ret == {
        "bool": {
            "should": [
                {
                    "bool": {
                        "filter": [
                            {"term": {"f1": "v1"}},
                            {
                                "bool": {
                                    "should": [
                                        {"term": {"f2": "v2"}},
                                        {"term": {"f2": "v22"}},
                                    ]
                                }
                            },
                        ]
                    }
                },
                {"bool": {"filter": [{"term": {"f3": "v3"}}, {"term": {"f4": "v4"}}]}},
            ]
        }
    }

    ret = qed.build(
        "((f1='v1') and ((f2='v2') or (f2='v22'))) or ((f3='v3') and ((f4='v4') or (f4='v44')))"
    )
    assert ret == {
        "bool": {
            "should": [
                {
                    "bool": {
                        "filter": [
                            {"term": {"f1": "v1"}},
                            {
                                "bool": {
                                    "should": [
                                        {"term": {"f2": "v2"}},
                                        {"term": {"f2": "v22"}},
                                    ]
                                }
                            },
                        ]
                    }
                },
                {
                    "bool": {
                        "filter": [
                            {"term": {"f3": "v3"}},
                            {
                                "bool": {
                                    "should": [
                                        {"term": {"f4": "v4"}},
                                        {"term": {"f4": "v44"}},
                                    ]
                                }
                            },
                        ]
                    }
                },
            ]
        }
    }

    ret = qed.build(
        "(name='vcp') and (((components.type='ocp') and (components.version='4.14.27')) and ((components.type='aspenmesh') and (components.version='1.18.7-am1')))"
    )
    assert ret == {
        "bool": {
            "filter": [
                {"term": {"name": "vcp"}},
                {
                    "bool": {
                        "filter": [
                            {
                                "nested": {
                                    "path": "components",
                                    "query": {
                                        "bool": {
                                            "filter": [
                                                {"term": {"components.type": "ocp"}},
                                                {
                                                    "term": {
                                                        "components.version": "4.14.27"
                                                    }
                                                },
                                            ]
                                        }
                                    },
                                }
                            },
                            {
                                "nested": {
                                    "path": "components",
                                    "query": {
                                        "bool": {
                                            "filter": [
                                                {
                                                    "term": {
                                                        "components.type": "aspenmesh"
                                                    }
                                                },
                                                {
                                                    "term": {
                                                        "components.version": "1.18.7-am1"
                                                    }
                                                },
                                            ]
                                        }
                                    },
                                }
                            },
                        ]
                    }
                },
            ]
        }
    }

    ret = qed.build(
        "((components.type='cnf-certification-test')) and ((team.name not_in ['telcoci', 'RedHat']))"
    )
    assert ret == {
        "bool": {
            "filter": [
                {
                    "nested": {
                        "path": "components",
                        "query": {
                            "term": {"components.type": "cnf-certification-test"}
                        },
                    }
                },
                {
                    "nested": {
                        "path": "team",
                        "query": {
                            "bool": {
                                "must_not": {
                                    "terms": {"team.name": ["telcoci", "RedHat"]}
                                }
                            }
                        },
                    }
                },
            ]
        }
    }


def test_query_1():
    ret = qed.build(
        "(components.type='cnf-certification-test') and (components.name not_in ['telcoci', 'RedHat'])"
    )
    assert ret == {
        "nested": {
            "path": "components",
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"components.type": "cnf-certification-test"}},
                        {
                            "bool": {
                                "must_not": {
                                    "terms": {"components.name": ["telcoci", "RedHat"]}
                                }
                            }
                        },
                    ]
                }
            },
        }
    }


def test_query_2():

    ret = qed.build("components.type='cpt_type'")
    assert ret == {
        "nested": {
            "path": "components",
            "query": {"term": {"components.type": "cpt_type"}},
        }
    }


def test_query_build_regex():
    ret = qed.build(
        "(((components.name='openshift-vanilla') and (components.type='ocp')) and ((components.type='netapp-trident') and (components.version=~'v24\\.02.*')))"
    )
    assert ret == {
        "bool": {
            "filter": [
                {
                    "nested": {
                        "path": "components",
                        "query": {
                            "bool": {
                                "filter": [
                                    {"term": {"components.name": "openshift-vanilla"}},
                                    {"term": {"components.type": "ocp"}},
                                ]
                            }
                        },
                    }
                },
                {
                    "nested": {
                        "path": "components",
                        "query": {
                            "bool": {
                                "filter": [
                                    {"term": {"components.type": "netapp-trident"}},
                                    {
                                        "regexp": {
                                            "components.version": {
                                                "case_insensitive": True,
                                                "flags": "ALL",
                                                "value": "v24\\.02.*",
                                            }
                                        }
                                    },
                                ]
                            }
                        },
                    }
                },
            ]
        }
    }


def test_query_build_comparison_operator():
    ret = qed.build(
        "(((keys_values.a>0) and (keys_values.a<10)) or ((keys_values.b>0) and (keys_values.b<=10)))"
    )
    assert ret == {
        "bool": {
            "should": [
                {
                    "nested": {
                        "path": "keys_values",
                        "query": {
                            "bool": {
                                "filter": [
                                    {"range": {"keys_values.a": {"gt": 0}}},
                                    {"range": {"keys_values.a": {"lt": 10}}},
                                ]
                            }
                        },
                    }
                },
                {
                    "nested": {
                        "path": "keys_values",
                        "query": {
                            "bool": {
                                "filter": [
                                    {"range": {"keys_values.b": {"gt": 0}}},
                                    {"range": {"keys_values.b": {"lte": 10}}},
                                ]
                            }
                        },
                    }
                },
            ]
        }
    }


def test_nrt_query_build_nested_regexp():
    ret = qed.build(
        "(name=~'.*upgrade.*') and ((components.type='ocp') and (components.name='openshift')) and (team.name=~'Intel.+') and (topic.name='OCP-4.16')  and (tags in ['daily'])"
    )
    assert ret == {
        "bool": {
            "filter": [
                {
                    "regexp": {
                        "name": {
                            "case_insensitive": True,
                            "flags": "ALL",
                            "value": ".*upgrade.*",
                        }
                    }
                },
                {
                    "nested": {
                        "path": "components",
                        "query": {
                            "bool": {
                                "filter": [
                                    {"term": {"components.type": "ocp"}},
                                    {"term": {"components.name": "openshift"}},
                                ]
                            }
                        },
                    }
                },
                {
                    "nested": {
                        "path": "team",
                        "query": {
                            "regexp": {
                                "team.name": {
                                    "case_insensitive": True,
                                    "flags": "ALL",
                                    "value": "Intel.+",
                                }
                            }
                        },
                    }
                },
                {
                    "nested": {
                        "path": "topic",
                        "query": {"term": {"topic.name": "OCP-4.16"}},
                    }
                },
                {"terms": {"tags": ["daily"]}},
            ]
        }
    }


def test_nrt_query_build_quoted_values():
    ret = qed.build(
        "(tags in ['daily']) and (team.name in ['rh-telco-ci','telco-ci-partner','f5 - openshift'])"
    )
    assert ret == {
        "bool": {
            "filter": [
                {"terms": {"tags": ["daily"]}},
                {
                    "nested": {
                        "path": "team",
                        "query": {
                            "terms": {
                                "team.name": [
                                    "rh-telco-ci",
                                    "telco-ci-partner",
                                    "f5 - openshift",
                                ]
                            }
                        },
                    }
                },
            ]
        }
    }


def test_query_build_nested_field():
    ret = qed.build(
        "(tests.name='junit_e2e.xml') and (tests.testsuites.name='my_testsuite_1') and (tests.testsuites.testscases.name='my_testcase_1')"
    )
    assert ret == {
        "nested": {
            "path": "tests",
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"tests.name": "junit_e2e.xml"}},
                        {
                            "nested": {
                                "path": "tests.testsuites",
                                "query": {
                                    "bool": {
                                        "filter": [
                                            {
                                                "term": {
                                                    "tests.testsuites.name": "my_testsuite_1"
                                                }
                                            },
                                            {
                                                "nested": {
                                                    "path": "tests.testsuites.testscases",
                                                    "query": {
                                                        "term": {
                                                            "tests.testsuites.testscases.name": "my_testcase_1"
                                                        }
                                                    },
                                                }
                                            },
                                        ]
                                    }
                                },
                            }
                        },
                    ]
                }
            },
        }
    }


def test_nrt_complex_test_name():
    ret = qed.build(
        "(team.name='lol') and (tests.name='[sig-api-machinery] API_Server WRS-NonHyperShiftHOST-ROSA-ARO-OSD_CCS-Longduration-NonPreRelease-Author:xxia-Medium-25806-Force encryption key rotation for etcd datastore [Slow][Disruptive] [Serial]')"
    )
    assert ret == {
        "nested": {
            "path": "team",
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"team.name": "lol"}},
                        {
                            "nested": {
                                "path": "tests",
                                "query": {
                                    "term": {
                                        "tests.name": "[sig-api-machinery] API_Server WRS-NonHyperShiftHOST-ROSA-ARO-OSD_CCS-Longduration-NonPreRelease-Author:xxia-Medium-25806-Force encryption key rotation for etcd datastore [Slow][Disruptive] [Serial]"
                                    }
                                },
                            }
                        },
                    ]
                }
            },
        }
    }


def test_nrt_nested_query():
    ret = qed.build(
        "(topic.name='OCP-4.19') and ((components.tags in ['build:dev']) and (components.name='OpenShift 4.19.0 ec.3'))"
    )
    assert ret == {
        "bool": {
            "filter": [
                {
                    "nested": {
                        "path": "topic",
                        "query": {"term": {"topic.name": "OCP-4.19"}},
                    }
                },
                {
                    "nested": {
                        "path": "components",
                        "query": {
                            "bool": {
                                "filter": [
                                    {"terms": {"components.tags": ["build:dev"]}},
                                    {
                                        "term": {
                                            "components.name": "OpenShift 4.19.0 ec.3"
                                        }
                                    },
                                ]
                            }
                        },
                    }
                },
            ]
        }
    }


def test_not_equal_on_testscases():
    ret = qed.build(
        "(tags in ['daily']) and (name='openshift-vz-sec') and (status='success') and (tests.name='junit_e2e') and ((tests.testsuites.testcases.name=~'.*SDN.*') and (tests.testsuites.testcases.action!='success'))"
    )
    assert ret == {
        "bool": {
            "filter": [
                {"terms": {"tags": ["daily"]}},
                {"term": {"name": "openshift-vz-sec"}},
                {"term": {"status": "success"}},
                {
                    "nested": {
                        "path": "tests",
                        "query": {"term": {"tests.name": "junit_e2e"}},
                    }
                },
                {
                    "nested": {
                        "path": "tests.testsuites.testcases",
                        "query": {
                            "bool": {
                                "filter": [
                                    {
                                        "regexp": {
                                            "tests.testsuites.testcases.name": {
                                                "value": ".*SDN.*",
                                                "flags": "ALL",
                                                "case_insensitive": True,
                                            }
                                        }
                                    },
                                    {
                                        "bool": {
                                            "must_not": {
                                                "term": {
                                                    "tests.testsuites.testcases.action": "success"
                                                }
                                            }
                                        }
                                    },
                                ]
                            }
                        },
                    }
                },
            ]
        }
    }
