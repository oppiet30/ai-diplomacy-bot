import io
import json
import unittest
from unittest.mock import Mock, patch
from urllib.error import URLError, HTTPError
from diplomacy import Game
from ai_bot.ollama import Ollama, ModelError
from ai_bot.player import Player, legal_choices, validate_orders


class PlayerTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.choices = legal_choices(self.game, 'FRANCE')
        self.holds = [unit + ' H' for unit in self.choices]

    def test_legal_complete_orders(self):
        self.assertEqual(validate_orders(self.holds, self.choices), self.holds)

    def test_invalid_missing_duplicate_foreign_orders(self):
        invalid = [None, 'A PAR H', [], self.holds[:-1],
                   [self.holds[0]] * 3, ['A MOS H'] + self.holds[1:],
                   ['A PAR - MOS'] + self.holds[1:], [1, 2, 3]]
        for orders in invalid:
            with self.subTest(orders=orders), self.assertRaises(ModelError):
                validate_orders(orders, self.choices)

    def test_model_receives_only_position_and_legal_choices(self):
        model = Mock()
        model.orders.return_value = self.holds
        self.assertEqual(Player(model, log=lambda _: None)(self.game, 'FRANCE'), self.holds)
        position = model.orders.call_args.args[0]
        self.assertEqual(set(position), {'power', 'phase', 'powers', 'legal_orders',
                                       'supply_centers', 'adjacency', 'baseline_orders',
                                       'baseline_coordination_issues', 'previous_turn'})
        self.assertEqual(position['legal_orders'], self.choices)
        # Neutral centers were absent from the original prompt's owned-center lists.
        owned = {center for state in position['powers'].values() for center in state['centers']}
        self.assertNotIn('BEL', owned)
        self.assertIn('BEL', position['supply_centers'])
        self.assertIn('BEL', position['adjacency']['PIC'])
        validate_orders(position['baseline_orders'], self.choices)

    def test_model_can_improve_on_baseline_or_hold_for_defense(self):
        model = Mock()
        alternative = ['A PAR - BUR', 'A MAR - SPA', 'F BRE - MAO']
        with patch('ai_bot.player.choose_orders', return_value=self.holds):
            model.orders.return_value = alternative
            self.assertEqual(Player(model, log=lambda _: None)(self.game, 'FRANCE'), alternative)
        model.orders.return_value = self.holds
        messages = []
        self.assertEqual(Player(model, log=messages.append)(self.game, 'FRANCE'), self.holds)
        self.assertTrue(any('all units holding' in line for line in messages))

    def test_invalid_model_uses_validated_fallback(self):
        model = Mock()
        model.orders.return_value = ['invented']
        with patch('ai_bot.player.choose_orders', return_value=self.holds) as baseline:
            self.assertEqual(Player(model, log=lambda _: None)(self.game, 'FRANCE'), self.holds)
            baseline.assert_called_once()

    def test_timeout_fallback_and_fail_closed(self):
        model = Mock()
        model.orders.side_effect = ModelError('timeout')
        with patch('ai_bot.player.choose_orders', return_value=self.holds):
            self.assertEqual(Player(model, log=lambda _: None)(self.game, 'FRANCE'), self.holds)
        with self.assertRaises(ModelError):
            Player(model, fallback=False)(self.game, 'FRANCE')

    def test_builds_use_baseline_without_model_call(self):
        self.game.set_current_phase('W1901A')
        model = Mock()
        with patch('ai_bot.player.choose_orders', return_value=[]) as baseline:
            self.assertEqual(Player(model, log=lambda _: None)(self.game, 'FRANCE'), [])
        model.orders.assert_not_called()
        baseline.assert_called_once()


class OllamaTests(unittest.TestCase):
    def model(self):
        return Ollama({'model': 'test-model', 'timeout_seconds': 10})

    def response(self, content, done=True):
        return io.BytesIO(json.dumps({'done': done, 'message': {'content': content}}).encode())

    def test_request_schema_and_no_auth_headers(self):
        model = self.model()
        model.opener = Mock()
        model.opener.open.return_value = self.response('{"orders": ["A PAR H"]}')
        self.assertEqual(model.orders({'power': 'FRANCE'}), ['A PAR H'])
        request = model.opener.open.call_args.args[0]
        body = json.loads(request.data)
        self.assertFalse(body['stream'])
        self.assertFalse(body['think'])
        self.assertEqual(body['format']['type'], 'object')
        self.assertNotIn('Authorization', request.headers)
        self.assertEqual(model.opener.open.call_args.kwargs['timeout'], 10)

    def test_malformed_and_incomplete_responses(self):
        for content, done in [('not JSON', True), ('[]', True),
                              ('{"orders": [], "extra": 1}', True), ('{"orders": []}', False)]:
            model = self.model()
            model.opener = Mock()
            model.opener.open.return_value = self.response(content, done)
            with self.subTest(content=content, done=done), self.assertRaises(ModelError):
                model.orders({})

    def test_network_errors_do_not_leak_response_or_url(self):
        for error in [URLError('PRIVATE'), TimeoutError('PRIVATE'),
                      HTTPError('http://PRIVATE', 500, 'PRIVATE', {}, None)]:
            model = self.model()
            model.opener = Mock()
            model.opener.open.side_effect = error
            with self.assertRaises(ModelError) as raised:
                model.orders({})
            self.assertNotIn('PRIVATE', str(raised.exception))

    def test_invalid_endpoint_or_timeout_rejected(self):
        for setting in [{'url': 'file:///tmp/model'}, {'url': 'http://user:pass@host'},
                        {'url': 'http://host/path'}, {'timeout_seconds': 0}]:
            with self.assertRaises(ValueError):
                Ollama({'model': 'test', **setting})

    def test_response_size_limit(self):
        model = self.model()
        model.opener = Mock()
        model.opener.open.return_value = io.BytesIO(b'x' * 1_048_577)
        with self.assertRaises(ModelError):
            model.orders({})


if __name__ == '__main__':
    unittest.main()
