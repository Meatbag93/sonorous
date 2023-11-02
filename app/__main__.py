if __name__ == "__main__":
    import wx
    from .config_screen import ConfigScreen
    app = wx.App()
    config = ConfigScreen()
    config.Show()
    app.MainLoop()