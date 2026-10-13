"""Compare real movement adjudicators in a disposable local CI database."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from diplomacy import Game
from diplomacy.utils.order_results import BOUNCE, DISLODGED, NO_CONVOY, VOID
from cpu_bot.board import Board
from scenarios import CASES


def prepare(orders):
    game = Game()
    game.clear_units()
    for power, rows in orders.items():
        game.set_units(power, [' '.join(row.split()[:2]) for row in rows])
    return game


def compare(webdip, php):
    variant = json.loads((ROOT / 'tests/cpu/fixtures/classic.json').read_text())
    mapper = Board({'game': {'turn': 0, 'phase': 'Diplomacy', 'variantID': 1}},
                   {'turn': 0, 'phase': 'Diplomacy', 'units': [], 'territories': []}, variant)
    countries = {name: cid for cid, name in mapper.countries.items()}
    borders = []
    for territory in variant['territories']:
        if territory['coast'] == 'Child':
            continue
        for edge in territory['borders']:
            borders.append([territory['id'], edge['id'], 'Yes' if edge['army'] else 'No',
                            'Yes' if edge['fleet'] else 'No'])
    inputs, expected = [], {}
    for name, orders in CASES:
        game = prepare(orders)
        rows, labels = [], {}
        for power, choices in orders.items():
            possible = game.get_all_possible_orders()
            for order in choices:
                unit = ' '.join(order.split()[:2])
                location = unit.split()[1]
                assert order in possible.get(location, possible.get(location[:3], [])), order
                row = mapper.translate(order, countries[power])
                # Match webDiplomacy's toMoves(): adjudicator input strips coast IDs.
                for field in ('terrID', 'toTerrID', 'fromTerrID'):
                    if row[field] is not None:
                        row[field] = mapper.ids[mapper.locations[row[field]][:3]]
                row['id'] = len(rows) + 1
                rows.append(row)
                labels[row['id']] = (unit, order)
            game.set_orders(power, choices)
        game.process()
        expected[name] = {}
        for row in rows:
            unit, order = labels[row['id']]
            status = game.get_order_status(unit=unit)
            expected[name][str(row['id'])] = {
                'move_success': row['type'] == 'Move' and not any(x in status for x in (BOUNCE, NO_CONVOY, VOID)),
                'dislodged': DISLODGED in status,
            }
        inputs.append({'name': name, 'orders': rows})
    result = subprocess.run([php, str(Path(__file__).with_name('php_adjudicate.php')), str(webdip)],
                            input=json.dumps({'borders': borders, 'cases': inputs}),
                            text=True, capture_output=True, timeout=120, check=True)
    actual = json.loads(result.stdout)
    failures = []
    for name, wanted in expected.items():
        if actual.get(name) != wanted:
            failures.append(name)
            print(f'FAIL {name}: Python={wanted!r}; PHP={actual.get(name)!r}')
        else:
            print(f'PASS {name}')
    print(f'{len(expected) - len(failures)}/{len(expected)} movement scenarios agree')
    return bool(failures)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--webdip', type=Path, required=True)
    parser.add_argument('--php', default='php')
    args = parser.parse_args()
    sys.exit(compare(args.webdip.resolve(), args.php))
