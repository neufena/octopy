"""Null MIDI object for use when ALSA/MIDI is unavailable (e.g., in containers)"""


class NullMidi:
    """Stub MIDI object that provides no-op implementations of MIDI methods"""

    def set_callback(self, cb):
        """No-op callback setter"""
        pass

    def open(self):
        """No-op open"""
        pass

    def send_start(self):
        """No-op send start"""
        pass

    def send_stop(self):
        """No-op send stop"""
        pass

    def play(self):
        """No-op play"""
        pass

    def stop(self):
        """No-op stop"""
        pass

    def close(self):
        """No-op close"""
        pass
