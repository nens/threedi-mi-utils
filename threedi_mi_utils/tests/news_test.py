import pytest
from qgis.PyQt.QtCore import QDateTime, Qt

from threedi_mi_utils.news import QgsNewsSettingsInjector


@pytest.fixture()
def news_injector():
    injector = QgsNewsSettingsInjector()
    yield injector
    injector.clear()


@pytest.fixture()
def news_item():
    return {
        "key": 10000005,
        "expiry": QDateTime.fromString("2999-01-01", Qt.ISODate),
        "title": "test title",
        "image-url": "",
        "content": "<p>test content</p>",
        "link": "bla",
        "sticky": False,
    }


@pytest.fixture()
def sticky_news_item(news_item):
    news_item["sticky"] = True
    return news_item


@pytest.fixture()
def expired_news_item():
    return {
        "key": 10000006,
        "expiry": QDateTime.fromString("1999-01-01", Qt.ISODate),
        "title": "test title",
        "image-url": "",
        "content": "<p>test content</p>",
        "link": "test",
        "sticky": False,
    }

def test_no_news_at_start(news_injector):
    assert len(news_injector.items()) == 0


def test_add_item(news_injector, news_item):
    assert news_injector.add_item(news_item)
    assert len(news_injector.items()) == 1
    entry = news_injector.items()[0]
    assert entry == news_item


def test_add_sticky_item(news_injector, sticky_news_item):
    assert news_injector.add_item(sticky_news_item)
    assert len(news_injector.items()) == 1
    entry = news_injector.items()[0]
    assert entry["sticky"] == True
    assert entry == sticky_news_item


def test_add_expired_item(news_injector, expired_news_item):
    assert not news_injector.add_item(expired_news_item)
    assert len(news_injector.items()) == 0


def test_item_twice(news_injector, news_item):
    assert news_injector.add_item(news_item)
    assert len(news_injector.items()) == 1
    assert not news_injector.add_item(news_item)
    assert len(news_injector.items()) == 1


def test_load_items_expired(news_injector, data_folder):
    assert len(news_injector.items()) == 0
    assert news_injector.load(data_folder / "feed_expired.json")
    # one entry is expired, so 3 items
    assert len(news_injector.items()) == 3
    news_injector.items()[0]["key"] == 10000004
    news_injector.items()[1]["key"] == 10000005
    news_injector.items()[1]["key"] == 10000006


def test_load_items_double(news_injector, data_folder):
    assert news_injector.load(data_folder / "feed_double.json")
    # double ids, so 2 items
    assert len(news_injector.items()) == 2
    news_injector.items()[0]["key"] == 10000004
    news_injector.items()[1]["key"] == 10000005
    news_injector.items()[1]["title"] == "title2"  # first double item remains
    news_injector.items()[1]["link"] == "link2"  # first double item remains


def test_load_items_too_small_pk(news_injector, data_folder):
    assert news_injector.load(data_folder / "feed_too_small_pk.json")
    assert len(news_injector.items()) == 1
    news_injector.items()[0]["key"] == 10000005
