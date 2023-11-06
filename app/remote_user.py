import time
from threading import Thread, RLock
from collections import deque
from pyogg.opus_decoder import OpusDecoder
import cyal


class RemoteUser(Thread):
    """Represents another connected user"""

    def __init__(
        self,
        context: cyal.Context,
        id: int,
        display_name: str,
        jitter_buffer_size: int = 3,
    ):
        """Construct a new RemoteUser. You must call destroy() to dispose of this object otherwise a memory leak happens."""
        super().__init__(name=f"RemoteUser-{id}-{display_name}", daemon=True)
        self.context = context
        self.id = id
        self.display_name = display_name
        self.jitter_buffer_size = jitter_buffer_size
        self.chunks = deque(maxlen=jitter_buffer_size)
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
        if self.buffering and len(self.chunks) >= self.jitter_buffer_size:
            self.buffering = False

    def get_chunk(self):
        chunk = self.chunks.pop()
        return chunk

    def update(self):
        if self.buffering or not self.chunks:
            return
        with self.lock:
            if self.source.buffers_processed:
                buffer = self.source.unqueue_buffers(max=1)[0]
            elif self.source.buffers_queued < self.jitter_buffer_size:
                buffer = self.context.gen_buffer()
            else:
                return
            chunk = self.get_chunk()
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
