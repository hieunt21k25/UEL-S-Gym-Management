"""
App/MyApp.py
────────────
Entry point — JSON-based, no backend required.
Run:  .venv\\Scripts\\python.exe App/MyApp.py
"""
from __future__ import annotations
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtWidgets import QApplication

_app: QApplication | None = None
_window = None


def show_login() -> None:
    global _window
    _window = None
    _login_flow()


def _load_stylesheet() -> None:
    qss = PROJECT_ROOT / "ui" / "styles.qss"
    if qss.exists() and _app:
        _app.setStyleSheet(qss.read_text(encoding="utf-8"))


def _open_main(user) -> None:
    global _window
    from App.MainWindowEx import MainWindowEx
    _window = MainWindowEx(logged_in_user=user)
    _window.show()
    _window.raise_()
    _window.activateWindow()


def _login_flow() -> None:
    from ui.dialogs.login_dialog import LoginDialog
    dlg = LoginDialog()
    dlg.raise_()
    dlg.activateWindow()
    if dlg.exec() == dlg.DialogCode.Accepted:
        _open_main(dlg.logged_in_user)
    else:
        if _app:
            _app.quit()


def main() -> None:
    global _app
    _app = QApplication(sys.argv)
    _app.setApplicationName("Gym Manager")
    _app.setStyle("Fusion")
    _load_stylesheet()
    _login_flow()
    sys.exit(_app.exec())


if __name__ == "__main__":
    main()
