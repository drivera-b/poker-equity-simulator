from collections import Counter
from dataclasses import dataclass
from itertools import combinations
import math
import random
from typing import Iterable, List, Sequence

RANKS = "23456789TJQKA"
SUITS = "cdhs"
RANK_VALUES = {r: i for i, r in enumerate(RANKS, start=2)}
HAND_CATEGORIES = (
    "High Card",
    "One Pair",
    "Two Pair",
    "Three of a Kind",
    "Straight",
    "Flush",
    "Full House",
    "Four of a Kind",
    "Straight Flush",
    "Royal Flush",
)
HandScore = tuple[int, tuple[int, ...]]


@dataclass(order=True, frozen=True)
class Card:
    rank: str
    suit: str

    def __post_init__(self):
        normalized_rank = self.rank.upper()
        normalized_suit = self.suit.lower()
        object.__setattr__(self, "rank", normalized_rank)
        object.__setattr__(self, "suit", normalized_suit)

        if normalized_rank not in RANKS or normalized_suit not in SUITS:
            raise ValueError(f"Invalid card: {self.rank}{self.suit}")

    def __str__(self):
        return f"{self.rank}{self.suit}"


def build_standard_deck() -> List[Card]:
    return [Card(rank, suit) for rank in RANKS for suit in SUITS]


class Deck:
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        self.cards: List[Card] = build_standard_deck()
        self.shuffle()

    def shuffle(self):
        self.rng.shuffle(self.cards)

    def deal(self, num_cards: int) -> List[Card]:
        if num_cards > len(self.cards):
            raise ValueError("Not enough cards left to deal")
        dealt = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt

    def __len__(self):
        return len(self.cards)

    def reset(self):
        self.__init__()


def parse_card(card_text: str) -> Card:
    text = card_text.strip()
    if len(text) != 2:
        raise ValueError(f"Cards must use two-character notation, like As or Td: {card_text}")
    return Card(text[0], text[1])


def validate_unique_cards(cards: Sequence[Card]) -> None:
    if len(set(cards)) != len(cards):
        duplicates = [str(card) for card, count in Counter(cards).items() if count > 1]
        raise ValueError(f"Duplicate card(s): {', '.join(duplicates)}")


def _straight_high_card(rank_values: Iterable[int]) -> int | None:
    unique_ranks = sorted(set(rank_values), reverse=True)
    for i in range(len(unique_ranks) - 4):
        window = unique_ranks[i : i + 5]
        if window[0] - window[-1] == 4:
            return window[0]

    if {14, 5, 4, 3, 2}.issubset(unique_ranks):
        return 5

    return None


def evaluate_five_card_hand(hand: Sequence[Card]) -> HandScore:
    if len(hand) != 5:
        raise ValueError("Exactly five cards are required for five-card evaluation")

    validate_unique_cards(hand)

    rank_nums = [RANK_VALUES[card.rank] for card in hand]
    counts = Counter(rank_nums)
    count_values = sorted(counts.values(), reverse=True)
    is_flush = len({card.suit for card in hand}) == 1
    straight_high = _straight_high_card(rank_nums)

    if straight_high and is_flush:
        if straight_high == 14:
            return (9, (14,))
        return (8, (straight_high,))

    if count_values == [4, 1]:
        quad_rank = max(rank for rank, count in counts.items() if count == 4)
        kicker = max(rank for rank, count in counts.items() if count == 1)
        return (7, (quad_rank, kicker))

    if count_values == [3, 2]:
        trip_rank = max(rank for rank, count in counts.items() if count == 3)
        pair_rank = max(rank for rank, count in counts.items() if count == 2)
        return (6, (trip_rank, pair_rank))

    if is_flush:
        return (5, tuple(sorted(rank_nums, reverse=True)))

    if straight_high:
        return (4, (straight_high,))

    if count_values == [3, 1, 1]:
        trip_rank = max(rank for rank, count in counts.items() if count == 3)
        kickers = sorted((rank for rank, count in counts.items() if count == 1), reverse=True)
        return (3, (trip_rank, *kickers))

    if count_values == [2, 2, 1]:
        pair_ranks = sorted((rank for rank, count in counts.items() if count == 2), reverse=True)
        kicker = max(rank for rank, count in counts.items() if count == 1)
        return (2, (*pair_ranks, kicker))

    if count_values == [2, 1, 1, 1]:
        pair_rank = max(rank for rank, count in counts.items() if count == 2)
        kickers = sorted((rank for rank, count in counts.items() if count == 1), reverse=True)
        return (1, (pair_rank, *kickers))

    return (0, tuple(sorted(rank_nums, reverse=True)))


def best_hand_score(cards: Sequence[Card]) -> HandScore:
    if not 5 <= len(cards) <= 7:
        raise ValueError("Best-hand evaluation requires 5 to 7 cards")

    validate_unique_cards(cards)
    return max(evaluate_five_card_hand(combo) for combo in combinations(cards, 5))


def best_five_card_hand(cards: Sequence[Card]) -> tuple[str, List[Card], HandScore]:
    if not 5 <= len(cards) <= 7:
        raise ValueError("Best-hand evaluation requires 5 to 7 cards")

    validate_unique_cards(cards)
    scored_hands = [(evaluate_five_card_hand(combo), list(combo)) for combo in combinations(cards, 5)]
    score, best_cards = max(scored_hands, key=lambda item: item[0])
    return HAND_CATEGORIES[score[0]], best_cards, score


def hand_rank(hand: Sequence[Card]) -> str:
    return HAND_CATEGORIES[best_hand_score(hand)[0]]


def hand_rank_value(name: str) -> int:
    return HAND_CATEGORIES.index(name)


def compare_hands(first: Sequence[Card], second: Sequence[Card]) -> int:
    first_score = best_hand_score(first)
    second_score = best_hand_score(second)
    return (first_score > second_score) - (first_score < second_score)


def simulate_win_rate(
    player_hand: Sequence[Card],
    num_simulations: int = 1000,
    community_cards: Sequence[Card] | None = None,
    num_opponents: int = 1,
    seed: int | None = None,
) -> dict:
    if len(player_hand) != 2:
        raise ValueError("Texas Hold'em simulations require exactly two player hole cards")
    if num_simulations <= 0:
        raise ValueError("num_simulations must be positive")
    if num_opponents <= 0:
        raise ValueError("num_opponents must be positive")

    known_community = list(community_cards or [])
    if len(known_community) > 5:
        raise ValueError("At most five community cards are allowed")

    player_cards = list(player_hand)
    known_cards = player_cards + known_community
    validate_unique_cards(known_cards)

    cards_needed = (2 * num_opponents) + (5 - len(known_community))
    base_deck = [card for card in build_standard_deck() if card not in known_cards]
    if cards_needed > len(base_deck):
        raise ValueError("Not enough unseen cards left for this simulation")

    wins = ties = losses = 0
    equity_total = 0.0
    rng = random.Random(seed)

    for _ in range(num_simulations):
        deck = base_deck.copy()
        rng.shuffle(deck)
        draw_index = 0

        opponent_hands = []
        for _ in range(num_opponents):
            opponent_hands.append(deck[draw_index : draw_index + 2])
            draw_index += 2

        board = known_community + deck[draw_index : draw_index + (5 - len(known_community))]
        scores = [best_hand_score(player_cards + board)]
        scores.extend(best_hand_score(opponent + board) for opponent in opponent_hands)

        top_score = max(scores)
        if scores[0] == top_score:
            tied_players = scores.count(top_score)
            equity_total += 1 / tied_players
            if tied_players == 1:
                wins += 1
            else:
                ties += 1
        else:
            losses += 1

    total = float(num_simulations)
    return {
        "win_rate": wins / total,
        "tie_rate": ties / total,
        "loss_rate": losses / total,
        "equity": equity_total / total,
        "wins": wins,
        "ties": ties,
        "losses": losses,
        "num_simulations": num_simulations,
        "num_opponents": num_opponents,
    }


def calculate_outs(player_hand: Sequence[Card], community_cards: Sequence[Card]) -> tuple[int, List[Card]]:
    known_cards = list(player_hand) + list(community_cards)
    if len(player_hand) != 2:
        raise ValueError("Out calculations require exactly two player hole cards")
    if len(known_cards) < 5:
        raise ValueError("Out calculations require at least the flop")
    if len(known_cards) >= 7:
        return 0, []

    validate_unique_cards(known_cards)
    deck = [card for card in build_standard_deck() if card not in known_cards]
    current_score = best_hand_score(known_cards)
    outs_cards = []

    for card in deck:
        new_hand = list(player_hand) + list(community_cards) + [card]
        if best_hand_score(new_hand) > current_score:
            outs_cards.append(card)

    return len(outs_cards), outs_cards


def calculate_odds(outs: int, unseen_cards: int = 47) -> float:
    if unseen_cards == 0:
        return 0.0
    return (outs / unseen_cards) * 100


def confidence_interval(proportion: float, trials: int, z_score: float = 1.96) -> tuple[float, float]:
    if trials <= 0:
        raise ValueError("trials must be positive")

    standard_error = math.sqrt((proportion * (1 - proportion)) / trials)
    margin = z_score * standard_error
    return max(0.0, proportion - margin), min(1.0, proportion + margin)


def format_cards(cards: Sequence[Card]) -> str:
    return " ".join(str(card) for card in cards)


if __name__ == "__main__":
    my_hand = [Card("A", "s"), Card("K", "s")]
    result = simulate_win_rate(my_hand, num_simulations=1000, seed=42)
    print(f"Simulated win/tie/loss rates for {my_hand[0]}, {my_hand[1]}:")
    print(result)
