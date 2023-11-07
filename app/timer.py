import time


class Timer:
    def __init__(self):
        self.start = time.time()

    @property
    def elapsed(self):
        """Elapsed time in ms"""
        now = time.time()
        return (now - self.start) * 1000

    def restart(self):
        """Restart timer"""
        self.start = time.time()
