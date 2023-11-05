import cyal
import wx


class ConfigScreen(wx.Frame):
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
        self.capture = cyal.CaptureExtension()
        self.input_device = input_device or self.capture.default_device
        self.output_device = output_device or cyal.get_default_all_device_specifier()
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
        self.input_device_ctrl.Bind(wx.EVT_CHOICE, self.on_input_device_change)
        output_device_label = wx.StaticText(tab2, label="Output Device:")
        self.output_device_ctrl = wx.Choice(tab2)
        self.output_device_ctrl.Bind(wx.EVT_CHOICE, self.on_output_device_change)
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
        string_to_remove = "OpenAL Soft on " # Just so we get only the device name
        input_devices = self.capture.devices
        output_devices = cyal.get_all_device_specifiers()
        for index, device in enumerate(input_devices):
            id = device.encode()
            self.input_device_ctrl.Append(device.replace(string_to_remove, "", 1), id)
            if id == self.input_device: # It's the selected/default one, so we set selection to it
                self.input_device_ctrl.SetSelection(index)
        for index, device in enumerate(output_devices):
            id = device
            self.output_device_ctrl.Append(device.replace(string_to_remove, "", 1), id) # For output devices we don't need to encode their names
            if id == self.output_device: # It's the selected/default one, so we set selection to it
                self.output_device_ctrl.SetSelection(index)


    def on_input_device_change(self, event):
        device = self.input_device_ctrl.GetClientData(
            self.input_device_ctrl.GetSelection()
        )
        self.input_device = device

    def on_output_device_change(self, event):
        device = self.output_device_ctrl.GetClientData(
            self.output_device_ctrl.GetSelection()
        )
        self.output_device = device
