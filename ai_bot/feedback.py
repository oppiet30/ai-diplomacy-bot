"""Remember confirmed submissions; report observations, never inferred adjudication."""
import hashlib
import json
import os
import tempfile
from pathlib import Path


class Feedback:
    def __init__(self, path):
        self.path = Path(path)

    def key(self, server, game_id, power):
        return hashlib.sha256(f'{server}:{game_id}:{power}'.encode()).hexdigest()

    def read(self):
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def previous(self, key, game, power):
        row = self.read().get(key)
        phase = game.get_current_phase()
        if not isinstance(row, dict):
            return None
        # Only compare the immediately preceding movement season. Missing or stale
        # records do not become a purported result for some later turn.
        previous = ('S' + phase[1:5] + 'M' if phase[0] == 'F'
                    else 'F' + str(int(phase[1:5]) - 1) + 'M')
        if row.get('phase') != previous:
            return None
        if (not isinstance(row.get('orders'), list)
                or not all(isinstance(o, str) for o in row['orders'])
                or not isinstance(row.get('centers'), list)
                or not all(isinstance(c, str) for c in row['centers'])):
            return None
        current = set(game.get_units(power))
        moves = []
        for order in row['orders']:
            words = order.split()
            if len(words) >= 4 and words[2] == '-':
                destination = words[3]
                moves.append({'order': order, 'own_unit_at_destination': any(
                    u.split()[0] == words[0] and u.split()[1][:3] == destination[:3]
                    for u in current)})
        centers = set(game.powers[power].centers)
        return {'phase': previous, 'submitted_orders': row['orders'],
                'move_observations': moves,
                'centers_gained': sorted(centers - set(row['centers'])),
                'centers_lost': sorted(set(row['centers']) - centers),
                'limits': 'Board observations only; not adjudicator results. Retreats and '
                          'builds may intervene. Spring moves do not transfer center ownership.'}

    def save(self, key, game, power, orders):
        data = self.read()
        data[key] = {'phase': game.get_current_phase(), 'orders': orders,
                     'centers': sorted(game.powers[power].centers)}
        # Atomic replacement avoids partially written feedback after interruption.
        fd, temporary = tempfile.mkstemp(dir=self.path.parent, suffix='.private.json')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as output:
                json.dump(data, output)
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
