# Project Process and Research Notes

## Original Question

The project asks a quantitative poker question:

> Given my hole cards and any known community cards, how often should this hand win against random opponents?

This is a natural Monte Carlo problem because many outcomes are possible, but each trial is easy to simulate by sampling from the remaining deck.

## Design Choices

- Represent cards with a small immutable `Card` dataclass.
- Remove known cards before every simulation so cards are sampled without replacement.
- Evaluate every five-card combination from a player's available cards instead of trying to write special-case seven-card logic.
- Compare full hand scores, not only category names, so an ace pair with a king kicker beats an ace pair with a queen kicker.
- Keep the Streamlit app separate from the core simulator so the math can be tested without launching the UI.

## Validation Work

The current test suite verifies important poker edge cases:

- Royal flush detection.
- Ace-low straight detection.
- Best five-card selection from seven cards.
- Kicker tie breakers.
- Duplicate-card validation.
- Simulation output accounting.
- Outs and odds calculations.

These tests protect the project from the most common poker-simulator mistake: calling two hands tied just because they have the same category.

## What Changed During Review

The reviewed version improves the project in several ways:

- Replaced category-only hand comparison with exact tuple scoring.
- Added optional known community cards to the Monte Carlo simulation.
- Added split-pot equity, which is more useful than raw win rate for quantitative analysis.
- Added a fixed random seed option for reproducible demonstrations.
- Added tests, dependency documentation, Git ignore rules, and a cleaner Streamlit interface.

## Recommended Extensions

- Add exact enumeration mode for turn and river spots where the remaining state space is small enough to compute exhaustively.
- Add convergence plots that show how the estimate stabilizes as trial count increases.
- Let users define opponent hand ranges instead of assuming random hands.
- Add CSV export for simulation results.
- Add a notebook with example research questions and charts.
- Add performance profiling or vectorized simulation for very large trial counts.
- Compare simulated pre-flop equities against known poker-equity references as an external validation check.

## Research Framing

This project is strongest when framed as a probability and simulation study. It demonstrates:

- Random sampling without replacement.
- Monte Carlo estimation.
- Reproducibility through seeded randomness.
- Discrete combinatorial evaluation.
- Empirical validation through tests and benchmark scenarios.
