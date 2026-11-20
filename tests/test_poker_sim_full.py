import unittest

from poker_sim_full import (
    Card,
    best_hand_score,
    calculate_odds,
    calculate_outs,
    compare_hands,
    hand_rank,
    parse_card,
    simulate_win_rate,
)


def cards(card_text: str) -> list[Card]:
    return [parse_card(card) for card in card_text.split()]


class PokerSimulatorTests(unittest.TestCase):
    def test_detects_royal_flush(self):
        self.assertEqual(hand_rank(cards("As Ks Qs Js Ts")), "Royal Flush")

    def test_detects_wheel_straight(self):
        self.assertEqual(best_hand_score(cards("As 2d 3c 4h 5s")), (4, (5,)))

    def test_pair_kicker_breaks_ties(self):
        ace_pair_king_kicker = cards("As Ad Kc 7h 3s")
        ace_pair_queen_kicker = cards("Ah Ac Qd 7c 3d")
        self.assertEqual(compare_hands(ace_pair_king_kicker, ace_pair_queen_kicker), 1)

    def test_seven_card_hand_uses_best_five_cards(self):
        seven_cards = cards("Ah As Ad Kc Kh 2c 3d")
        self.assertEqual(hand_rank(seven_cards), "Full House")
        self.assertEqual(best_hand_score(seven_cards), (6, (14, 13)))

    def test_duplicate_cards_are_rejected(self):
        with self.assertRaises(ValueError):
            hand_rank(cards("As As Kc Qh Jd"))

    def test_simulation_rates_sum_to_one(self):
        result = simulate_win_rate(cards("As Ah"), num_simulations=250, seed=7)
        observed_total = result["win_rate"] + result["tie_rate"] + result["loss_rate"]
        self.assertAlmostEqual(observed_total, 1.0)
        self.assertGreaterEqual(result["equity"], result["win_rate"])

    def test_outs_include_improving_cards(self):
        player_hand = cards("Ah Kh")
        board = cards("Qh Jh 2c")
        outs_count, outs_cards = calculate_outs(player_hand, board)
        self.assertGreater(outs_count, 0)
        self.assertIn(Card("T", "h"), outs_cards)

    def test_one_card_odds(self):
        self.assertAlmostEqual(calculate_odds(9, 47), 19.1489361702)


if __name__ == "__main__":
    unittest.main()
