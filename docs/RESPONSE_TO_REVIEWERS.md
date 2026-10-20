# Response to the reviewers of the previous submission

*(Draft for the cover letter / the "response to previous reviews" field of the new journal. The previous version was rejected
by another journal; the reviewer reports are summarised below with the changes made. The study was redone from scratch: new
experiments, a new controlled variable, new baselines and a different conclusion. Section numbers refer to the new manuscript.)*

## Summary of what changed
1. **Different question and conclusion.** The earlier version reported that MPC outperformed PI. Reviewer 1 suspected that this
   depended on an untuned PI without anti-windup and without load information. We tested this directly: a PI that uses the
   observed load (feedforward) performs like MPC, and a feedback-only PI is 5 to 8 times worse in burst error. The earlier claim
   does not hold; the new claim is that **load information, not prediction or optimisation, explains the gain** (Sections 6, 7).
2. **Fair design.** Same tuning budget for every controller family, robust tuning, interleaved randomised runs, a pre-specified
   analysis (plus two dated amendments written before the data were seen), 135 valid runs on a real cluster and 81 runs of sensitivity analysis.
3. **Scope reduced to what was measured:** one engine (MongoDB), one knob, no claim about other engines.

## Reviewer 1 (control engineering, MPC)

| # | Comment | Response and location |
|---|---|---|
| 1.1 | Acronyms (RPO, SLA, EWMA) undefined. | RPO and SLA are defined at first use; exponential smoothing is described in words (Section 1, Section 4). |
| 1.2 | How is the proxy measured; how is measurement noise modelled? | The controlled variable is now computed from two engine counters only (Section 3.1) and never reads the commanded value. Its noise is characterised in Section 3.2 (Table 3): mostly count quantisation, 5.4--5.8 % at J = 500 ms down to 0.3--0.6 % at 20 ms; the load estimate has 1.6--3.6 % per-tick noise, close to white. |
| 1.3 | The problem is convex; a line search would do. | Agreed for the linear additive model. With the identified static law convexity is not guaranteed, so the solver is a dense grid followed by golden-section refinement of a continuous solution (Section 4). |
| 1.4 | MPC wins only under actuator saturation when the PI has no anti-windup. | The PI baselines now have clamp or back-calculation anti-windup, are tuned, and a low-load scenario where the target is unreachable tests saturation explicitly (Section 5; Table 7: recovery times). |
| 1.5 | More sophisticated predictions do worse than the PI; attributed to noise. | The new design separates the factors. Moving-average forecasting is worse than persistence (+1.12 percentage points, Holm p < 0.001); ARIMA is equivalent; persistence MPC is equivalent to feedforward with a bias observer (Sections 6, 7). The earlier attribution to noise is not retained. |
| 1.6 | Parameters of PI and MPC are never varied and not reported. | All parameters are reported (Table 5). Each family received the same random-search tuning budget on a calibrated simulator (60 candidates, robust objective). A sensitivity analysis varies every continuous parameter by x0.5 and x1.5 and the target V* (Section 6.1, Tables 8--9). |
| 1.7 | A PI can use feedforward. | Two feedforward baselines were added: PI with feedforward and feedforward with a model-bias observer (no feedback, no prediction). This is the most informative comparison of the study (Sections 4, 6). |

## Reviewer 2

| # | Comment | Response and location |
|---|---|---|
| 2.1 | Title and Section 1.3 suggest a general decision criterion; cross-engine results contradict it. | The criterion is withdrawn. The title names MongoDB; the scope and limits are stated in Sections 1 and 8. |
| 2.2 | Inconsistent number of runs; bootstrap on n = 5; "2.6x less accurate". | Every cell reports n (Table 2). Cell sizes were set from the pilot's variability (amendment 1). No ratio claim rests on a small bootstrap; contrasts use direct tests with effect sizes. |
| 2.3 | H = 1 with identity predictor is not "analogous to the proportional part of the PI". | Removed. We show instead that MPC with H = 1 reduces to feedforward with the observer (checked numerically) and that with a flat forecast H and the move penalty are redundant (Section 4). |
| 2.4 | Eq. (4) additive relation needs justification. | The actuator effect is identified: V follows R (J + pL)/p; in logarithms it is additive with gain close to 1 (fit exponents 1.001 and 0.959, error 1.4 %; Section 3.2, Table 2, Fig. 1). Caveat: the fit uses six points above the floor. |
| 2.5 | How was significance determined? Multiple comparisons? | Mann--Whitney tests, Cliff's delta, bootstrap CIs, Holm correction over 14 pre-specified tests; equivalence claims use TOST with margins fixed in advance (Section 5, Tables 3--4). Non-overlapping CIs are no longer used. |
| 2.6 | Saturation analysis is diagnostic, not a complete causal explanation. | We no longer claim a causal mechanism. Saturation appears as a scenario and as measured recovery times; the cause of the PI-FF fragility is stated as an unverified hypothesis (Section 8). |
| 2.7 | Burst experiments are on MongoDB only; limit the claim. | All experiments use the same engine and the burst scenario; the conclusion is explicitly limited to the scenarios, engine and platform tested (Sections 8, 9). |

## What remains open (stated in the manuscript)
One engine, single pod, one host; the signal measures exposure of journal data and no crash-recovery experiment verifies data loss; the
simulator underestimates noise and between-run variability; a 12.5 s journal-sync stall occurred in one run (analysed with and without it);
the sensitivity analysis is descriptive (n = 3 per variant). A second-platform replication on a free Linux runner is planned (amendment 3)
and, if completed before submission, will be reported.
