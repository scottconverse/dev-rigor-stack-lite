# GauntletGate golden eval

This is GauntletGate **gating itself** — the most credible proof the tool works,
and the exit gate for every change to this repo (nothing ships "done" until it
passes).

## What it is

- `sample-app/app.py` — a tiny app with a **genuine** first-run dead-end: the core
  action (Create) is disabled and the setup copy says "install it yourself" **when
  the backend dependency is absent.** The dead-end is driven by a real dependency
  check, not mocked.
- `run_eval.py` — constructs the **real** dependency-absent state (it scrubs the
  dependency env var, it does not fake it), serves the app, fetches it as a brand-new
  user, and asserts the core action is **disabled** with a dead-end marker — the exact
  condition a correct Walkthrough lane reports as a **Blocker → DO NOT ADVANCE.** It
  then asserts the dependency-present state *is* reachable. It writes an artifact
  bundle (captured HTML for both states + `verdict.json`) to `eval/artifacts/`.

Run it:

```bash
python eval/run_eval.py        # exit 0 = passed
```

## What it proves — and what it doesn't (honest boundary)

**It proves**, deterministically and with no browser or LLM in the loop, that the
first-run dead-end is **real and detectable** by a new-user request with the
dependency genuinely absent — i.e. a correctly-executed Walkthrough lane *would*
return DO NOT ADVANCE. It also includes a **theater guard**: if the absent state
isn't a dead-end (or the present state is also blocked), the fixture is broken and
the eval **fails** — so the test can't pass vacuously. The fixture obeys GauntletGate's
own first-run discipline: it constructs the absent state for real and emits the same
kind of observable artifact the attestation requires.

**It does not** exercise an LLM agent's judgment — it doesn't prove a given agent
*will* run the Walkthrough lane correctly. That is the **live agent eval** below.

## Live agent eval (manual)

In an agent session with the skill installed:

1. Start the sample app with the dependency **absent**:
   `python eval/sample-app/app.py 8799` (do **not** set `GAUNTLET_SAMPLE_BACKEND`).
2. Run `gauntletgate walkthrough` pointed at `http://127.0.0.1:8799`.
3. **Expected:** the run constructs/verifies the dependency-absent first-run state,
   finds the core action unreachable, files it as a **Blocker**, and the verdict is
   **DO NOT ADVANCE** with a valid environment attestation.

If the agent reports anything other than DO NOT ADVANCE for the absent state, that is
a finding against the agent's execution of the skill — exactly the kind of gap
GauntletGate exists to surface.
