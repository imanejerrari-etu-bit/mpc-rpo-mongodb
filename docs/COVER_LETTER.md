# Cover letter (draft: complete the bracketed items)

Dear Editor,

Please find enclosed our manuscript, "Load Feedforward, Not Prediction: An Empirical Comparison of PI and Model Predictive Control of the
MongoDB Journal Commit Interval under Load Bursts", for consideration in [JOURNAL].

**What the paper does.** Database engines expose a write-behind setting, the journal commit interval, that trades durability against write cost.
We ask whether a feedback or predictive controller can keep the volume of journal data not yet synchronised to disk near a target during write-load
bursts, and whether predicting the load helps. On MongoDB we derive the controlled variable from engine counters only, identify the plant, and compare
seven controllers in a pre-specified, interleaved, randomised design on a real cluster (135 valid runs, plus 81 runs of sensitivity analysis and a
24-run replication on a second platform).

**Main findings.** A tuned feedback-only PI controller has a burst error five to eight times larger than any controller that uses the observed load.
Model predictive control with persistence forecasting is statistically equivalent to a plain feedforward with a model-bias observer; moving-average
forecasting is worse and ARIMA brings no gain. The responsiveness of the load estimate is the parameter that matters; PI with feedforward has the lowest
nominal burst error on our main platform but loses stability with a 50 % higher gain, and its advantage over MPC did not replicate on the second platform.

**Relation to a previous submission.** An earlier version of this study was submitted to another journal and rejected. Its reviewers noted that the PI
baseline was untuned, had no anti-windup and no load information, that parameters were not varied or reported, that the signal was not defined, and that
the claimed decision criterion did not generalise across engines. We addressed each point by redoing the study from scratch (new experiments, new controlled
variable, new baselines including feedforward, equal tuning budget, sensitivity analysis, pre-specified statistics with multiplicity correction and equivalence
tests). The conclusion changed: the earlier claim that MPC outperforms PI does not hold once the PI uses the load. A point-by-point response is attached.

**Declarations.** The manuscript is not under consideration elsewhere. No funding was received. The authors declare no competing interests.
Code, schedules, 240+ run files and analysis scripts are available at https://github.com/imanejerrari-etu-bit/mpc-rpo-mongodb (release v1.0). [AI-assistance statement as required by the journal.]

**Limitations stated in the paper.** One engine; single-node deployments on two hosts; the signal measures exposure of journal data, not observed data
loss (no crash-recovery experiment); one run contains a journal-sync stall of unknown cause (analysed with and without it); the sensitivity analysis is
descriptive (n = 3 per variant).

Sincerely,
Imane Jerrari and Ismail Assayad
Laboratory of Information Systems, Faculty of Sciences Ain Chock, and ENSEM, Hassan II University of Casablanca
