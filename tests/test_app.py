import pytest

from sc4_mapper.SC4MapApp import SC4App, check_tools_pyd, main


def test_tools3d():
    assert check_tools_pyd()


class TestMainWindow:
    @pytest.fixture(scope="function")
    @pytest.mark.usefixtures("mocker")
    def sc4_app_obj(self, mocker):
        init_mock = mocker.patch("sc4_mapper.SC4MapApp.SC4App.OnInit")
        sc4_app = SC4App(False)
        yield sc4_app, init_mock
        sc4_app.Destroy()

    @pytest.mark.usefixtures("mocker")
    def test_main(self, mocker):
        init_mock = mocker.patch("sc4_mapper.SC4MapApp.SC4App")
        check_tools_mock = mocker.patch("sc4_mapper.SC4MapApp.check_tools_pyd")
        mocker.patch("wx.App.MainLoop")
        main()
        check_tools_mock.assert_called_once()
        init_mock.assert_called_once_with(False)

    def test_app_init(self, sc4_app_obj):
        sc4_app, init_mock = sc4_app_obj
        init_mock.assert_called_once()
