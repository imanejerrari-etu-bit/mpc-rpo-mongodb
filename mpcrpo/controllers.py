"""Controllers on ln V with actuator J.  Common interface: step(obs) -> J (seconds), where
obs = {"R_tick", "R_fast", "V"} comes from sensor.Sensor.  Nothing is hidden elsewhere.

Static plant model:  V(R, J) = R*(J + p*L0)/p ,  p = min(1, R*J/b0)."""
from collections import deque
import numpy as np
from .config import Common, PIConfig, MPCConfig


def v_model(R, J, b0, L0):
    R = np.maximum(R, 1.0)
    p = np.minimum(1.0, R * J / b0)
    return R * (J + p * L0) / p


class BiasObserver:
    """EWMA of ln(V_measured) - ln(V_model over the same 10 s window): absorbs model error (p, L, floor)."""

    def __init__(self, c: Common, alpha: float):
        self.c, self.alpha = c, alpha
        self.h = deque(maxlen=c.window_ticks)
        self.b = 0.0
        self.init = False

    def update(self, R_tick, J_applied, lnV):
        c = self.c
        self.h.append((R_tick, J_applied))
        if self.alpha <= 0 or len(self.h) < self.h.maxlen or lnV is None:
            return self.b
        R = np.array([x[0] for x in self.h]); J = np.array([x[1] for x in self.h])
        Rm = np.maximum(R, 1.0)
        p = np.minimum(1.0, Rm * J / c.b0_B)
        rate = p / (J + p * c.L0_s)                 # syncs per second in each tick
        v_win = Rm.sum() / max(rate.sum(), 1e-9)    # bytes / syncs over the window
        raw = float(lnV - np.log(v_win))
        self.b = raw if not self.init else self.alpha * raw + (1 - self.alpha) * self.b
        self.init = True
        return self.b


class PIController:
    """PI on e = ln V* - ln V (lagged sensor). ff=True adds a feedforward from the fast load estimate."""
    name = "pi"

    def __init__(self, common: Common, cfg: PIConfig):
        self.c, self.p = common, cfg
        self.reset()

    def reset(self):
        self.sigma, self.yf, self.J_prev, self.sat_ticks = 0.0, None, self.c.j_init, 0
        self.Rf = None
        self.obs_b = BiasObserver(self.c, self.p.bias_alpha)

    def step(self, obs):
        c, p = self.c, self.p
        lnV = None if obs["V"] is None else float(np.log(obs["V"]))
        b = self.obs_b.update(obs["R_tick"], self.J_prev, lnV)
        self.Rf = obs["R_tick"] if self.Rf is None else p.ff_alpha * obs["R_tick"] + (1 - p.ff_alpha) * self.Rf
        if lnV is None:
            return self.J_prev
        self.yf = lnV if self.yf is None else p.filter_alpha * lnV + (1 - p.filter_alpha) * self.yf
        e = np.log(c.v_star_B) - self.yf
        if p.ff and self.Rf:
            j_ff = np.clip(c.v_star_B * np.exp(-b) / max(self.Rf, 1.0) - c.L0_s, c.j_min, c.j_max)
            u0 = np.log(j_ff)
        else:
            u0 = np.log(c.j_init)
        s = self.sigma + c.dt * e
        if p.antiwindup == "clamp":
            s = float(np.clip(s, -p.i_max, p.i_max))
        u = u0 + p.kp * e + p.ki * s
        u_sat = float(np.clip(u, np.log(c.j_min), np.log(c.j_max)))
        if p.antiwindup == "backcalc" and p.ki > 1e-9:
            s += c.dt * p.kt * (u_sat - u) / p.ki
        if abs(u_sat - u) > 1e-12:
            self.sat_ticks += 1
        self.sigma = s
        self.J_prev = float(np.exp(u_sat))
        return self.J_prev


class _Forecaster:
    """Forecast of a scalar series (here ln R): persistence = flat EWMA level; ma = level + LS slope;
    arima = ARIMA(1,1,0) fitted by least squares on the window."""

    def __init__(self, kind, window, alpha):
        self.kind, self.alpha = kind, alpha
        self.hist = deque(maxlen=window + 1)
        self.level = None

    def update(self, y):
        self.hist.append(y)
        self.level = y if self.level is None else self.alpha * y + (1 - self.alpha) * self.level

    def forecast(self, H):
        h = np.asarray(self.hist, float)
        i = np.arange(1, H + 1)
        if self.kind == "persistence" or len(h) < 4:
            return np.full(H, self.level)
        if self.kind == "ma":
            slope = np.polyfit(np.arange(len(h)), h, 1)[0]
            return self.level + i * slope
        if self.kind == "arima":
            d = np.diff(h)
            den = float(np.dot(d[:-1], d[:-1]))
            phi = float(np.clip(np.dot(d[:-1], d[1:]) / den, -0.95, 0.95)) if den > 1e-12 else 0.0
            return h[-1] + d[-1] * np.cumsum(phi ** i)
        raise ValueError(self.kind)


class MPCController:
    """Chooses u = ln J minimising  sum_i w_i * s(e_i) e_i^2 + lam (u - u_prev)^2 ,
    e_i = ln V* - [ln v_model(exp(f_i), J) + bias],  f_i = forecast of ln R,  s = under_weight if e>0 else 1.
    Grid search on u followed by golden-section refinement (continuous solution)."""
    name = "mpc"

    def __init__(self, common: Common, cfg: MPCConfig):
        self.c, self.p = common, cfg
        self.w = cfg.gamma ** np.arange(cfg.horizon)
        self.ugrid = np.linspace(np.log(common.j_min), np.log(common.j_max), 121)
        self.reset()

    def reset(self):
        self.fc = _Forecaster(self.p.predictor, self.p.window, self.p.ewma_alpha)
        self.obs_b = BiasObserver(self.c, self.p.bias_alpha)
        self.J_prev, self.sat_ticks = self.c.j_init, 0

    def _cost(self, u, Rtil, b, u_prev):
        c, p = self.c, self.p
        J = np.exp(u)
        e = np.log(c.v_star_B) - (np.log(v_model(Rtil, J, c.b0_B, c.L0_s)) + b)
        s = np.where(e > 0, p.under_weight, 1.0)
        return float(np.sum(self.w * s * e ** 2) + p.lam * (u - u_prev) ** 2)

    def step(self, obs):
        c = self.c
        lnV = None if obs["V"] is None else float(np.log(obs["V"]))
        b = self.obs_b.update(obs["R_tick"], self.J_prev, lnV)
        self.fc.update(float(np.log(max(obs["R_tick"], 1.0))))
        if lnV is None:
            return self.J_prev
        Rtil = np.exp(self.fc.forecast(self.p.horizon))
        u_prev = np.log(self.J_prev)
        # vectorised grid
        J = np.exp(self.ugrid)
        e = np.log(c.v_star_B) - (np.log(v_model(Rtil[:, None], J[None, :], c.b0_B, c.L0_s)) + b)
        s = np.where(e > 0, self.p.under_weight, 1.0)
        cost = (self.w[:, None] * s * e ** 2).sum(0) + self.p.lam * (self.ugrid - u_prev) ** 2
        k = int(np.argmin(cost))
        lo, hi = self.ugrid[max(k - 1, 0)], self.ugrid[min(k + 1, len(self.ugrid) - 1)]
        gr = 0.6180339887
        x1, x2 = hi - gr * (hi - lo), lo + gr * (hi - lo)
        f1, f2 = self._cost(x1, Rtil, b, u_prev), self._cost(x2, Rtil, b, u_prev)
        for _ in range(25):
            if f1 < f2:
                hi, x2, f2 = x2, x1, f1
                x1 = hi - gr * (hi - lo); f1 = self._cost(x1, Rtil, b, u_prev)
            else:
                lo, x1, f1 = x1, x2, f2
                x2 = lo + gr * (hi - lo); f2 = self._cost(x2, Rtil, b, u_prev)
        u = 0.5 * (lo + hi)
        if self._cost(u, Rtil, b, u_prev) > cost[k]:
            u = float(self.ugrid[k])
        u = float(np.clip(u, np.log(c.j_min), np.log(c.j_max)))
        if u <= np.log(c.j_min) + 1e-9 or u >= np.log(c.j_max) - 1e-9:
            self.sat_ticks += 1
        self.J_prev = float(np.exp(u))
        return self.J_prev


def build_controller(common: Common, spec: dict):
    s = dict(spec)
    kind = s.pop("type")
    if kind == "pi":
        return PIController(common, PIConfig(**s))
    if kind == "mpc":
        return MPCController(common, MPCConfig(**s))
    raise ValueError(kind)
