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
        self.input_device = input_device or self.capture.default_device
        self.output_device = output_device or cyal.get_default_all_device_specifier()

    def to_json(self):
        return {
            "host": self.host,
            "port": self.port,
            "name": self.name,
            "input_device": self.input_device,
            "output_device": self.output_device,
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
