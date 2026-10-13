"""Bounded Ollama requests. Never send API credentials or raw player messages."""
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener
from cpu_bot.client import NoRedirect


class ModelError(ValueError):
    pass


class Ollama:
    def __init__(self, settings):
        self.url = settings.get('url', 'http://127.0.0.1:11434').rstrip('/')
        parsed = urlsplit(self.url)
        if (parsed.scheme not in ('http', 'https') or not parsed.hostname
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ('', '/')):
            raise ValueError('ollama.url must be an HTTP(S) server origin without credentials')
        self.model = settings.get('model')
        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError('ollama.model is required')
        self.timeout = settings.get('timeout_seconds', 120)
        if type(self.timeout) not in (int, float) or not 1 <= self.timeout <= 600:
            raise ValueError('timeout_seconds must be between 1 and 600')
        self.opener = build_opener(NoRedirect())

    def orders(self, position):
        schema = {'type': 'object', 'properties': {'orders': {
            'type': 'array', 'items': {'type': 'string'}}},
            'required': ['orders'], 'additionalProperties': False}
        payload = {
            'model': self.model, 'stream': False, 'format': schema,
            # Only final orders are consumed; keep thinking from using the output budget.
            'think': False,
            'options': {'temperature': 0, 'num_predict': 1024},
            'messages': [
                {'role': 'system', 'content': (
                    'You play Classic no-press Diplomacy. Choose a coherent set of orders '
                    'to capture and defend supply centers. Consider support moves and '
                    'enemy threats. Return JSON with only an orders array. '
                    'Use supply_centers and powers to identify neutral and enemy centers. '
                    'Adjacency describes map connections; legal_orders remains authoritative '
                    'for each unit and coast. Compare baseline_orders with alternatives: '
                    'the baseline is a legal candidate, not a required answer. Prefer '
                    'supported attacks, threatened-center defense, or movement toward '
                    'reachable centers over aimless moves or holding every unit. Holding '
                    'is appropriate when it protects a center or a move would expose one. '
                    'Assess likely enemy moves and coordinate your units. '
                    'Match supports to your own selected moves or stationary units. Avoid '
                    'competing moves into one province, direct swaps, and moving into an '
                    'own unit that stays. Coordinate convoy fleets with the army VIA order '
                    'and a complete sea route; do not assume foreign fleets will cooperate. '
                    'Use baseline_coordination_issues to improve the baseline plan. '
                    'Use previous_turn when present to reconsider unproductive plans; its '
                    'observations do not prove why a move failed or succeeded. '
                    'Choose exactly one order for each unit from its legal_orders list. Do not invent '
                    'units, orders or provinces. No negotiation or player messages.')},
                {'role': 'user', 'content': json.dumps(position)}]}
        request = Request(self.url + '/api/chat', data=json.dumps(payload).encode(),
                          headers={'Content-Type': 'application/json'})
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                body = response.read(1_048_577)
            if len(body) > 1_048_576:
                raise ModelError('Ollama response exceeds limit')
            envelope = json.loads(body)
            if not isinstance(envelope, dict) or envelope.get('done') is not True:
                raise ModelError('Ollama response is incomplete')
            answer = json.loads(envelope['message']['content'])
            if not isinstance(answer, dict) or set(answer) != {'orders'}:
                raise ModelError('Ollama response has an unexpected shape')
            return answer['orders']
        except HTTPError as error:
            raise ModelError(f'Ollama HTTP {error.code}') from None
        except (URLError, OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            if isinstance(error, ModelError):
                raise
            raise ModelError('Ollama request or JSON response failed') from None
