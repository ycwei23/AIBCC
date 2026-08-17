from app.pipeline.fixtures import list_fixture_keys, load_fixture


def test_lists_all_10_fixtures():
    keys = list_fixture_keys()
    assert len(keys) == 10
    assert "case_01_clean_pass" in keys
    assert "case_10_empty" in keys


def test_load_fixture_returns_bundle_with_expected_shape():
    bundle = load_fixture("case_01_clean_pass")
    assert len(bundle.vlm_detections) == 4
    assert bundle.metadata_by_element_id["exit_001"]["is_evacuation_floor"] is True


def test_load_fixture_unknown_key_raises():
    import pytest
    with pytest.raises(FileNotFoundError):
        load_fixture("does_not_exist")


def test_load_fixture_path_traversal_key_raises_not_reads_outside_dir():
    import pytest
    with pytest.raises(FileNotFoundError):
        load_fixture("../rules/mvp_rules_active_v0")
