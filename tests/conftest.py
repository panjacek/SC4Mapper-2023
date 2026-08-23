import warnings

import pytest

try:
    import wx

    HAVE_WX = True
except ImportError:
    wx = None
    HAVE_WX = False

# UI tests need real wx — skip collection entirely when running under uv venv (no wx).
# test_full_load.py is wx-free (rgnReader imports wx lazily) and runs everywhere.
if not HAVE_WX:
    collect_ignore = [
        "test_about.py",
        "test_canvas.py",
        "test_overview.py",
        "test_region_from_file.py",
        "test_region_handler.py",
        "test_app.py",
    ]
    warnings.warn(
        f"wx not available: {len(collect_ignore)} UI test modules SKIPPED "
        f"({', '.join(collect_ignore)}). Local run covers the wx-free core only - "
        "full suite = 'make test' (docker); run it before pushing.",
        stacklevel=1,
    )
else:
    # Create the singleton app eagerly, at collection time — immune to
    # fixture-ordering surprises. Never destroyed: process-lifetime object.
    _APP = wx.App.Get() or wx.App()


@pytest.fixture(scope="session", autouse=True)
def wx_app():
    yield _APP if HAVE_WX else None


@pytest.fixture(autouse=True)
def _ensure_wx_app():
    """Self-healing singleton.

    Some tests (e.g. test_app) legitimately construct and destroy their own
    wx.App subclass, which kills wx's process-wide app pointer. Recreate it
    before every test so nothing downstream sees PyNoAppError.
    """
    if HAVE_WX and wx.App.Get() is None:
        wx.App()
    yield


@pytest.fixture(autouse=True)
def mock_wx_dialog(monkeypatch):
    """Mock wx.MessageDialog to always return OK without showing UI"""
    if not HAVE_WX:
        return

    class MockDialog:
        def __init__(self, *args, **kwargs):
            pass

        def ShowModal(self):
            return wx.ID_OK

        def Destroy(self):
            pass

        def Update(self, *args, **kwargs):
            pass

    monkeypatch.setattr(wx, "MessageDialog", MockDialog)
