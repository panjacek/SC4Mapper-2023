import webbrowser

import pytest
import wx

from sc4_mapper import about


class LinkInfo:
    def __init__(self, href):
        self.href = href

    def GetHref(self):
        return self.href


class TestMyHtmlWindow:
    def setup_method(self, method):
        # Create a wx.App object.
        self.app = wx.App()

        # Create the wx.HtmlWindow.
        self.frame = wx.Frame(None, title="Test MyHtmlWindow")
        self.window = about.MyHtmlWindow(self.frame, -1, (640, 480))

    def teardown_method(self, method):
        self.window.Destroy()
        self.frame.Destroy()

        # Destroy the wx.App object.
        self.app.Destroy()

    @pytest.mark.usefixtures("mocker")
    def test_link_clicked(self, mocker):
        # Mock the webbrowser.open_new() function.
        browser_mock = mocker.patch("webbrowser.open_new")

        # Simulate a link click event.
        linkinfo = LinkInfo("https://www.example.com")

        # Call the OnLinkClicked() method.
        self.window.OnLinkClicked(linkinfo)

        # Verify that the webbrowser.open_new() function was called.
        browser_mock.assert_called_once_with(linkinfo.GetHref())


class TestAuthorBox:
    def setup_method(self, method):
        # Create a wx.App object.
        self.app = wx.App()

        # Create the wx.HtmlWindow.
        self.frame = wx.Frame(None, title="Test AuthorBox")
        self.window = None

    def teardown_method(self, method):
        # self.window.Destroy()
        self.frame.Destroy()

        # Destroy the wx.App object.
        self.app.Destroy()

    @pytest.mark.usefixtures("mocker")
    def test_init(self, mocker):
        html_mock = mocker.patch("sc4_mapper.about.MyHtmlWindow.SetPage")
        self.window = about.AuthorBox(self.frame, "This is test note")
        html_mock.assert_called_once_with("This is test note")
        self.frame.Close()
