"""Regression positions from England's logs, without changing legal orders."""
import unittest
from unittest.mock import Mock
from ai_bot.player import Player, legal_choices, validate_orders
from ai_bot.ollama import ModelError
from compare_engines import prepare
from scenarios import CASES


class ScenarioTests(unittest.TestCase):
    def test_shared_scenarios_use_legal_orders(self):
        for name, orders in CASES:
            with self.subTest(name=name):
                game = prepare(orders)
                for power, rows in orders.items():
                    validate_orders(rows, legal_choices(game, power))
                    game.set_orders(power, rows)
                game.process()

    def test_kiel_self_bounce_is_legal_but_does_not_advance(self):
        orders = dict(CASES)['kiel_self_bounce']
        game = prepare(orders)
        model = Mock()
        model.orders.return_value = orders['ENGLAND']
        # The game still permits a self-bounce; the model's planning policy avoids it.
        validate_orders(orders['ENGLAND'], legal_choices(game, 'ENGLAND'))
        with self.assertRaises(ModelError):
            Player(model, fallback=False, log=lambda _: None)(game, 'ENGLAND')
        game.set_orders('ENGLAND', orders['ENGLAND'])
        game.process()
        self.assertEqual(set(game.get_units('ENGLAND')), {'F HEL', 'F DEN'})

    def test_matching_support_can_capture_kiel(self):
        orders = dict(CASES)['kiel_supported_attack']
        game = prepare(orders)
        for power, rows in orders.items():
            game.set_orders(power, rows)
        game.process()
        self.assertIn('F KIE', game.get_units('ENGLAND'))
        self.assertIn('F KIE', game.powers['GERMANY'].retreats)

    def test_competing_supported_foreign_moves_bounce(self):
        orders = dict(CASES)['competing_foreign_support']
        game = prepare(orders)
        for power, rows in orders.items():
            game.set_orders(power, rows)
        game.process()
        self.assertEqual(set(game.get_units('FRANCE')), {'A MUN', 'A RUH'})
