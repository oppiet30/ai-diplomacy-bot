"""Planning checks for our own orders, independent of adjudication rules."""
from .ollama import ModelError


def coordination_issues(orders):
    own = {' '.join(o.split()[:2]): o.split() for o in orders}
    by_province = {unit.split()[1][:3]: words for unit, words in own.items()}
    issues, destinations = [], {}
    for unit, words in own.items():
        action = words[2]
        if action == '-':
            destination = words[3][:3]
            if destination in destinations:
                issues.append(f'{unit}: competing own moves to {destination}')
            destinations[destination] = unit
            occupant = by_province.get(destination)
            if occupant and occupant[2] != '-':
                issues.append(f'{unit}: moving into an own unit that is not moving')
            # A direct head-to-head swap cannot work; convoy swaps can.
            if (occupant and occupant[2] == '-' and occupant[3][:3] == words[1][:3]
                    and 'VIA' not in words and 'VIA' not in occupant):
                issues.append(f'{unit}: direct swap with an own unit')
        elif action in ('S', 'C'):
            target = by_province.get(words[4][:3])
            if target and target[0] == words[3]:
                if len(words) == 5:
                    matches = target[2] != '-'
                else:
                    matches = target[2] == '-' and target[3][:3] == words[6][:3]
                    if action == 'C':
                        matches = matches and 'VIA' in target
                if not matches:
                    issues.append(f'{unit}: {action} does not match the own target order')
    return sorted(set(issues))


def validate_coordination(orders):
    if coordination_issues(orders):
        raise ModelError('Model orders contain conflicting own-unit plans')
    return orders
