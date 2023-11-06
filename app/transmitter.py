import time
from typing import Callable
from threading import Thread, RLock
from pyogg.opus_encoder import OpusEncoder
import cyal


class transmitter(Thread):
    """Record and transmit opus frames to a callback"""

    def __init__(
        self,
        device: bytes,
        callback: Callable[[bytes], None],
        channels: int = 2,
        frame_size: int = 1920,
    ):
        super().__init__(name="Transmitter-thread", daemon=True)
        self.capture = cyal.CaptureExtension()
        self.frame_size = frame_size
        self.channels = channels
        self.device = self.capture.open_device(
            device,
            format=cyal.BufferFormat.STEREO16
            if channels == 2
            else cyal.BufferFormat.MONO16,
            sample_rate=48000,
            buf_size=frame_size,
        )
        self.callback = callback
        self.encoder = OpusEncoder()
        self.encoder.set_application("audio")
        self.encoder.set_sampling_frequency(48000)
        self.encoder.set_channels(2)
        self.running = True
        self.transmitting = False
        self.buffer = bytearray(frame_size * 2*channels)

    def run(self):
        while self.running:
            if not self.transmitting:
                time.sleep(0.01)  # Sleep for longer when paused
                continue
            with self.device.capturing():
                while self.running and self.transmitting:
                    if self.device.available_samples >= self.frame_size * self.channels:
                        self.device.capture_samples(self.buffer)
                        encoded = self.encoder.encode(self.buffer)
                        self.callback(encoded.tobytes())
                    time.sleep(0.004)

    def destroy(self):
        self.running = False
        self.join()
