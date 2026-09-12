# Statistical design and interpretation

Verified against: SciPy 1.18.0 documentation for the inference example;
design guidance is engine-independent. API claims below are [official];
design checks are curated from the attributed analysis/EDA sources.

## Contents

- Specify the estimand before the test
- Identity is not independence
- Missing outcomes change the population
- A narrow independent-means example
- Interpret the evidence, not a threshold

## Specify the estimand before the test

Write one sentence naming population, outcome, contrast, time window, and
weighting. Distinguish the following questions before choosing a calculation:

- The mean measurement across recorded events weights prolific subjects more.
- The mean of each participant's mean weights participants equally, even with
  unequal numbers of measurements. That is not an erroneous average of averages
  when participant weighting was specified.
- A population rate is total events divided by total eligible exposure. Average
  group rates only with the corresponding exposure weights.
- A paired change is the within-entity difference under a declared follow-up
  rule; separate pre/post means need not describe that paired population.

Do not silently switch from a mean difference to a rank/distribution question
because data is skewed. A nonparametric test is not a general-purpose repair
for an undefined estimand, selection bias, or dependent observations.

## Identity is not independence

Deduplicate acquisition/retransmission IDs globally before analysis. Two
observations with equal subject, timestamp, and value can be legitimate repeats;
only the declared record identity decides whether they are duplicates.

Map the design explicitly: row -> measurement -> participant -> household/site
or randomized cluster. Count independent units at the design level, not the row
level. Subject aggregation is appropriate for a subject-level summary; use a
repeated-measures/mixed or cluster-aware method when the longitudinal structure
itself is the question. Do not discard time structure merely to use a t-test.

For paired observations, align by identity and retain a pair-exclusion ledger.
For resampling, resample the independent units and keep their associated rows
or pairs together. For temporal dependence, choose a design-justified block
method rather than shuffling individual time points. A fixed random seed does
not make an invalid exchangeability assumption valid.

## Missing outcomes change the population

Keep an eligibility roster independent of observed measurements. An eligible
participant with only missing measurements belongs in the coverage denominator
but cannot contribute a measured participant mean without an assumption.

Report both the requested population and the actually observed estimand.
Complete-case analysis can be biased when observation depends on outcome or
group; similar missing percentages do not prove that the missing values are
ignorable. Distinguish unknown, not applicable, non-detect/censoring, instrument
failure, and true zero. A value below a detection limit is not automatically zero.

Default to a transparent observed-only estimate with coverage and limitations.
If a full-population inference is required, name the missingness assumptions and
run a plausible sensitivity analysis; do not manufacture precision with an
unexplained fill value. Preserve all-missing groups in the coverage report.

## A narrow independent-means example

For independent unit-level arrays `a` and `b`, when a mean contrast and Welch
assumptions are justified, SciPy 1.18.0 provides:

```python
from scipy import stats

result = stats.ttest_ind(a, b, equal_var=False, nan_policy="raise")
interval = result.confidence_interval(confidence_level=0.95)
print(result.statistic, result.pvalue, result.df)
print(interval.low, interval.high)
```

The effect and interval are for mean(a) minus mean(b). Prepare the arrays using
the declared missingness policy first; `nan_policy="raise"` makes leftover NaNs
an error rather than silently choosing a complete-case population. Verify sample
sizes and degeneracy before interpreting NaN or infinite results. Welch relaxes
equal variances, not independence or arbitrary small-sample distribution issues.
The confidence-interval method requires SciPy 1.11+; verify the installed API.

## Interpret the evidence, not a threshold

Report effect direction and units with uncertainty and independent-unit counts.
A p-value is a tail probability under the null model, not the probability that
the null is true, an effect exists, or a treatment caused the difference.
A non-significant result is not evidence of equivalence: equivalence needs a
pre-specified meaningful margin and an appropriate design/analysis.

List the hypothesis family when many outcomes or segments were examined. Use a
pre-specified multiplicity procedure for confirmatory claims; mark post hoc
patterns as exploratory instead of presenting the smallest p-value alone.
A significance threshold chosen after viewing results is not pre-specified.

Keep observed association separate from intervention effects. Check selection,
confounding, regression to the mean, seasonality, measurement changes, and
attrition before attributing a before/after change to the intervention. Neither
a very large dataset nor a tiny p-value resolves those identification problems.

Show sensitivity to influential valid observations, exclusion, and weighting
when those decisions could reverse the conclusion. Outlier flags are diagnostic,
not deletion permission. Explain uncertainty without inventing an interval when
the design or available data cannot support one.

<!-- sources: anthropic-data, kdense-eda, scipy-ttest -->
