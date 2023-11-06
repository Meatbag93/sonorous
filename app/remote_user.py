import time
from threading import Thread, RLock
from collections import deque
from pyogg.opus_decoder import OpusDecoder
import cyal


class RemoteUser(Thread):
    """Represents another connected user"""

    def __init__(self, context: cyal.Context, id: int, display_name: str):
        super().__init__(name=f"RemoteUser-{id}-{display_name}", daemon=True)
        self.context = context
        self.id = id
        self.display_name = display_name
        self.chunks = deque(maxlen=3)
        self.buffering = True
        self.decoder = OpusDecoder()
        self.decoder.set_sampling_frequency(48000)
        self.decoder.set_channels(2)
        self.source = context.gen_source(direct_channels=True)
        self.lock = RLock()
        self.running = True
        self.start()

    def put_packet(self, packet: bytes):
        self.chunks.append(bytes(self.decoder.decode(memoryview(bytearray(packet)))))
        if self.buffering and len(self.chunks) >= 3:
            self.buffering = False

    def get_chunk(self):
        chunk = self.chunks.pop()
        if not self.chunks and not self.buffering:
            self.buffering = True

    def update(self):
        if self.buffering or not self.chunks:
            return
        with self.lock:
            chunk = self.get_chunk()
            if self.source.buffers_processed:
                buffer = self.source.unqueue_buffers(max=1)[0]
            elif self.source.buffers_queued < 3:
                buffer = self.context.gen_buffer()
            else:
                return
            buffer.set_data(chunk, sample_rate=48000, format=cyal.BufferFormat.STEREO16)
            self.source.queue_buffers(buffer)
            if self.source.state in [
                cyal.SourceState.STOPPED,
                cyal.SourceState.INITIAL,
            ]:
                self.source.play()

    def run(self):
        while self.running:
            self.update()
            time.sleep(0.001)

    def destroy(self):
        self.running = False
        self.join()
