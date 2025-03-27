import logging
from pathlib import Path

import pytest
from qgis.core import QgsApplication

_singletons = {}
logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def qgis_app_initialized():
    """Make sure qgis is initialized for testing."""
    if "app" not in _singletons:
        app = QgsApplication([], False)
        app.initQgis()
        logger.debug("Initialized qgis (for testing): %s", app.showSettings())
        _singletons["app"] = app

@pytest.fixture()
def data_folder():
    return Path(__file__).parent / "data"