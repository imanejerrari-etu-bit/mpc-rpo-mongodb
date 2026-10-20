from .base import Adapter
from ..plant import PlantParams, VolumePlant
from ..sim import tps_at


class SimAdapter(Adapter):
    """Virtual time (no sleeping)."""
    def __init__(self, plant: PlantParams = None):
        self.pp = plant or PlantParams()

    def start(self, row, scn, common):
        self.scn, self.c = scn, common
        self.pl = VolumePlant(self.pp, int(row["seed"]), common.j_init)
        self.J = common.j_init

    def measure(self, t):
        tps = tps_at(self.scn, t)                      # offered load now (logged)
        return self.pl.advance(self.J, tps_at(self.scn, t - self.c.dt), self.c.dt), tps

    def actuate(self, j_seconds):
        self.J = j_seconds

    def wait_next_tick(self, t, dt):
        pass

    def stop(self):
        pass
