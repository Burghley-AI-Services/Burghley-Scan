"""
pywebview wiring: window creation and the js_api bridge the dashboard's
JS talks to. Business logic lives entirely in scan.run_scan() - this
module only adapts it to a GUI.
"""
from pathlib import Path

import webview

from gui.render import get_index_html

# scan.py is the entrypoint script (both in dev and frozen via PyInstaller),
# so it's importable as a top-level module regardless of cwd.
from scan import run_scan


class Api:
    """The `_window` and `_default_path` names are deliberately
    underscore-prefixed: pywebview builds the JS bridge by recursively
    walking every public (non-underscore) attribute on this object via
    `dir()`. A public `self.window` attribute holding the actual
    pywebview Window recurses straight into its native WinForms handle -
    `.native.AccessibilityObject.Bounds` is cyclic in .NET's object
    model, so that walk never terminates."""

    def __init__(self, default_repo_path="."):
        self._window = None
        default = Path(default_repo_path).resolve()
        self._default_path = str(default) if default.is_dir() else None

    def set_window(self, window):
        self._window = window

    def pick_folder(self):
        if self._window is None:
            return None
        result = self._window.create_file_dialog(
            webview.FOLDER_DIALOG, directory=self._default_path or str(Path.cwd())
        )
        if not result:
            return None
        return result[0]

    def run_scan(self, repo_path):
        try:
            return run_scan(repo_path)
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Unexpected error: {e}"}


def launch_gui(default_repo_path="."):
    api = Api(default_repo_path)
    window = webview.create_window(
        "Burghley Scan",
        html=get_index_html(),
        js_api=api,
        width=760,
        height=640,
        min_size=(600, 480),
    )
    api.set_window(window)
    webview.start()


if __name__ == "__main__":
    # Manual dev entrypoint: run as `python -m gui.app` from the repo root.
    launch_gui()
