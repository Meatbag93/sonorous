from enum import Enum
from typing import Callable
import wx
import time
import msgpack
import threading
import enet
from . import structs, timer, channels


class ClientState(Enum):
    CONNECTING = 1
    CONNECTED = 2
    TIMEOUT = 3
    DISCONNECTED = 4


timeout_time = 5000


class Client(threading.Thread):
    """The networking client. the on_* callbacks passed to this will be called in the UI (main) thread, and should take an instance of this as there only argument. Every instantiation of this must be pared with a destroy() call at some point to prevent memory leaks."""

    def __init__(
        self,
        host: str,
        port: int,
        event_handler_factory,
        on_disconnect: Callable,
        on_connect: Callable,
        on_connection_timeout: Callable,
    ):
        super().__init__(name="Network-thread", daemon=True)
        self.host = host
        self.port = port
        self.event_handler = event_handler(self)
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_connection_timeout = on_connection_timeout
        self.timeout_timer = timer.Timer()
        self.address = enet.Address(host.encode(), port)
        self.net = enet.Host(None, 1, 10, 0, 0)
        self.peer = None
        self.running = True
        self.should_poll = True  # for pausing and unpausing networking: No events will be processed and nothing would be done unless this is True
        self.state = ClientState.DISCONNECTED
        self.lock = threading.RLock()
        self.start()

    def connect(self):
        with self.lock:
            if self.state in [ClientState.CONNECTED, ClientState.CONNECTING]:
                self.disconnect()
            self.peer = self.net.connect(self.address, 10)
            self.state = ClientState.CONNECTING

    def run(self):
        while self.running:
            if (
                self.should_poll
                and self.peer
                and self.state
                in [
                    ClientState.CONNECTED,
                    ClientState.CONNECTING,
                ]
            ):
                self.loop()
                time.sleep(0.0004)
                continue
            time.sleep(0.05)

    def loop(self):
        with self.lock:
            event = self.net.service(0)
            if event.type == enet.EVENT_TYPE_CONNECT:
                self.state = ClientState.CONNECTED
                wx.CallAfter(self.on_connect, self)
            elif event.type == enet.EVENT_TYPE_DISCONNECT:
                self.state = ClientState.DISCONNECTED
                self.peer = None
                wx.CallAfter(self.on_disconnect, self)
            elif event.type == enet.EVENT_TYPE_RECEIVE:
                channel = event.channelID
                if channel == channels.audio:
                    data = event.packet.data
                    user_id, seq_number = structs.audio_packet_header.unpack(data[:2])
                    opus_data = data[2:]
                    self.event_handler.audio(user_id, seq_number, opus_data)
                    return
                data = msgpack.loads(event.packet.data)
                getattr(self.event_handler, f'event_{data["event"]}')(data["data"])
            elif (
                self.state is ClientState.CONNECTING
                and self.timeout_timer.elapsed >= timeout_time
            ):
                self.timeout_timer.restart()
                self.state = ClientState.TIMEOUT
                self.peer = None
                wx.CallAfter(self.on_connection_timeout, self)

    def send(self, channel, event, data=None):
        if self.state is not ClientState.CONNECTED:
            raise BrokenPipeError(
                "Attempted sending a packet to a client that is not connected."
            )
        with self.lock:
            if channel == channels.audio:
                raise ValueError("Can't send non-audio packets to audio channel")
            if data is None:
                data = {}
            packet = enet.Packet(
                msgpack.dumps({"event": event, "data": data}),
                flags=enet.PACKET_FLAG_RELIABLE,
            )
            self.peer.send(channel, packet)

    def send_audio(self, audio):
        if self.state is not ClientState.CONNECTED:
            raise BrokenPipeError(
                "Attempted sending a packet to a client that is not connected."
            )
        with self.lock:
            packet = enet.Packet(audio)
            self.peer.send(channels.audio, packet)

    def destroy(self):
        self.running = False
        with self.lock:
            if self.state is ClientState.CONNECTED:
                self.disconnect()
        self.join()

    def disconnect(self):
        with self.lock:
            if self.peer is None or self.state not in [
                ClientState.CONNECTING,
                ClientState.CONNECTED,
            ]:
                raise ConnectionError("Attempted to disconnect a disconnected client")
            self.peer.disconnect_now()
            self.net.flush()
            self.peer = None
            self.state = ClientState.DISCONNECTED
