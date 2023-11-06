import wx
from .config import AppConfig
from .remote_user import RemoteUser
from .transmitter import Transmitter

class AudioTestDialog(wx.Dialog):
    def __init__(self, parent: wx.Window|None, config: AppConfig):
        super().__init__(parent, title = "Audio test")
        self.config=config
        self.output = RemoteUser(self.config.context, 1, "test")
        self.input = Transmitter(self.config.input_device_id, self.output.put_packet)
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.echo = wx.ToggleButton(panel, label = "&Echo input to output")
        self.echo.CenterOnParent()
        self.echo.Bind(wx.EVT_TOGGLEBUTTON, self.on_echo_change)
        sizer.Add(self.echo)
        self.done = wx.Button(panel, wx.ID_CANCEL, label = "&Done")
        sizer.Add(self.done)
    def Destroy(self):
        self.output.destroy()
        self.input.destroy()
        return super().Destroy()
    def on_echo_change(self, event):
        self.input.transmitting = self.echo.GetValue()