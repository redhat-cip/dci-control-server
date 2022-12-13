from dci import dci_config


def test_nrt_s3_config_is_merged_correctly():
    store = dci_config.get_store()
    assert store.s3_config.region_name == "us-east-1"
    assert store.s3_config.signature_version == "s3v4"
