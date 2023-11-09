import os
from enum import Enum
from typing import Callable
import wx
import time
import msgpack
import threading
import enet
from .session import Session
from . import structs, timer, channels


class ClientState(Enum):
    CONNECTING = 1
    AUTHENTICATING = 2
    CONNECTED = 3
    TIMEOUT = 4
    DISCONNECTED = 5


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
        self.event_handler = event_handler_factory(self)
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_connection_timeout = on_connection_timeout
        self.session: Session | None = None
        self.timeout_timer = timer.Timer()
        self.address = enet.Address(host.encode(), port)
        self.net = enet.Host(None, 1, 10, 0, 0)
        self.peer = None
        self.running = True
        self.should_poll = True  # for pausing and unpausing networking: No events will be processed and nothing would be done unless this is True
        self.state = ClientState.DISCONNECTED
        self.auth_random_bytes = os.urandom(32)
        self.lock = threading.RLock()
        self.start()

    def connect(self):
        with self.lock:
            if self.state in [
                ClientState.CONNECTED,
                ClientState.AUTHENTICATING,
                ClientState.CONNECTING,
            ]:
                self.disconnect()
            self.auth_random_bytes = os.urandom(32)
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
                    ClientState.AUTHENTICATING,
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
                self.state = ClientState.AUTHENTICATING
                self.session = None
            elif event.type == enet.EVENT_TYPE_DISCONNECT:
                self.state = ClientState.DISCONNECTED
                self.peer = None
                self.session = None
                wx.CallAfter(self.on_disconnect, self)
            elif event.type == enet.EVENT_TYPE_RECEIVE:
                channel = event.channelID
                if self.state is ClientState.AUTHENTICATING:
                    if channel == channels.auth:
                        data = event.packet.data
                        if not self.session:
                            # The servre gave us its public key
                            self.session = Session(data)
                            self.peer.send(
                                channels.auth,
                                enet.Packet(
                                    self.session.get_encrypted_aes_key(),
                                    flags=enet.PACKET_FLAG_RELIABLE,
                                ),
                            )
                            self.peer.send(
                                channels.auth,
                                enet.Packet(
                                    self.session.encrypt(self.auth_random_bytes),
                                    flags=enet.PACKET_FLAG_RELIABLE,
                                ),
                            )
                        elif data == self.auth_random_bytes:
                            self.state = ClientState.CONNECTED
                        else:
                            return self.disconnect()
                elif self.state is ClientState.CONNECTED:
                    data = self.session.decrypt(event.packet.data)
                    if channel == channels.audio_out:
                        user_id, seq_number = structs.audio_packet_header.unpack(
                            data[:2]
                        )
                        opus_data = data[2:]
                        self.event_handler.audio(user_id, seq_number, opus_data)
                        return
                    data = msgpack.loads(event.packet.data)
                    getattr(self.event_handler, f'event_{data["event"]}')(data["data"])
            elif (
                self.state in [ClientState.CONNECTING, ClientState.AUTHENTICATING]
                and self.timeout_timer.elapsed >= timeout_time
            ):
                self.timeout_timer.restart()
                self.state = ClientState.TIMEOUT
                self.peer = None
                self.session = None
                wx.CallAfter(self.on_connection_timeout, self)

    def send(self, channel, event, data=None):
        if self.state is not ClientState.CONNECTED:
            raise BrokenPipeError(
                "Attempted sending a packet to a client that is not connected."
            )
        with self.lock:
            if channel in [channels.audio_in, channels.audio_out]:
                raise ValueError("Can't send non-audio packets to audio channel")
            if data is None:
                data = {}
            packet = enet.Packet(
                self.session.encrypt(msgpack.dumps({"event": event, "data": data})),
                flags=enet.PACKET_FLAG_RELIABLE,
            )
            self.peer.send(channel, packet)

    def send_audio(self, audio):
        if self.state is not ClientState.CONNECTED:
            raise BrokenPipeError(
                "Attempted sending a packet to a client that is not connected."
            )
        with self.lock:
            packet = enet.Packet(self.session.encrypt(audio))
            self.peer.send(channels.audio_in, packet)

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
                ClientState.AUTHENTICATING,
                ClientState.CONNECTED,
            ]:
                raise ConnectionError("Attempted to disconnect a disconnected client")
            self.peer.disconnect_now()
            self.net.flush()
            self.peer = None
            self.state = ClientState.DISCONNECTED
            self.session = None
            wx.CallAfter(self.on_disconnect, self)
