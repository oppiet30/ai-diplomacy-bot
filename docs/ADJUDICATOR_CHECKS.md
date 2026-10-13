# Checking the bot and adjudicators

The bot uses the Python `diplomacy==1.1.2` engine to enumerate legal orders.
webDiplomacy's PHP adjudicator resolves actual game phases automatically.
These checks keep both engines and the game rules unchanged. Run them on test
positions, never by manually processing a live game.

## Local Python checks

From the AI bot repository with its virtual environment:

```bash
.venv/bin/python -m unittest discover -s tests/ai -v
.venv/bin/python -m unittest discover -s tests/cpu -v
.venv/bin/python -m unittest discover -s tests/rules -v
```

The rules suite runs all 160 standard DATC cases bundled with the pinned Python
dependency. They cover movement, support, convoys, retreats and adjustments.
It also exercises shared comparison positions and reproduces the legal
self-bounce and competing foreign supports seen in England's log. These tests
document the planning limitation; they do not forbid legal tactical self-bounces
or change model decisions.

## PHP/Python comparison in CI

The **Adjudicator compatibility** GitHub Actions job starts a disposable MariaDB
service and loads the real PHP movement adjudicator from this webDiplomacy revision:

```text
oppiet30/webDiplomacy bcb0c5edec9b5667d8317fff9c41d1f9e44d1920
```

Thirteen identical movement scenarios run through both engines. The comparison
checks each moving unit's success and each unit's dislodgement, including Kiel
bounces, matching/mismatched support, support cutting and its exception, head-to-head
moves, rotation, self-dislodgement, successful/disrupted convoys, and a separate-coast
fleet move. Inputs are individually legal under the Python engine. PHP receives
the parent province IDs used by webDiplomacy's `toMoves()` adapter.

The harness calls the original `adjudicatorDiplomacy::adjudicate()` and original
move/dependency classes, using the original Moves and Borders table definitions.
The database adapter and minimal Classic variant factory are test plumbing.
No game, accounts, API keys or live server are involved.

The PHP runner only connects to loopback port 3307 and the dedicated
`adjudicator_compat_test` database. It refuses pre-existing Moves/Borders tables,
creates its own tables, and removes only those tables on completion.
The credentials in CI are disposable test credentials.

This is a targeted movement comparison, **not full certification** of the PHP
engine. It does not exercise PHP order-entry validation, game processing, supply
center updates, retreats or winter adjustments. The separate-coast case compares
province-level movement after translation; PHP coastal order-entry validation
is outside this harness. Additional DATC positions and PHP phase adapters can
extend coverage. Re-run against the deployed server revision when it changes.

## Reading failures

- Python DATC failure: investigate the pinned dependency and the expected rule.
- PHP/Python disagreement: inspect the exact case, source revisions and adapter
  before changing any code. A disagreement alone does not identify the wrong engine.
- Passing adjudication with stalled units: examine planning and coordination.
  Legal submissions can still bounce or contain ineffective support.

The bot currently rechecks phase/turn/readiness before writes, verifies saved
orders before marking ready, and delegates retreats/adjustments to DumbBot.
Coordination checks and previous-turn feedback are separate planning work.
