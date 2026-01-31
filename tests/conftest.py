import pytest
import wx


@pytest.fixture(scope="session", autouse=True)
def wx_app():
    # Create the app before any test runs
    app = wx.App.Get()
    if not app:
        app = wx.App()
    yield app
    # Cleanup after all tests finish
    # app.Destroy() # Avoid destroying if it persists or causes issues


@pytest.fixture(autouse=True)
def mock_wx_dialog(monkeypatch):
    """Mock wx.MessageDialog to always return OK without showing UI"""

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
