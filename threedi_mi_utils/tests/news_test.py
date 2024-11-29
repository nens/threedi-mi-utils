from pathlib import Path
from typing import Any

import pytest

from threedi_mi_utils.news import NewsInjector


def none_to_null(value: Any) -> str:
    return value if value is not None else "null"


def compare(entry, test_item):
    assert entry.key == test_item.pk
    assert ((entry.expiry.toSecsSinceEpoch() if entry.expiry.isValid() else None)
            == int(test_item.publish_to))
    assert entry.title == test_item.title
    assert entry.content == test_item.content
    assert entry.imageUrl == test_item.image
    assert entry.link.toString() == test_item.url
    assert entry.sticky == test_item.sticky


class TestItem():

    __test__ = False

    def __init__(self, pk: int, publish_from: int, publish_to: int, title: str,
                image: str, content: str, url: str, sticky: bool):
        self.pk = pk
        self.publish_from = publish_from
        self.publish_to = publish_to
        self.title = title
        self.image = image
        self.content = content
        self.url = url
        self.sticky = sticky

    def __repr__(self):
        return f'[{{"pk": {none_to_null(self.pk)}, "publish_from": {none_to_null(self.publish_from)}, "publish_to": {none_to_null(self.publish_to)}, \
"title": "{none_to_null(self.title)}", "image": "{none_to_null(self.image)}", "content": "{none_to_null(self.content)}", "url": "{none_to_null(self.url)}", \
"sticky": {none_to_null(str(self.sticky).lower())}}}]'
    
@pytest.fixture()
def news_injector():
    injector = NewsInjector()
    yield injector
    injector.clear()

@pytest.fixture()
def news_item():
    return TestItem(pk=4, publish_from=1557073748.13, publish_to=2557073748.13, title="test title", image="", content="<p>test content</p>", url="bla", sticky=False)

@pytest.fixture()
def sticky_news_item(news_item):
    news_item.sticky = True
    return news_item

@pytest.fixture()
def expired_news_item():
    return TestItem(pk=5, publish_from=None, publish_to=17073748.13, title="test title", image="", content="<p>test content</p>", url="test", sticky=False)

@pytest.fixture()
def data_folder():
    return Path(__file__).parent / "data"

def test_no_news_at_start(news_injector):
    assert len(news_injector.items()) == 0

def test_add_item(news_injector, news_item):
    news_injector.add_items(str(news_item))
    assert len(news_injector.items()) == 1
    news_injector.update()
    assert len(news_injector.items()) == 1
    entry = news_injector.items()[0]
    compare(entry, news_item)

def test_add_sticky_item(news_injector, sticky_news_item):
    news_injector.add_items(str(sticky_news_item))
    assert len(news_injector.items()) == 1
    news_injector.update()
    assert len(news_injector.items()) == 1
    entry = news_injector.items()[0]
    assert entry.sticky == True
    compare(entry, sticky_news_item)
    
def test_add_expired_item(news_injector, expired_news_item):
    # Expired items are added the first time ...
    news_injector.add_items(str(expired_news_item))
    assert len(news_injector.items()) == 1
    entry = news_injector.items()[0]
    compare(entry, expired_news_item)
    news_injector.update()  # ... but are pruned at an update()
    assert len(news_injector.items()) == 0

def test_add_corrupt_item(news_injector):
    news_injector.add_items('thisisnotvalidjson[{"pk": 6, "publish_from": 1557073]')
    assert len(news_injector.items()) == 0

def test_item_twice(news_injector, news_item):
    news_injector.add_items(str(news_item))
    assert len(news_injector.items()) == 1
    news_injector.add_items(str(news_item))
    assert len(news_injector.items()) == 2
    news_injector.update()  # Double items are pruned at an update
    assert len(news_injector.items()) == 1

def test_load_items_expired(news_injector, data_folder):
    assert len(news_injector.items()) == 0
    assert news_injector.load(data_folder / "feed_expired.json")
    # one entry is expired, so 3 items
    assert len(news_injector.items()) == 3
    news_injector.items()[0].key == 10000004
    news_injector.items()[1].key == 10000005
    news_injector.items()[1].key == 10000006

def test_load_items_double(news_injector, data_folder):
    assert news_injector.load(data_folder / "feed_double.json")
    # double ids, so 2 items
    assert len(news_injector.items()) == 2
    news_injector.items()[0].key == 10000004
    news_injector.items()[1].key == 10000005
    news_injector.items()[1].title == "title3"  # last double item remains
    news_injector.items()[1].link == "link3"  # last double item remains

def test_load_items_too_small_pk(news_injector, data_folder):
    assert news_injector.load(data_folder / "feed_too_small_pk.json")
    # double ids, so 2 items
    assert len(news_injector.items()) == 1
    news_injector.items()[0].key == 10000005
