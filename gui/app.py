"""
pywebview wiring: window creation and the js_api bridge the dashboard's
JS talks to. Business logic lives entirely in scan.run_scan() - this
module only adapts it to a GUI.
"""
import threading
import time
from pathlib import Path

import webview

from gui.render import get_index_html

# scan.py is the entrypoint script (both in dev and frozen via PyInstaller),
# so it's importable as a top-level module regardless of cwd.
from scan import ScanCancelled, check_repo, run_scan


def _make_progress_pusher(window):
    """Returns an on_progress(current, total) callback that pushes into the
    page via evaluate_js. Time-throttled to ~10 updates/second rather than
    one push per file - on a repo with thousands of files, one JS-engine
    round trip per file would add real lag; a human can't perceive updates
    faster than about 10Hz anyway, so nothing is lost by capping there."""
    last_push = [0.0]

    def push(current, total):
        now = time.monotonic()
        if current < total and now - last_push[0] < 0.1:
            return
        last_push[0] = now
        try:
            window.evaluate_js(f"window.updateScanProgress && window.updateScanProgress({current}, {total})")
        except Exception:
            pass  # window may already be closing - a dropped progress update isn't worth crashing the scan over

    return push


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
        self._cancel_event = None

    def set_window(self, window):
        self._window = window

    def pick_folder(self):
        """Validates the folder the moment it's picked (a real git repo,
        not just any directory) and hands the result back in the same
        round trip, so the UI can catch a bad folder before the user
        even clicks Run instead of finding out after a scan attempt
        fails deep inside run_scan()."""
        if self._window is None:
            return None
        result = self._window.create_file_dialog(
            webview.FOLDER_DIALOG, directory=self._default_path or str(Path.cwd())
        )
        if not result:
            return None
        path = result[0]
        ok, message = check_repo(path)
        return {"path": path, "ok": ok, "message": message}

    def run_scan(self, repo_path):
        self._cancel_event = threading.Event()
        on_progress = _make_progress_pusher(self._window) if self._window else None
        try:
            return run_scan(repo_path, on_progress=on_progress, should_cancel=self._cancel_event.is_set)
        except ScanCancelled:
            return {"cancelled": True}
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Unexpected error: {e}"}

    def cancel_scan(self):
        if self._cancel_event is not None:
            self._cancel_event.set()
        return {"ok": True}


def launch_gui(default_repo_path="."):
    api = Api(default_repo_path)
    window = webview.create_window(
        "Burghley Scan - Preview",
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
