import pyaudio
import wx


class ConfigScreen(wx.Dialog):
    def __init__(
        self,
        parent: wx.Window | None = None,
        host: str | None = None,
        port: int | None = None,
        input_device: int | None = None,
        output_device: int | None = None,
        name: str = "",
    ):
        super().__init__(parent, title="Configuration")
        self.pyaudio = pyaudio.PyAudio()
        self.input_device = input_device
        self.output_device = output_device
        tabs = wx.Treebook(self)
        # Tab 1: Host, Port, and Name
        tab1 = wx.Panel(tabs)
        tabs.AddPage(tab1, "Connection")
        tab1_sizer = wx.BoxSizer(wx.VERTICAL)
        host_label = wx.StaticText(tab1, label="Host:")
        self.host_ctrl = wx.TextCtrl(tab1, value=host or "")
        port_label = wx.StaticText(tab1, label="Port:")
        self.port_ctrl = wx.SpinCtrl(
            tab1, value=str(port) if port is not None else "", max=65535
        )
        name_label = wx.StaticText(tab1, label="Name:")
        self.name_ctrl = wx.TextCtrl(tab1, value=name)
        self.name_ctrl.SetMaxLength(32)
        tab1_sizer.Add(host_label, 0, wx.ALIGN_LEFT | wx.ALL, 10)
        tab1_sizer.Add(self.host_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        tab1_sizer.Add(port_label, 0, wx.ALIGN_LEFT | wx.ALL, 10)
        tab1_sizer.Add(self.port_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        tab1_sizer.Add(name_label, 0, wx.ALIGN_LEFT | wx.ALL, 10)
        tab1_sizer.Add(self.name_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        tab1.SetSizer(tab1_sizer)
        # Tab 2: Audio Devices
        tab2 = wx.Panel(tabs)
        tabs.AddPage(tab2, "Audio Devices")
        tab2_sizer = wx.BoxSizer(wx.VERTICAL)
        input_device_label = wx.StaticText(tab2, label="Input Device:")
        self.input_device_ctrl = wx.Choice(tab2)
        output_device_label = wx.StaticText(tab2, label="Output Device:")
        self.output_device_ctrl = wx.Choice(tab2)
        tab2_sizer.Add(input_device_label, 0, wx.ALIGN_LEFT | wx.ALL, 10)
        tab2_sizer.Add(self.input_device_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        tab2_sizer.Add(output_device_label, 0, wx.ALIGN_LEFT | wx.ALL, 10)
        tab2_sizer.Add(self.output_device_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        tab2.SetSizer(tab2_sizer)
        self.update_devices()
        tabs.SetSelection(0)  # Start with the first tab

    @property
    def host(self):
        return self.host_ctrl.GetValue()

    @property
    def port(self):
        return int(self.port_ctrl.GetValue())

    @property
    def name(self):
        return self.name_ctrl.GetValue()

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
