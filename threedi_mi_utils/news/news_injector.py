import json
from pathlib import Path
from typing import List

from qgis.core import QgsNewsFeedParser
from qgis.PyQt.QtCore import QUrl

__all__ = ["NewsInjector"]

# We still need this url as the entry in the setting is based on this,
# and (hardcoded) used for later lookup
feed_url = "https://feed.qgis.org/"
# To distinguish custom news items from QGIS news items,
# we start custom items at this (extremely high) offset
pk_offset = 10000000


class NewsInjector:
    def __init__(self):
        self.update()

    def load(self, file_path: Path) -> bool:
        """Loads all news items from a provided JSON file"""
        with open(file_path, 'r') as file:
            self.update()
            existing_entries = self.parser.entries()

            # Check whether all items > pk_offset and don't already exists
            entries = json.load(file)
            filtered_entries = []
            for entry in entries:
                pk = entry["pk"]
                if pk < pk_offset:
                    continue

                if next((x for x in existing_entries if x.key == pk), None):
                    continue

                filtered_entries.append(entry)

            self.add_items(json.dumps(filtered_entries))
            self.update()

        return True

    def update(self) -> None:
        """Reads all the entries from the settings and prunes expired entries,
          including entries with the same id"""
        # invokes readStoredEntries()
        self.parser = QgsNewsFeedParser(QUrl(feed_url))

    def items(self) -> List[QgsNewsFeedParser.Entry]:
        """Returns the list of news items"""
        return self.parser.entries()

    def clear(self) -> None:
        """Removes all news items, including QGIS items, useful for testing"""
        self.parser.dismissAll()

    def add_items(self, items_string: str) -> None:
        """Add items, if there are expired items, these are only removed after
         a call to update()"""
        # This stores entries in member variable AND settings
        self.parser.onFetch(items_string)
