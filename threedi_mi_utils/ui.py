from .constants import PROGRESS_COLOR_FAILED, PROGRESS_COLOR_FINISHED, PROGRESS_COLOR_RUNNING
from qgis.PyQt.QtWidgets import QProgressBar


class ColoredProgressBar(QProgressBar):
    """QProgressBar that auto-colors based on progress: blue while running, green when complete."""

    COLOR_RUNNING = PROGRESS_COLOR_RUNNING
    COLOR_FINISHED = PROGRESS_COLOR_FINISHED
    COLOR_FAILED = PROGRESS_COLOR_FAILED

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_color()

    def setValue(self, value):
        super().setValue(value)
        self._update_color()

    def setMaximum(self, maximum):
        super().setMaximum(maximum)
        self._update_color()

    def set_failed(self):
        """Set progress bar to failed (red) state."""
        self.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {self.COLOR_FAILED}; }}"
            f"QProgressBar {{ background-color: {self.COLOR_FAILED}; }}"
        )

    def _update_color(self):
        if self.maximum() > 0 and self.value() >= self.maximum():
            color = self.COLOR_FINISHED
        else:
            color = self.COLOR_RUNNING
        self.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")
