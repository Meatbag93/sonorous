import cyal


class AppConfig:
    """Holds the configuration"""

    def __init__(
        self,
        host: str = "",
        port: int = 0,
        name: str = "",
        input_device: bytes = b"",
        output_device: str = "",
    ):
        self.capture = cyal.CaptureExtension()
        self.host = host
        self.port = port
        self.name = name
        self.input_device_id = input_device or self.capture.default_device
        output_device_id = output_device or cyal.get_default_all_device_specifier()
        self._output_device = None
        self.output_device_id = output_device
        self.context = cyal.Context(self._output_device, make_current = True)

    @property
    def output_device_id(self):
        if self._output_device is not None:
            return self._output_device.output_name

    @output_device_id.setter
    def output_device_id(self, value: str):
        if self._output_device is None:
            self._output_device = cyal.Device(value)
        else:
            self._output_device.reopen(value)

    def to_json(self):
        return {
            "host": self.host,
            "port": self.port,
            "name": self.name,
            "input_device": self.input_device_id,
            "output_device": self.output_device_id,
        }

    @classmethod
    def from_json(cls, json):
        cls(
            json["host"],
            json["port"],
            json["name"],
            json["input_device"],
            json["output_device"],
        )
