import pytest

from threedi_mi_utils.working_dir import (
    is_schematisation_db,
    LocalSchematisation,
    LocalRevision,
    RevisionSubPathType
)

from pathlib import Path

def test_is_schematisation_db(data_folder):
    assert is_schematisation_db(str(data_folder / "old_schematisation.sqlite"))
    assert not is_schematisation_db(str(data_folder / "feed_double.json"))


@pytest.fixture
def local_schematisation(tmp_path):
    return LocalSchematisation(str(tmp_path), schematisation_pk=1, schematisation_name="test", create=True)


@pytest.fixture
def local_revision(local_schematisation):
    local_revision = LocalRevision(local_schematisation, 1)
    local_revision.make_revision_structure()
    return local_revision

def test_init_with_create(local_schematisation):
    for sub_path in local_schematisation.subpaths:
        assert Path(sub_path).exists()
    assert Path(local_schematisation.schematisation_config_path).exists()


def test_add_revision(local_schematisation):
    new_revision = local_schematisation.add_revision(1)
    for sub_path in local_schematisation.subpaths:
        assert Path(sub_path).exists()
    assert local_schematisation.revisions[1] == new_revision


def test_replace_revision(local_schematisation):
    # add revision 1 and create an empty file in its folder
    new_revision = local_schematisation.add_revision(1)
    marker_file = Path(new_revision.main_dir).joinpath('foo')
    marker_file.touch()
    # add revision with same number and ensure marker is removed
    local_schematisation.add_revision(new_revision.number)
    assert not marker_file.exists()


def test_set_wip_revision(local_schematisation):
    wip_revision = local_schematisation.set_wip_revision(1)
    for sub_path in local_schematisation.subpaths:
        assert Path(sub_path).exists()
    assert local_schematisation.wip_revision == wip_revision


def test_replace_wip_revision(local_schematisation):
    # add revision 1 and create an empty file in its folder
    wip_revision = local_schematisation.set_wip_revision(1)
    marker_file = Path(wip_revision.main_dir).joinpath('foo')
    marker_file.touch()
    # add revision with same number and ensure marker is removed
    local_schematisation.set_wip_revision(wip_revision.number)
    assert not marker_file.exists()


@pytest.mark.parametrize("exclude_subpaths", [None, [], [RevisionSubPathType.RESULTS], [RevisionSubPathType.GRID, RevisionSubPathType.SCHEMATISATION]])
def test_clear_main_dir(local_revision, exclude_subpaths):
    local_revision.clear_main_dir(exclude_subpaths)
    for sub_path_type in RevisionSubPathType:
        revision_sub_path = Path(local_revision.subpath_map[sub_path_type])
        if exclude_subpaths and sub_path_type in exclude_subpaths:
            assert revision_sub_path.exists()
        else:
            assert not revision_sub_path.exists()
