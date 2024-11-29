from pathlib import Path
from typing import List

from qgis.core import QgsNewsFeedParser
from qgis.PyQt.QtCore import QUrl

__all__ = ["NewsInjector"]

# We still need this url as the entry in the setting is based on this, and (hardcoded) used for later lookup
feed_url = "https://feed.qgis.org/"

class NewsInjector:

    def __init__(self):
        self.refresh()

    def refresh(self) -> None:
        """Reads all the entries from the settings and prunes expired entries"""
        # This invokes readStoredEntries() which also prunes expired entries
        self.parser = QgsNewsFeedParser(QUrl(feed_url))

    def items(self) -> List[QgsNewsFeedParser.Entry]:
        return self.parser.entries()

    def clear(self) -> None:
        self.parser.dismissAll()

    def add_items(self, items_string: str) -> None:
        """Add items"""
        
        # Stores entries in member variable AND settings
        self.parser.onFetch(items_string)
