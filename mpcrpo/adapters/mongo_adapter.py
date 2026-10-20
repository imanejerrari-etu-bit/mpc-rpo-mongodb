"""Real MongoDB adapter (Kind, via kubectl port-forward svc/mongodb 27018:27017).

Reads ONLY engine counters (serverStatus wiredTiger.log: flush / sync / bytes written), applies J with
setParameter journalCommitInterval + read-back, drives the write load (variable rate, absolute pacing),
and produces a validity report: pod restarts before/after, acknowledged vs offered documents, insertion
errors. A run whose report says valid=False is stored as *.INVALID_*.json and repeated by run_schedule."""
import json, os, subprocess, threading, time
from pymongo import MongoClient, WriteConcern
from .base import Adapter
from ..sim import tps_at

LEAN = {"serverStatus": 1, "metrics": 0, "locks": 0, "transactions": 0, "tcmalloc": 0,
        "opLatencies": 0, "opcounters": 0, "network": 0, "connections": 0, "extra_info": 0}
DB = "mpc_bench"


def kubectl_restarts(prefix="mongodb-"):
    out = subprocess.run(["kubectl", "get", "pods", "-o", "json"], capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        raise RuntimeError("kubectl: " + out.stderr[:200])
    n = 0
    for it in json.loads(out.stdout)["items"]:
        if it["metadata"]["name"].startswith(prefix):
            n += sum(cs.get("restartCount", 0) for cs in it.get("status", {}).get("containerStatuses", []))
    return n


def docker_started_at(container):
    """Restart probe for a plain Docker MongoDB (CI runner): the container start time changes if it restarts."""
    out = subprocess.run(["docker", "inspect", "-f", "{{.State.StartedAt}}", container], capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        raise RuntimeError("docker inspect: " + out.stderr[:200])
    return out.stdout.strip()


class Loader:
    """Insert load with a settable rate (documents/s), absolute pacing (no burst catch-up), error counter."""

    def __init__(self, coll, tps, batch, threads=4):
        self.coll, self.batch, self.n = coll, batch, threads
        self.period = batch * threads / float(tps)
        self.acked, self.errors = 0, 0
        self.lock, self.stop_evt, self.ths = threading.Lock(), threading.Event(), []
        self.payload = os.urandom(100)

    def set_rate(self, tps):
        self.period = self.batch * self.n / float(tps)

    def _run(self, i):
        nxt = time.perf_counter() + i * self.period / self.n
        while not self.stop_evt.is_set():
            d = nxt - time.perf_counter()
            if d > 0:
                time.sleep(d)
            elif d < -1.0:
                nxt = time.perf_counter()
            try:
                self.coll.insert_many([{"p": self.payload, "ts": time.time()} for _ in range(self.batch)], ordered=False)
                with self.lock:
                    self.acked += self.batch
            except Exception:  # noqa
                with self.lock:
                    self.errors += 1
                time.sleep(0.5)
            nxt += self.period

    def start(self):
        for i in range(self.n):
            t = threading.Thread(target=self._run, args=(i,), daemon=True)
            t.start()
            self.ths.append(t)

    def stop(self):
        self.stop_evt.set()
        for t in self.ths:
            t.join(timeout=5)


class MongoAdapter(Adapter):
    def __init__(self, uri=None, user=None, password=None, authdb=None, batch=10, threads=4,
                 restore_j_ms=100, client_factory=MongoClient, restart_probe=None):
        self.uri = uri or os.environ.get("MONGO_URI", "mongodb://localhost:27018")
        self.user = user or os.environ.get("MONGO_USER")
        self.password = password or os.environ.get("MONGO_PASSWORD")
        self.authdb = authdb or os.environ.get("MONGO_AUTHDB", "admin")
        self.batch, self.threads, self.restore_j_ms = batch, threads, restore_j_ms
        self.factory = client_factory
        if restart_probe is None:                       # kubectl (Kind) by default; Docker if MPCRPO_DOCKER_CONTAINER is set
            c = os.environ.get("MPCRPO_DOCKER_CONTAINER")
            restart_probe = (lambda: docker_started_at(c)) if c else kubectl_restarts
        self.probe = restart_probe
        self.client = None
        self._report = {"valid": False, "reason": "not started"}

    # -- helpers ---------------------------------------------------------------------------------
    def _set_j_ms(self, ms):
        self.client.admin.command({"setParameter": 1, "journalCommitInterval": int(ms)})
        got = int(self.client.admin.command({"getParameter": 1, "journalCommitInterval": 1})["journalCommitInterval"])
        if got != int(ms):
            raise RuntimeError(f"journalCommitInterval read-back {got} != {ms}")
        self.j_ms = int(ms)

    # -- Adapter interface -----------------------------------------------------------------------
    def start(self, row, scn, common):
        self.scn, self.c = scn, common
        kw = dict(serverSelectionTimeoutMS=4000, directConnection=True)
        if self.user:
            kw.update(username=self.user, password=self.password, authSource=self.authdb)
        self.client = self.factory(self.uri, **kw)
        self.client.admin.command("ping")
        try:                                   # fail fast with a clear message if credentials are missing
            self.client.admin.command(LEAN)
        except Exception as e:  # noqa
            if "requires authentication" in str(e) or getattr(e, "code", None) in (13, 18):
                raise RuntimeError("MongoDB authentication missing or wrong: load MONGO_USER and MONGO_PASSWORD "
                                   "in THIS PowerShell window") from e
            raise
        self.restarts0 = self.probe()
        try:
            self.mongo_version = self.client.admin.command("buildInfo")["version"]
        except Exception:  # noqa
            self.mongo_version = "unknown"
        self.client.drop_database(DB)
        self.coll = self.client[DB].get_collection("events", write_concern=WriteConcern(w=1, j=False))
        self._set_j_ms(round(common.j_init * 1000))
        self.cur_tps = float(scn["tps0"])
        self.loader = Loader(self.coll, self.cur_tps, self.batch, self.threads)
        self.loader.start()
        self.t0 = time.perf_counter()
        self.offered, self._last_t, self.max_lag, self.n_actuations = 0.0, 0.0, 0.0, 0

    def measure(self, t):
        tps_now = float(tps_at(self.scn, t))
        self.offered += self.cur_tps * (t - self._last_t)
        self._last_t = t
        log = self.client.admin.command(LEAN)["wiredTiger"]["log"]
        ctr = {"flush": log["log flush operations"], "sync": log["log sync operations"],
               "bytes": log["log bytes written"],
               # diagnostics only (not used by controllers): journal pre-allocation / sync time
               "x_prealloc_missed": log.get("pre-allocated log files not ready and missed", 0),
               "x_zero_filled": log.get("log files manually zero-filled", 0),
               "x_sync_us": log.get("log sync time duration (usecs)", 0)}
        if tps_now != self.cur_tps:               # the load changes AFTER the counters of this tick were read
            self.loader.set_rate(tps_now)
            self.cur_tps = tps_now
        return ctr, tps_now

    def actuate(self, j_seconds):
        ms = max(1, min(500, int(round(j_seconds * 1000))))
        if ms != self.j_ms:
            self._set_j_ms(ms)
            self.n_actuations += 1

    def wait_next_tick(self, t, dt):
        d = self.t0 + t + dt - time.perf_counter()
        if d > 0:
            time.sleep(d)
        else:
            self.max_lag = max(self.max_lag, -d)

    def stop(self):
        rep = {"valid": True, "reasons": []}
        try:
            self.loader.stop()
        except Exception as e:  # noqa
            rep["reasons"].append(f"loader.stop: {type(e).__name__}")
        try:
            self._set_j_ms(self.restore_j_ms)
            self.client.drop_database(DB)
        except Exception as e:  # noqa
            rep["reasons"].append(f"restore: {type(e).__name__}: {str(e)[:80]}")
        try:
            r1 = self.probe()
        except Exception as e:  # noqa
            r1 = None
            rep["reasons"].append(f"restart probe failed: {str(e)[:80]}")
        acked = self.loader.acked
        ratio = acked / self.offered if self.offered > 0 else 0.0
        rep.update(restarts_before=self.restarts0, restarts_after=r1, acked_docs=acked,
                   offered_docs=round(self.offered), acked_over_offered=round(ratio, 4),
                   insert_errors=self.loader.errors, max_tick_lag_s=round(self.max_lag, 3),
                   actuations=self.n_actuations, mongo_version=getattr(self, "mongo_version", "unknown"))
        if r1 is None or r1 != self.restarts0:
            rep["reasons"].append("pod restarted or unknown")
        if ratio < 0.95:
            rep["reasons"].append(f"acked/offered {ratio:.3f} < 0.95")
        if self.loader.errors > 0:
            rep["reasons"].append(f"{self.loader.errors} insertion errors")
        if "restore" in " ".join(rep["reasons"]):
            rep["reasons"].append("J NOT restored: check journalCommitInterval")
        rep["valid"] = not rep["reasons"]
        self._report = rep
        try:
            self.client.close()
        except Exception:  # noqa
            pass

    def report(self):
        return self._report
