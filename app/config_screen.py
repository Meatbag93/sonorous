import pyaudio
import wx


class ConfigScreen(wx.Frame):
    def __init__(
        self,
        parent: wx.Window | None = None,
        host: str | None = None,
        port: int | None = None,
        input_device: int | None = None,
        output_device: int | None = None,
    ):
        super().__init__(parent, title="Configuration")
        self.pyaudio = pyaudio.PyAudio()
        self.input_device = input_device
        self.output_device = output_device
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer()
        host_sizer = wx.BoxSizer(wx.VERTICAL)
        host_sizer.Add(wx.StaticText(panel, label="Host"))
        self.host_ctrl = wx.TextCtrl(panel, value=host or "")
        host_sizer.Add(self.host_ctrl, wx.EXPAND | wx.ALL)
        main_sizer.Add(host_sizer, wx.EXPAND | wx.LEFT)
        port_sizer = wx.BoxSizer(wx.VERTICAL)
        port_sizer.Add(wx.StaticText(panel, label="Port"))
        self.port_ctrl = wx.SpinCtrl(
            panel, value=str(port) if port is not None else "", max=65535
        )
        port_sizer.Add(self.port_ctrl, wx.EXPAND | wx.ALL)
        main_sizer.Add(port_sizer, wx.EXPAND | wx.LEFT)
        input_device_sizer = wx.BoxSizer(wx.VERTICAL)
        input_device_sizer.Add(wx.StaticText(panel, label="Input device"))
        self.input_device_ctrl = wx.Choice(panel)
        self.input_device_ctrl.Bind(wx.EVT_CHOICE, self.on_input_device_change)
        input_device_sizer.Add(self.input_device_ctrl, wx.EXPAND | wx.ALL)
        main_sizer.Add(input_device_sizer, wx.EXPAND | wx.LEFT)
        output_device_sizer = wx.BoxSizer(wx.VERTICAL)
        output_device_sizer.Add(wx.StaticText(panel, label="output device"))
        self.output_device_ctrl = wx.Choice(panel)
        self.output_device_ctrl.Bind(wx.EVT_CHOICE, self.on_output_device_change)
        output_device_sizer.Add(self.output_device_ctrl, wx.EXPAND | wx.ALL)
        main_sizer.Add(output_device_sizer, wx.EXPAND | wx.LEFT)
        self.update_devices()
        panel.SetSizer(main_sizer)

    @property
    def host(self):
        return self.host_ctrl.GetValue()

    @property
    def port(self):
        return int(self.port_ctrl.GetValue())

    def update_devices(self):
        host_api = self.pyaudio.get_default_host_api_info()
        if self.input_device is None:
            self.input_device = host_api.get("defaultInputDevice", 0)
        if self.output_device is None:
            self.output_device = host_api.get("defaultOutputDevice", 0)
        self.input_device_ctrl.Clear()
        self.output_device_ctrl.Clear()
        devices = [
            self.pyaudio.get_device_info_by_host_api_device_index(host_api["index"], i)
            for i in range(
                host_api.get("deviceCount", 0),
            )
        ]
        input_device_index = 0
        output_device_index = 0
        for index, device in enumerate(devices):
            if device.get("maxInputChannels", 0) > 0:
                self.input_device_ctrl.Append(device["name"], device)
                if index == self.input_device:
                    self.input_device_ctrl.SetSelection(input_device_index)
                input_device_index += 1
            elif device.get("maxOutputChannels", 0) > 0:
                self.output_device_ctrl.Append(device["name"], device)
                if index == self.output_device:
                    self.output_device_ctrl.SetSelection(output_device_index)
                output_device_index += 1

    def on_input_device_change(self, event):
        device = self.input_device_ctrl.GetClientData(
            self.input_device_ctrl.GetSelection()
        )
        self.input_device = device["index"]

    def on_output_device_change(self, event):
        device = self.output_device_ctrl.GetClientData(
            self.output_device_ctrl.GetSelection()
        )
        self.output_device = device["index"]
