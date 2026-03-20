"""Base class for all page widgets."""
from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout


class BasePage(QWidget):
    """
    Every page inherits this. Provides:
    - standard layout accessible via self.layout_
    - refresh() hook called by MainWindowEx on navigation
    """

    PAGE_TITLE: str = ""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(16)
        self.build()

    def build(self) -> None:
        """Override in subclass to create widgets."""
        raise NotImplementedError

    def refresh(self) -> None:
        """Called by MainWindowEx each time the user navigates to this page. Override to reload data."""
        pass
