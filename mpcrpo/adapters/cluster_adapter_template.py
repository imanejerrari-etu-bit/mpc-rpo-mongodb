"""TEMPLATE for the real MongoDB (Kind). Fill together, after step 3b.
  start():   connect (port-forward 27018 + MONGO_USER/MONGO_PASSWORD), set J = common.j_init, start the
             load generator (scenario scn: tps0, optional burst tps1), record pod restart counts.
  measure(): one lean serverStatus -> counters {'flush','sync','bytes'}; return the offered tps now.
  actuate(): setParameter journalCommitInterval = round(1000*J) ms, verified by read-back.
  wait_next_tick(): sleep until t0 + (k+1)*dt (absolute schedule).
  stop():    stop load, restore J=100 ms, compare pod restart counts (a run with a restart is INVALID)."""
from .base import Adapter


class ClusterAdapter(Adapter):
    def start(self, row, scn, common): raise NotImplementedError
    def measure(self, t): raise NotImplementedError
    def actuate(self, j_seconds): raise NotImplementedError
    def wait_next_tick(self, t, dt): raise NotImplementedError
    def stop(self): raise NotImplementedError
