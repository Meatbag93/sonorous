import cyal
import wx
from . import config, audio_test_dialog


class ConfigScreen(wx.Frame):
    def __init__(
        self,
        parent: wx.Window | None = None,
        configuration: config.AppConfig | None = None,
    ):
        super().__init__(parent, title="Configuration")
        self.config = configuration or config.AppConfig()
        self.capture = self.config.capture
        tabs = wx.Treebook(self)
        # Tab 1: Host, Port, and Name
        tab1 = wx.Panel(tabs)
        tabs.AddPage(tab1, "Connection")
        tab1_sizer = wx.BoxSizer(wx.VERTICAL)
        host_label = wx.StaticText(tab1, label="Host:")
        self.host_ctrl = wx.TextCtrl(tab1, value=self.config.host)
        port_label = wx.StaticText(tab1, label="Port:")
        self.port_ctrl = wx.SpinCtrl(tab1, value=str(self.config.port), max=65535)
        name_label = wx.StaticText(tab1, label="Name:")
        self.name_ctrl = wx.TextCtrl(tab1, value=self.config.name)
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
        tabs.AddPage(tab2, "Sound system")
        tab2_sizer = wx.BoxSizer(wx.VERTICAL)
        input_device_label = wx.StaticText(tab2, label="Input Device:")
        self.input_device_ctrl = wx.Choice(tab2)
        self.input_device_ctrl.Bind(wx.EVT_CHOICE, self.on_input_device_change)
        output_device_label = wx.StaticText(tab2, label="Output Device:")
        self.output_device_ctrl = wx.Choice(tab2)
        self.output_device_ctrl.Bind(wx.EVT_CHOICE, self.on_output_device_change)
        self.test_ctrl = wx.Button(tab2, label="&Test your configuration")
        self.test_ctrl.Bind(wx.EVT_BUTTON, self.on_test)
        tab2_sizer.Add(input_device_label, 0, wx.ALIGN_LEFT | wx.ALL, 10)
        tab2_sizer.Add(self.input_device_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        tab2_sizer.Add(output_device_label, 0, wx.ALIGN_LEFT | wx.ALL, 10)
        tab2_sizer.Add(self.output_device_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        tab2_sizer.Add(self.test_ctrl)
        tab2.SetSizer(tab2_sizer)
        self.update_devices()
        tabs.SetSelection(0)  # Start with the first tab

    def update_devices(self):
        string_to_remove = "OpenAL Soft on "  # Just so we get only the device name
        input_devices = self.capture.devices
        output_devices = cyal.get_all_device_specifiers()
        for index, device in enumerate(input_devices):
            id = device.encode()
            self.input_device_ctrl.Append(device.replace(string_to_remove, "", 1), id)
            if (
                id == self.config.input_device_id
            ):  # It's the selected/default one, so we set selection to it
                self.input_device_ctrl.SetSelection(index)
        for index, device in enumerate(output_devices):
            id = device
            self.output_device_ctrl.Append(
                device.replace(string_to_remove, "", 1), id
            )  # For output devices we don't need to encode their names
            if (
                id == self.config.output_device_id
            ):  # It's the selected/default one, so we set selection to it
                self.output_device_ctrl.SetSelection(index)

    def on_input_device_change(self, event):
        device = self.input_device_ctrl.GetClientData(
            self.input_device_ctrl.GetSelection()
        )
        self.config.input_device_id = device

    def on_output_device_change(self, event):
        device = self.output_device_ctrl.GetClientData(
            self.output_device_ctrl.GetSelection()
        )
        self.config.output_device_id = device
    def on_test(self, event):
        with audio_test_dialog.AudioTestDialog(self, self.config) as dlg:
            dlg.ShowModal()