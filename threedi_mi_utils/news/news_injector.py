import json
import re
from pathlib import Path
from typing import Any, Dict, List

from qgis.core import QgsSettings
from qgis.PyQt.QtCore import QDateTime, Qt

__all__ = ["QgsNewsSettingsInjector"]


class QgsNewsSettingsInjector:
    """
    A hack to be able to add custom news items to Qgis news feed window.
    https://gis.stackexchange.com/questions/342147/adding-own-items-into-qgis-3-10-news-feed/342218#342218

    We'll add additional news item (with a very high key) in the settings...
    """

    # The url is hardcoded, so we need this settings path.
    settings_path = "app/news-feed/items/httpsfeedqgisorg/entries/items/"
    # To distinguish custom news items from QGIS news items, we start custom items at this (extremely high) offset
    key_offset = 10000000
    regex = r"^app/news-feed/items/httpsfeedqgisorg/entries/items/([0-9]*)/*"

    def load(self, file_path: Path) -> bool:
        """Loads all news items from a provided JSON file"""
        with open(file_path, "r") as file:

            # Check whether all items > key_offset
            entries = json.load(file)
            for entry in entries:
                pk = entry["key"]
                if pk < QgsNewsSettingsInjector.key_offset:
                    continue

                if entry["expiry"]:
                    entry["expiry"] = QDateTime.fromString(entry["expiry"], Qt.ISODate)

                self.add_item(entry)
        return True

    def items(self) -> List[Dict[str, Any]]:
        """Returns the list of custom news items in the settings, useful for testing"""
        all_news_settings_entries = {
            t[0: t.rfind("/")] for t in QgsSettings().allKeys() if t.startswith(QgsNewsSettingsInjector.settings_path)
        }
        keys = set()
        for news_setting_entry in all_news_settings_entries:
            m = re.search(QgsNewsSettingsInjector.regex, news_setting_entry)
            key = int(m.groups()[0])
            if key >= QgsNewsSettingsInjector.key_offset:
                keys.add(key)

        result = []
        for key in keys:
            entry = {}
            entry_path = QgsNewsSettingsInjector.settings_path + str(key)
            entry["title"] = QgsSettings().value(entry_path + "/title")
            entry["image-url"] = QgsSettings().value(entry_path + "/image-url")
            entry["content"] = QgsSettings().value(entry_path + "/content")
            entry["link"] = QgsSettings().value(entry_path + "/link")
            entry["sticky"] = QgsSettings().value(entry_path + "/sticky")
            entry["expiry"] = QgsSettings().value(entry_path + "/expiry")
            entry["key"] = key
            result.append(entry)

        return result

    def clear(self) -> None:
        """Removes all custom news items from settings, useful for testing"""
        all_news_settings_entries = {
            t for t in QgsSettings().allKeys() if t.startswith(QgsNewsSettingsInjector.settings_path)
        }

        for news_setting_entry in all_news_settings_entries:
            m = re.search(QgsNewsSettingsInjector.regex, news_setting_entry)
            key = int(m.groups()[0])
            if key >= QgsNewsSettingsInjector.key_offset:
                QgsSettings().remove(news_setting_entry)

    def add_item(self, entry: Dict[str, Any]) -> bool:
        """Add items to settings, but only if they are not expired and do not already exist"""
        if entry["key"] is None:
            return False

        if entry["expiry"] and entry["expiry"] < QDateTime.currentDateTime():
            return False

        entry_path = QgsNewsSettingsInjector.settings_path + str(entry["key"])
        if QgsSettings().contains(entry_path + "/title"):  # contains() requires complete entry
            return False

        QgsSettings().setValue(entry_path + "/title", entry["title"])
        QgsSettings().setValue(entry_path + "/image-url", entry["image-url"])
        QgsSettings().setValue(entry_path + "/content", entry["content"])
        QgsSettings().setValue(entry_path + "/link", entry["link"])
        QgsSettings().setValue(entry_path + "/sticky", entry["sticky"])
        QgsSettings().setValue(entry_path + "/expiry", entry["expiry"])
        return True
