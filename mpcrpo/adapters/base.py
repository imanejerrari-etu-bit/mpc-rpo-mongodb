"""What a real-engine adapter must provide. SimAdapter implements it for tests."""
from abc import ABC, abstractmethod


class Adapter(ABC):
    @abstractmethod
    def start(self, row, scn, common): ...

    @abstractmethod
    def measure(self, t):
        """Return (counters, tps): counters = {'flush','sync','bytes'} cumulative engine counters
        (serverStatus wiredTiger.log: 'log flush operations', 'log sync operations', 'log bytes written')
        and tps = offered load now. The signal is derived ONLY from counters, never from the commanded J."""

    @abstractmethod
    def actuate(self, j_seconds): ...

    @abstractmethod
    def wait_next_tick(self, t, dt): ...

    @abstractmethod
    def stop(self): ...
