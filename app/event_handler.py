from .config import AppConfig


class EventHandler:
    """An event handler is responsible for handling packets from the server. It defines methods which corespond to either control events or audio packets. For control events, methods must be defined with the name `event_<name>`, where <name> is the name of the event as sent by the server. It must take a single argument: a dict holding data that come with this event."""

    def __init__(self, client, config: AppConfig):
        self.client = client
        self.config = config

    def audio(self, user_id: int, seq_number: int, opus_audio: bytes):
        """Called when an audio packet is receaved"""
        pass
