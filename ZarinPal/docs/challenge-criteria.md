# Challenge success criteria

This document translates the official challenge description into product and delivery
requirements for this submission. Use it to prioritize features and to review whether a
slice is worth building. The product brief defines the product; the metric contracts
define calculations; this document defines how the submission will be judged.

## Required submission

The final submission must be an analytical product that uses the supplied dataset to
give ZarinPal merchants useful, actionable insights. A user must be able to inspect and
trace an analytical result to understand how its number or claim was derived from the
data.

Delivery requires:

- a link to the GitHub repository; and
- a demo video of at least five minutes that explains the product and every implemented
  feature, with all features demonstrated and tested on both mobile and desktop.

## Judging priorities

| Criterion | Points | What the product must demonstrate |
|---|---:|---|
| Actionability and originality of insights | 90 | Insights end in a specific quantified finding and an action the merchant can take. Analysis beyond the sample directions in the challenge brief is rewarded. |
| Accuracy and traceability | 75 | Every number and claim is derived from the data and can be investigated through the UI, including its source and calculation. |
| Analytical depth | 60 | Analysis uses multi-step reasoning such as hypothesis construction and testing, segmentation, relationships between variables, and control of confounding effects. |
| UX for a non-technical audience | 45 | A merchant can understand the main findings at a glance without interpreting raw data or complex charts. |
| Technical quality and executability | 30 | Architecture, code quality, project structure, run instructions, and real-world executability let a judge start and assess the project quickly. |

The score weighting is an explicit product priority. Prefer a smaller number of
original, defensible, actionable insight journeys over a larger collection of generic
charts. Technical polish supports the analysis but cannot substitute for it.

## Required dataset awareness

Analysis and presentation must explicitly account for:

- the dataset's payment-attempt grain rather than treating every row as a unique
  purchase, customer, or payment session;
- the concentration of volume among some merchants, which can make unweighted global
  comparisons misleading; and
- null values in some columns, including their effect on sample coverage and the
  reliability of a conclusion.

Merchant-visible analytics remain scoped to the authenticated merchant. Benchmarks or
cross-merchant aggregates require a separately authorized, privacy-safe definition and
must not allow another merchant's data to be inferred.

## What qualifies as an insight

A primary insight should answer this chain in plain language:

1. **Finding:** What changed or is abnormal?
2. **Magnitude:** How large is it, using a concrete number and an appropriate baseline?
3. **Concentration:** Which supported segment or condition contributes most?
4. **Action:** What specific next step can the merchant take?
5. **Evidence:** What calculation, population, assumptions, and limitations support it?
6. **Drill-down:** Which sessions or attempts contributed to the result?

Recommendations must not imply causality that the analysis did not establish. Label
estimates and hypotheses as such, state important coverage limitations, and distinguish
payment attempts from sessions, customers, purchases, and lost revenue.

## Feature review checklist

Before treating an analytics feature as submission-ready, verify that it:

- produces a quantified merchant-relevant conclusion, not only a visualization;
- suggests a feasible action or clearly supports a merchant decision;
- uses a documented metric definition and a reproducible comparison population;
- exposes formula, grain, numerator/denominator where applicable, filters, time basis,
  freshness, sample size, null handling, and known limitations;
- provides a path to the contributing sessions and ordered attempts;
- separates observed evidence from hypotheses, estimates, and causal claims;
- communicates the conclusion before asking the user to interpret a chart;
- works in Persian/RTL and English/LTR, light and dark themes, and mobile and desktop;
- includes representative tests and remains straightforward for a judge to run; and
- has a concise demo path that can be shown with realistic data on both viewport sizes.

Generic KPI cards and charts can provide context, but they do not satisfy the central
challenge requirement unless they participate in an actionable, traceable analytical
journey.
