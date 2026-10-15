# ai-diplomacy-bot

An experimental CPU-friendly Ollama player for a private webDiplomacy installation.
Python fetches a Classic no-press position, asks your local model for orders, validates
every order against the engine's legal choices, and optionally submits through the
existing webDiplomacy API. No hosted AI API or OpenAI billing is required.

## First version

- Ollama selects movement orders; the proven DumbBot handles retreats and builds.
- Malformed, incomplete, duplicate, foreign-unit or illegal model orders are rejected.
- Model timeouts/errors use DumbBot fallback by default; disable fallback to send nothing
  on a movement-model failure. This option does not disable baseline retreat/build handling.
- Dry-run is the default. Only explicit game IDs are processed; ready, finished,
  paused, processing and unsupported positions are skipped by the inherited adapter.
- Submission rechecks the phase, saves unready, verifies returned orders, then marks ready.
- Model plans also reject conflicting own moves, blocked friendly destinations, direct
  swaps, and supports/convoys that contradict the selected own-unit order. These are
  strategy checks; the engine's legal orders and adjudication rules are unchanged.
  Rejected plans use the existing validated DumbBot fallback (or fail closed when
  fallback is disabled). DumbBot's own strategy is unchanged.
- The CLI remembers confirmed movement submissions in a `.feedback.private.json` file
  beside the private config. The next movement season receives submitted orders,
  destination-occupancy observations and center changes. Dry-runs never update it.
  Delete that file to reset memory. Missing, corrupt or stale feedback is ignored.
- No trained research weights, datasets or player messages are bundled or sent to Ollama.

Legal orders are not necessarily good strategy. This has not been benchmarked against
DumbBot or tested on Dell/Ollama. Complete convoy-route validation and negotiation are not supported
as dedicated planning features. Use a separate test game, not Game 6's working scheduler.

## Install on Dell (outside Apache's document root)

```bash
git clone https://github.com/oppiet30/ai-diplomacy-bot.git
cd ai-diplomacy-bot
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Python 3.11, 3.12 and 3.14 are tested. If using 3.11 or 3.12, substitute that interpreter
in the virtual-environment command above. Do not install the original diplomacy-research training stack.

## Private configuration

Copy `config.example.json` to `~/.config/ai-diplomacy-bot.json`, restrict its permissions
to 600, and edit it locally. Keep credentials outside the repository and web root.
Use the exact model tag shown by `ollama list`; no model is downloaded automatically.
For remote Ollama, set `ollama.url` to the OptiPlex's reachable LAN address on port 11434.
Allow only trusted LAN clients to reach Ollama; do not expose its unauthenticated API
to the internet. HTTP on a trusted LAN is supported but does not encrypt API credentials
sent to webDiplomacy; use HTTPS when it is configured.

`game_ids: []` is intentionally inert. Create a separate Classic no-press test game,
join a bot account, and add that game's ID. Start with one account and review a dry-run:

```bash
.venv/bin/python -m ai_bot --config ~/.config/ai-diplomacy-bot.json
```

Only after reviewing the choices, opt in to submission:

```bash
.venv/bin/python -m ai_bot --config ~/.config/ai-diplomacy-bot.json --submit
```

The program runs once and exits. It may query Ollama during a dry-run but makes no
order writes. Use the existing DumbBot separately; do not run two schedulers for the
same account/game. Multiple sequential model calls may take more than five minutes
on a CPU, so benchmark before scheduling. The server's gamemaster still advances turns.

## Diagnosing rejected Ollama orders

The bot logs the specific `ModelError` category (such as missing orders,
illegal orders, coordination conflicts, or Ollama timeout) with the game power
and phase. It does **not** log raw model output, API keys, or configuration
secrets.

`fallback_to_dumbbot` defaults to `true`. When enabled, a rejected movement
plan uses the independently validated DumbBot orders. When set to `false`,
the bot logs the reason and submits **no** orders; this preserves the
intentional fail-closed setting. To enable fallback, edit the **private**
configuration file outside the repository:

```json
"fallback_to_dumbbot": true
```

Do not run a second scheduler for the same game. Test with a separate game
and a dry-run before enabling live submission. If a live game repeatedly
reports `Model failed validation; no orders submitted`, inspect its private
`fallback_to_dumbbot` setting and the new validation reason in the logs.

## Tests and GitHub runners

```bash
.venv/bin/python -m unittest discover -s tests/cpu -v
.venv/bin/python -m unittest discover -s tests/ai -v
```

GitHub-hosted runners test Python 3.11, 3.12 and 3.14 on pushes, PRs and manual dispatch.
All tests are isolated: mocked Ollama, engine fixtures, and a local HTTP test server.
They never access real accounts, Dell or the OptiPlex. No self-hosted runner is needed.

## Attribution

`cpu_bot/`, its baseline tests and Classic fixture are adapted from
`oppiet30/diplomacy-bot`'s `feature/cpu-webdip-bot` branch, including retreat and
empty-phase fixes. The DumbBot ruleset originated in Philip Paquette's MIT-licensed
diplomacy-research project; its original notices remain in the file and the original
project license is in `THIRD_PARTY/diplomacy-bot-LICENSE`. This repository does not
redistribute restricted trained model weights or datasets.

AI-assisted implementation: Codex. Review changes and run the tests before deployment.
