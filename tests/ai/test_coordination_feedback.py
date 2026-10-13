import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from diplomacy import Game
from ai_bot.coordination import coordination_issues
from ai_bot.feedback import Feedback
from ai_bot.ollama import ModelError
from ai_bot.player import Player


class CoordinationTests(unittest.TestCase):
    def test_conflicts(self):
        cases = [
            ['A PAR - BUR', 'A MAR - BUR'],
            ['A PAR - BUR', 'A BUR H'],
            ['A PAR - BUR', 'A BUR - PAR'],
            ['A PAR S A MAR - BUR', 'A MAR - SPA'],
            ['A PAR S A BUR', 'A BUR - MUN'],
            ['F ENG C A LON - BEL', 'A LON H'],
            ['F ENG C A LON - BEL', 'A LON - WAL'],
            ['F ENG C A LON - BEL', 'A LON - BEL'],
        ]
        for orders in cases:
            with self.subTest(orders=orders):
                self.assertTrue(coordination_issues(orders))

    def test_coherent_sets_and_coasts(self):
        cases = [
            ['A PAR S A MAR - BUR', 'A MAR - BUR'],
            ['A PAR S A BUR', 'A BUR S A MUN'],
            ['A PAR - BUR', 'A BUR - MUN', 'A MUN - TYR'],
            ['F ENG C A LON - BEL', 'A LON - BEL VIA'],
            ['A LON - BEL VIA', 'A BEL - LON VIA'],
            ['F MAO S F WES - SPA', 'F WES - SPA/SC'],
            ['A PAR S A BUR - MUN'],  # Foreign support cannot be matched locally.
        ]
        for orders in cases:
            with self.subTest(orders=orders):
                self.assertFalse(coordination_issues(orders))
        self.assertTrue(coordination_issues(['F MAO - SPA/NC', 'F WES - SPA/SC']))

    def test_legal_but_conflicting_model_falls_back_or_fails_closed(self):
        game = Game()
        holds = ['A PAR H', 'A MAR H', 'F BRE H']
        model = Mock()
        model.orders.return_value = ['A PAR - BUR', 'A MAR - BUR', 'F BRE H']
        with patch('ai_bot.player.choose_orders', return_value=holds):
            self.assertEqual(Player(model, log=lambda _: None)(game, 'FRANCE'), holds)
            with self.assertRaises(ModelError):
                Player(model, fallback=False, log=lambda _: None)(game, 'FRANCE')


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = Feedback(Path(self.directory.name) / 'feedback.private.json')
        self.key = self.store.key('http://test/api.php', 5, 'FRANCE')
        self.game = Game()
        self.orders = ['A PAR - BUR', 'A MAR - SPA', 'F BRE - MAO']

    def test_submission_survives_new_player_and_reports_observations(self):
        model = Mock()
        model.orders.return_value = self.orders
        player = Player(model, feedback=self.store, log=lambda _: None)
        player.begin_turn('http://test/api.php', 5, self.game, 'FRANCE')
        player(self.game, 'FRANCE')
        self.assertFalse(self.store.path.exists())  # Selection/dry-run never saves.
        player.submitted(self.game, 'FRANCE', self.orders)
        self.game.set_units('FRANCE', ['A PAR', 'A SPA', 'F MAO'])
        self.game.set_current_phase('F1901M')
        next_model = Mock()
        next_model.orders.return_value = ['A PAR H', 'A SPA H', 'F MAO H']
        restarted = Player(next_model, feedback=Feedback(self.store.path), log=lambda _: None)
        restarted.begin_turn('http://test/api.php', 5, self.game, 'FRANCE')
        restarted(self.game, 'FRANCE')
        feedback = next_model.orders.call_args.args[0]['previous_turn']
        self.assertEqual(feedback['submitted_orders'], self.orders)
        self.assertEqual([m['own_unit_at_destination'] for m in feedback['move_observations']],
                         [False, True, True])
        self.assertEqual(feedback['centers_gained'], [])

    def test_scoping_same_phase_stale_and_corrupt_records(self):
        self.store.save(self.key, self.game, 'FRANCE', self.orders)
        self.assertIsNone(self.store.previous(self.key, self.game, 'FRANCE'))
        self.game.set_current_phase('F1901M')
        for key in [self.store.key('other', 5, 'FRANCE'),
                    self.store.key('http://test/api.php', 6, 'FRANCE'),
                    self.store.key('http://test/api.php', 5, 'GERMANY')]:
            self.assertIsNone(self.store.previous(key, self.game, 'FRANCE'))
        self.game.set_current_phase('S1902M')
        self.assertIsNone(self.store.previous(self.key, self.game, 'FRANCE'))
        for content in ['broken', '[]', json.dumps({self.key: {'phase': 'F1901M', 'orders': [1]}})]:
            self.store.path.write_text(content)
            self.assertIsNone(self.store.previous(self.key, self.game, 'FRANCE'))

    def test_fall_to_spring_center_changes_and_retreat_build_do_not_overwrite(self):
        self.game.set_current_phase('F1901M')
        self.store.save(self.key, self.game, 'FRANCE', self.orders)
        player = Player(Mock(), feedback=self.store)
        player.begin_turn('http://test/api.php', 5, self.game, 'FRANCE')
        self.game.set_current_phase('W1901A')
        player.submitted(self.game, 'FRANCE', ['A PAR B'])
        self.game.set_current_phase('S1902M')
        self.game.set_centers('FRANCE', ['PAR', 'BRE', 'SPA'], reset=True)
        feedback = self.store.previous(self.key, self.game, 'FRANCE')
        self.assertEqual(feedback['centers_gained'], ['SPA'])
        self.assertEqual(feedback['centers_lost'], ['MAR'])

    def test_save_failure_does_not_turn_successful_submission_into_error(self):
        messages = []
        player = Player(Mock(), feedback=self.store, log=messages.append)
        player.begin_turn('http://test/api.php', 5, self.game, 'FRANCE')
        with patch.object(self.store, 'save', side_effect=OSError('private path')):
            player.submitted(self.game, 'FRANCE', self.orders)
        self.assertIn('could not be saved', messages[0])
        self.assertNotIn('private path', messages[0])
