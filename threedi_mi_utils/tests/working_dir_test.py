import pytest

from threedi_mi_utils.working_dir import is_schematisation_db


def test_is_schematisation_db(data_folder):
    assert is_schematisation_db(str(data_folder / "old_schematisation.sqlite"))
    assert not is_schematisation_db(str(data_folder / "feed_double.json"))
