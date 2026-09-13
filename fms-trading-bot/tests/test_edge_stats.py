"""The statistics find_edge.py uses to say "edge" or "noise".

The live run of --days 60 reported liquidity_sweep as "beats noise" at
p = 0.010. It had tested thirteen strategies to get there and measured
its own noise rate from twelve shuffled runs. Both facts make that number
smaller than the evidence supports, and neither was in the arithmetic.
"""

from find_edge import (ALPHA, NULL_CONFIDENCE, binomial_at_least,
                       binomial_at_most, family_wise, null_rate_upper,
                       null_runs_needed, symbols_needed)

# The run that prompted these tests: 6 symbols, 2 null runs each.
SYMBOLS, NULL_TRIALS, STRATEGIES = 6, 12, 13


def test_binomial_tails_agree():
    for n in (6, 12, 30):
        for p in (0.05, 0.2, 0.5):
            for k in range(0, n + 1):
                total = binomial_at_least(k, n, p) + binomial_at_most(k - 1, n, p)
                assert abs(total - 1.0) < 1e-9, (n, p, k, total)


def test_never_claims_a_rate_of_zero_from_absence():
    """Not seeing a thing in 12 tries does not make it impossible."""
    bound = null_rate_upper(0, 12, NULL_CONFIDENCE)
    assert 0.1 < bound < 0.3, bound


def test_more_null_runs_sharpen_the_bound():
    """The bound is what extra shuffled runs actually buy."""
    bounds = [null_rate_upper(0, t, NULL_CONFIDENCE) for t in (12, 30, 60, 120)]
    assert bounds == sorted(bounds, reverse=True), bounds
    assert bounds[-1] < 0.03, bounds


def test_bound_sits_above_the_point_estimate():
    for hits, trials in ((1, 12), (2, 30), (5, 60)):
        assert null_rate_upper(hits, trials, NULL_CONFIDENCE) > hits / trials


def test_thirteen_strategies_inflate_a_lone_p_value():
    """Reporting the best of thirteen at face value is the classic error."""
    one = family_wise(0.05, 1)
    many = family_wise(0.05, STRATEGIES)
    assert abs(one - 0.05) < 1e-12, one
    assert many > 0.45, many


def test_the_live_verdict_does_not_survive_correction():
    """liquidity_sweep, 3 of 6 symbols, 1 null hit in 12 — the real run."""
    raw = binomial_at_least(3, SYMBOLS, 1 / NULL_TRIALS)
    assert raw < 0.01, raw                      # what the tool first reported
    corrected = family_wise(raw, STRATEGIES)
    assert corrected > ALPHA, corrected         # once the search is counted
    bound = null_rate_upper(1, NULL_TRIALS, NULL_CONFIDENCE)
    conservative = family_wise(binomial_at_least(3, SYMBOLS, bound), STRATEGIES)
    assert conservative > 0.5, conservative     # and the null is 12 samples


def test_widening_the_test_is_offered_when_deepening_it_cannot_work():
    """Three of six at a 10% noise rate needs more instruments, not more CPU."""
    wider = symbols_needed(3, SYMBOLS, STRATEGIES, 0.10)
    assert wider > SYMBOLS, wider
    need = round(3 / SYMBOLS * wider)
    assert family_wise(binomial_at_least(need, wider, 0.10), STRATEGIES) < ALPHA
    # a strategy that survived nowhere cannot be rescued by adding symbols
    assert symbols_needed(0, SYMBOLS, STRATEGIES, 0.10) == 0


def test_naming_one_strategy_in_advance_removes_the_penalty():
    """Why route 3 exists: the multiplicity cost is the search, not the data."""
    raw = binomial_at_least(3, SYMBOLS, 0.10)
    assert family_wise(raw, STRATEGIES) > ALPHA     # picked from 13
    assert family_wise(raw, 1) < ALPHA              # fixed in advance


def test_it_says_how_many_null_runs_would_settle_it():
    need = null_runs_needed(3, SYMBOLS, STRATEGIES)
    assert need > 2, need                       # more than the run that ran
    bound = null_rate_upper(0, need * SYMBOLS, NULL_CONFIDENCE)
    assert family_wise(binomial_at_least(3, SYMBOLS, bound), STRATEGIES) < ALPHA


def test_a_single_symbol_survivor_is_never_enough():
    """One hit out of six is the amount of luck the test expects to see."""
    for hits in (0, 1, 2):
        bound = null_rate_upper(hits, NULL_TRIALS, NULL_CONFIDENCE)
        p = family_wise(binomial_at_least(1, SYMBOLS, bound), STRATEGIES)
        assert p > ALPHA, (hits, p)


def test_hopeless_results_are_reported_as_hopeless():
    """One of six cannot be rescued by grinding more null runs.

    A weak result is not always hopeless — two of six is reachable, but
    only with 20-odd shuffled runs per symbol, and the tool says so rather
    than letting the user re-run at random and read the tea leaves again.
    """
    assert null_runs_needed(1, SYMBOLS, STRATEGIES) == 0
    assert null_runs_needed(2, SYMBOLS, STRATEGIES) > 15
    # the stronger the real result, the cheaper it is to confirm
    needs = [null_runs_needed(k, SYMBOLS, STRATEGIES) for k in (3, 4, 5, 6)]
    assert needs == sorted(needs, reverse=True), needs


def _render(per_strategy, null_hits, symbols=None, null_runs=2, tried=STRATEGIES):
    """Run the verdict printer and hand back what it printed."""
    import io
    from contextlib import redirect_stdout
    import find_edge
    buf = io.StringIO()
    with redirect_stdout(buf):
        find_edge.report(per_strategy, null_hits,
                         symbols or [f"SYM{i}" for i in range(SYMBOLS)],
                         tried, null_runs, 60)
    return buf.getvalue()


def test_the_verdict_prints_without_blowing_up_at_the_last_step():
    """The whole run is thrown away if this line raises. It has, before."""
    out = _render({"liquidity_sweep": ["EURUSDm", "USDJPYm", "XAUUSDm"],
                   "mean_reversion": ["EURUSDm"]},
                  {"liquidity_sweep": 1, "mean_reversion": 2})
    assert "VERDICT" in out
    assert "liquidity_sweep" in out
    for line in out.splitlines():
        assert len(line) < 80, line


def test_a_candidate_short_of_proof_is_named_as_such():
    out = _render({"liquidity_sweep": ["EURUSDm", "USDJPYm", "XAUUSDm"]},
                  {"liquidity_sweep": 1})
    assert "not proven" in out
    assert "NOTHING PROVEN" in out
    assert "beats noise" not in out
    # all three routes out, and the one that settles it named as such
    assert "More symbols" in out
    assert "--strategy liquidity_sweep" in out


def test_it_does_not_prescribe_the_run_that_just_happened():
    """The advice was "use 7 null runs" to someone who had just used 7.

    Four of 42 shuffled runs found the strategy in noise. More runs
    measure that 10% more precisely; they cannot make it smaller, and
    3 of 6 never beats 10% once 13 strategies are counted.
    """
    out = _render({"liquidity_sweep": ["EURUSDm", "USDJPYm", "XAUUSDm"]},
                  {"liquidity_sweep": 4}, null_runs=7)
    assert "NOT more shuffled runs" in out
    assert "--null-runs 8" not in out
    assert null_runs_needed(3, 6, STRATEGIES, hits=4, trials=42) == 0
    # and the same k/n IS rescuable when noise genuinely never produced it
    assert null_runs_needed(3, 6, STRATEGIES, hits=0, trials=12) > 2


def test_nothing_anywhere_still_says_no_edge_found():
    out = _render({}, {"pin_bar": 3})
    assert "NO EDGE FOUND" in out
    assert "not proven" not in out


def test_a_strong_result_is_allowed_to_pass():
    """The bar is high, not unreachable — a clean sweep clears it."""
    out = _render({"liquidity_sweep": [f"SYM{i}" for i in range(SYMBOLS)]},
                  {}, null_runs=5)
    assert "beats noise" in out
    assert "DEMO" in out
