import matplotlib.pyplot as plt
import streamlit as st

from poker_sim_full import (
    Card,
    best_five_card_hand,
    calculate_odds,
    calculate_outs,
    confidence_interval,
    format_cards,
    simulate_win_rate,
    validate_unique_cards,
)

SUITS = ["c", "d", "h", "s"]
SUIT_SYMBOLS = {"c": "Clubs", "d": "Diamonds", "h": "Hearts", "s": "Spades"}
RANKS = list("23456789TJQKA")
BOARD_DEFAULTS = [("2", "c"), ("7", "d"), ("T", "h"), ("4", "s"), ("Q", "c")]


def get_card_input(label_prefix: str, default_rank: str, default_suit: str) -> Card:
    rank = st.selectbox(
        f"{label_prefix} rank",
        RANKS,
        index=RANKS.index(default_rank),
        key=f"{label_prefix}_rank",
    )
    suit = st.selectbox(
        f"{label_prefix} suit",
        SUITS,
        format_func=lambda s: SUIT_SYMBOLS[s],
        index=SUITS.index(default_suit),
        key=f"{label_prefix}_suit",
    )
    return Card(rank, suit)


def render_rate_chart(result: dict) -> None:
    labels = ["Win", "Tie", "Loss", "Equity"]
    values = [
        result["win_rate"] * 100,
        result["tie_rate"] * 100,
        result["loss_rate"] * 100,
        result["equity"] * 100,
    ]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(labels, values, color=["#2f855a", "#b7791f", "#c53030", "#2b6cb0"])
    ax.set_ylim(0, 100)
    ax.set_ylabel("Percent")
    ax.set_title("Monte Carlo outcome distribution")
    ax.grid(axis="y", alpha=0.25)
    st.pyplot(fig)


def validate_selection(cards: list[Card]) -> bool:
    try:
        validate_unique_cards(cards)
    except ValueError as exc:
        st.error(str(exc))
        return False
    return True


st.set_page_config(page_title="Poker Equity Simulator", layout="wide")
st.title("Monte Carlo Poker Equity Simulator")
st.caption("MITES Semester research project: Texas Hold'em equity estimation with exact hand comparison.")

tab_simulator, tab_benchmark = st.tabs(["Simulator", "Benchmark"])

with tab_simulator:
    controls, results_panel = st.columns([0.95, 1.35])

    with controls:
        st.subheader("Scenario")
        hole_a, hole_b = st.columns(2)
        with hole_a:
            card1 = get_card_input("Hole card 1", "A", "s")
        with hole_b:
            card2 = get_card_input("Hole card 2", "K", "s")

        known_board_count = st.slider("Known community cards", 0, 5, 0, 1)
        community_cards = []
        if known_board_count:
            st.subheader("Community")
            for index in range(known_board_count):
                rank, suit = BOARD_DEFAULTS[index]
                community_cards.append(get_card_input(f"Board card {index + 1}", rank, suit))

        st.subheader("Simulation")
        num_simulations = st.slider("Trials", 500, 50000, 5000, 500)
        num_opponents = st.slider("Opponents", 1, 5, 1, 1)
        use_seed = st.checkbox("Use fixed random seed", value=True)
        seed = None
        if use_seed:
            seed = int(st.number_input("Seed", min_value=0, max_value=1_000_000, value=42, step=1))

        run_simulation = st.button("Run simulation", type="primary")

    with results_panel:
        selected_cards = [card1, card2] + community_cards
        st.subheader("Current Selection")
        st.write(f"Hole cards: **{format_cards([card1, card2])}**")
        if community_cards:
            st.write(f"Community: **{format_cards(community_cards)}**")
        else:
            st.write("Community: **pre-flop**")

        if run_simulation and validate_selection(selected_cards):
            try:
                result = simulate_win_rate(
                    [card1, card2],
                    num_simulations=int(num_simulations),
                    community_cards=community_cards,
                    num_opponents=int(num_opponents),
                    seed=seed,
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                low, high = confidence_interval(result["equity"], result["num_simulations"])

                metric_cols = st.columns(4)
                metric_cols[0].metric("Equity", f"{result['equity']:.2%}")
                metric_cols[1].metric("Win", f"{result['win_rate']:.2%}")
                metric_cols[2].metric("Tie", f"{result['tie_rate']:.2%}")
                metric_cols[3].metric("Loss", f"{result['loss_rate']:.2%}")
                st.caption(f"Approximate 95% confidence interval for equity: {low:.2%} to {high:.2%}")

                render_rate_chart(result)

                if len(selected_cards) >= 5:
                    category, best_cards, _ = best_five_card_hand(selected_cards)
                    st.success(f"Current made hand: {category} using {format_cards(best_cards)}")
                else:
                    st.info("Current made-hand evaluation begins after the flop.")

                if 3 <= len(community_cards) <= 4:
                    outs_count, outs_cards = calculate_outs([card1, card2], community_cards)
                    unseen_cards = 52 - len(selected_cards)
                    st.write(f"Outs that improve the current hand: **{outs_count}**")
                    st.write(f"One-card improvement odds: **{calculate_odds(outs_count, unseen_cards):.2f}%**")
                    if outs_cards:
                        st.caption(format_cards(outs_cards))
                elif len(community_cards) == 5:
                    st.info("The river is complete, so no future-card outs remain.")

with tab_benchmark:
    st.subheader("Starting Hand Benchmark")
    benchmark_trials = st.slider("Benchmark trials per hand", 500, 20000, 3000, 500)
    benchmark_hands = {
        "Pocket Aces": [Card("A", "s"), Card("A", "h")],
        "Ace-King suited": [Card("A", "s"), Card("K", "s")],
        "Queen-Jack suited": [Card("Q", "h"), Card("J", "h")],
        "Seven-Two offsuit": [Card("7", "c"), Card("2", "d")],
    }

    if st.button("Run benchmark"):
        rows = []
        for name, hand in benchmark_hands.items():
            result = simulate_win_rate(hand, num_simulations=int(benchmark_trials), seed=42)
            rows.append(
                {
                    "Hand": name,
                    "Cards": format_cards(hand),
                    "Equity": f"{result['equity']:.2%}",
                    "Win": f"{result['win_rate']:.2%}",
                    "Tie": f"{result['tie_rate']:.2%}",
                    "Loss": f"{result['loss_rate']:.2%}",
                }
            )
        st.table(rows)

    st.subheader("Model Notes")
    st.write(
        "The simulator randomly samples unknown opponent cards and community cards, evaluates every "
        "possible five-card poker hand from the available seven cards, and compares full tie-breaker "
        "scores instead of comparing only hand categories."
    )
