# 0003 — The LLM emits a typed spec; deterministic code writes every artifact

**Status:** accepted · 2026-08-20

## Context

We generate `liara.json`, Dockerfiles, nginx configs, hooks and CI workflows for a user's
stack. The obvious implementation asks the model to write the file.

## Decision

The model emits a **typed `DeploymentSpec`** — platform, version, plan, deploy path,
database, needs_disk/cron/healthcheck/nginx — which is itself schema-validated. A
deterministic renderer expands that spec through templates into files. **The model never
writes config text.**

## Why

A model that cannot type a key into a file cannot hallucinate one. This converts the
largest fabrication surface in the product from a prompt-engineering problem into a type
system. The field space is genuinely closed — enums, integers, a fixed file set, a plan
table — so 85–90% of what matters is decidable deterministically.

The stakes are asymmetric. A confidently-formatted patch that is wrong for the user's
deploy path costs more of the 80-point answer-quality budget than ten cautious answers,
because it converts "cited the right doc" into "told me to break my deploy". And the
judges are Liara's own engineers.

## The risk this does not remove

Generator and validator are built from the **same harvest of the same prose docs**, so a
misreading is correlated — the generator emits the wrong thing and the validator blesses
it. That is strictly worse than guessing, because it removes the user's suspicion. Liara's
own published samples contain bugs we could inherit (a `healthCheck` sample where
`interval: 30` means 30 milliseconds; a workflow triggering on `main` while testing
`refs/heads/master`).

Mitigation is **scoping the claim, not widening coverage**: every check names what it
compared and cites the doc URL; checks that did not run render as "not checked" and are
never folded into the pass count; the summary says "12 checks ran, 3 areas unverified"
rather than "validated"; and the rule table is versioned so a later contradiction is a
data change with a test.

## Also decided

Never emit a diff unless **platform and deploy path are both known** — parsed from the
artifact, taken from the saved profile, or obtained by asking exactly one question.
Adding `app`/`platform` to `liara.json` is correct on the CLI and Console paths and
**fails the deploy on the GitHub path**.
