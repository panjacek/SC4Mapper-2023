from unittest.mock import MagicMock

import pytest

from sc4_mapper.SC4MapApp import SC4App, check_tools_pyd, main

pytestmark = pytest.mark.ui


def test_tools3d():
    assert check_tools_pyd()


class TestMainWindow:
    def test_main(self, mocker):
        """main(): constructs SC4App(False); tool check gates startup."""
        app_cls = mocker.patch("sc4_mapper.SC4MapApp.SC4App")
        check_tools_mock = mocker.patch("sc4_mapper.SC4MapApp.check_tools_pyd")

        main()

        app_cls.assert_called_once_with(False)
        check_tools_mock.assert_called_once()

    def test_on_init_shows_splash(self, mocker):
        """OnInit: suppresses log noise, shows splash, returns True.

        Calls OnInit unbound against a mock self - no real wx.App lifecycle.
        Instantiating a second real App here used to destroy wx's global
        singleton for every later test module (PyNoAppError cascade).
        """
        splash_cls = mocker.patch("sc4_mapper.SC4MapApp.SplashScreen")
        app_self = MagicMock()

        assert SC4App.OnInit(app_self) is True
        splash_cls.assert_called_once()
        splash_cls.return_value.Show.assert_called_once()
