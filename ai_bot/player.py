"""Model choices must pass independent legality and completeness checks."""
from cpu_bot.strategy import choose_orders
from .ollama import ModelError
from .coordination import coordination_issues, validate_coordination


def legal_choices(game, power):
    possible = game.get_all_possible_orders()
    choices = {}
    for unit in game.get_units(power):
        location = unit.split()[1]
        rows = possible.get(location, possible.get(location[:3], []))
        choices[unit] = sorted(set(order for order in rows if order.startswith(unit + ' ')))
    return choices


def validate_orders(orders, choices):
    if not isinstance(orders, list) or len(orders) != len(choices):
        raise ModelError('Model must supply exactly one order per unit')
    used = set()
    for order in orders:
        if not isinstance(order, str) or len(order) > 160:
            raise ModelError('Invalid order value')
        units = [unit for unit, legal in choices.items() if order in legal]
        if len(units) != 1 or units[0] in used:
            raise ModelError('Illegal, foreign or duplicate unit order')
        used.add(units[0])
    return orders


class Player:
    def __init__(self, model, fallback=True, log=print, feedback=None):
        self.model, self.fallback, self.log = model, fallback, log
        self.feedback, self.feedback_key = feedback, None

    def begin_turn(self, server, game_id, game, power):
        self.feedback_key = self.feedback.key(server, game_id, power) if self.feedback else None

    def submitted(self, game, power, orders):
        if self.feedback and self.feedback_key and game.phase_type == 'M':
            try:
                self.feedback.save(self.feedback_key, game, power, orders)
            except OSError:
                self.log(f'{power}: orders submitted, but previous-turn feedback could not be saved')

    def __call__(self, game, power):
        # Use the tested phase adapter for retreats/builds in this first version.
        if game.phase_type != 'M':
            self.log(f'{power}: DumbBot handles retreat/build phase')
            return choose_orders(game, power)
        choices = legal_choices(game, power)
        if not choices:
            return []
        baseline = validate_orders(choose_orders(game, power), choices)
        position = {
            'power': power, 'phase': game.get_current_phase(),
            'powers': {name: {'units': game.get_units(name),
                              'centers': list(state.centers)}
                       for name, state in game.powers.items()},
            'supply_centers': sorted(game.map.scs),
            'adjacency': {location: sorted(neighbors)
                          for location, neighbors in game.map.loc_abut.items()},
            'baseline_orders': baseline,
            'baseline_coordination_issues': coordination_issues(baseline),
            'previous_turn': (self.feedback.previous(self.feedback_key, game, power)
                              if self.feedback and self.feedback_key else None),
            'legal_orders': choices}
        try:
            result = validate_coordination(validate_orders(self.model.orders(position), choices))
            self.log(f'{power} {position["phase"]}: validated Ollama orders')
            if all(order.endswith(' H') for order in result):
                self.log(f'{power}: all units holding; review strategic progress')
            return result
        except ModelError as error:
            if not self.fallback:
                self.log(f'{power} {position["phase"]}: model rejected ({error}); fallback disabled; no orders submitted')
                raise ModelError('Model failed validation; no orders submitted') from None
            self.log(f'{power} {position["phase"]}: model rejected ({error}); using validated DumbBot fallback')
            return baseline
