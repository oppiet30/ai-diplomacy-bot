# Diplomacy bot log cheat sheet

Use this guide to read England's Ollama orders and the other six bots' orders.

## Log files on Dell

| Bot | Log file |
| --- | --- |
| England (Ollama for movement; DumbBot for retreats and adjustments) | `~/ai-diplomacy-bot.log` |
| Other six countries (DumbBot) | `~/diplomacy-bot-cron.log` |

Show recent entries:

```bash
tail -n 40 ~/ai-diplomacy-bot.log
tail -n 40 ~/diplomacy-bot-cron.log
```

Watch England's log:

```bash
tail -f ~/ai-diplomacy-bot.log
```

Press Ctrl+C to stop watching. The bot service keeps running.

## Seasons and phase labels

The four seasons are spring, summer, autumn (fall), and winter.
Standard Diplomacy uses spring and autumn movement turns, with winter
adjustments. There is no separate summer turn.

| Label | Meaning |
| --- | --- |
| `S2171M` | Spring 2171 movement |
| `S2171R` | Spring 2171 retreats |
| `F2171M` | Autumn (fall) 2171 movement |
| `F2171R` | Autumn (fall) 2171 retreats |
| `W2171A` | Winter 2171 adjustments: builds or disbands |

The first letter is the season, the number is the game year, and the
last letter is the phase type. Retreats occur when units are dislodged
and need orders. Winter builds/disbands depend on the difference between
units and supply centers; builds also require an eligible vacant home center.

England's current AI bot delegates retreats and adjustments to DumbBot.
Those entries say `DumbBot handles retreat/build phase` rather than
`validated Ollama orders`.

## Order symbols

Most orders begin with a unit type and its current location.

| Symbol | Meaning | Example |
| --- | --- | --- |
| `A` | Army | `A MUN`: army in Munich |
| `F` | Fleet | `F DEN`: fleet in Denmark |
| `H` | Hold | `F DEN H` |
| `-` | Move to | `F DEN - KIE` |
| `S` | Support | `F HEL S F DEN - KIE` |
| `C` | Convoy an army | `F ENG C A LON - BEL` |
| `R` | Retreat to | `F NTH R DEN` |
| `D` | Disband | `A LVP D` |
| `B` | Build | `F LON B` |
| `VIA` | Army move by convoy | `A LON - BEL VIA` |
| `/NC`, `/SC`, `/EC` | North, south, or east coast | `F BUL/SC` |

A convoy requires a suitable chain of fleets with matching convoy orders.
Coast suffixes distinguish fleet positions in provinces with separate coasts.

## Examples from England's log

| Order | Decoded |
| --- | --- |
| `F DEN - KIE` | Fleet in Denmark attempts to move to Kiel. |
| `F HEL S F DEN - KIE` | Fleet in Heligoland Bight supports the fleet moving from Denmark to Kiel. |
| `F HEL - HOL` | Fleet in Heligoland Bight attempts to move to Holland. |
| `F HEL S A BEL - HOL` | Fleet in Heligoland Bight supports an army moving from Belgium to Holland. |
| `F DEN S A MUN - KIE` | Fleet in Denmark supports an army moving from Munich to Kiel. |
| `F DEN S A KIE` | Fleet in Denmark supports the army in Kiel holding. |
| `F HEL - KIE` and `F DEN - KIE` | Both fleets attempt to enter Kiel. If both attacks have equal strength, they bounce. |

Support can target another country's unit. It helps only if the supported
unit's actual order matches the support and the support survives adjudication.
Legal orders can still be strategically poor or fail.

## Common territory abbreviations

| Code | Territory |
| --- | --- |
| `BEL` | Belgium |
| `BER` | Berlin |
| `DEN` | Denmark |
| `EDI` | Edinburgh |
| `ENG` | English Channel |
| `HEL` | Heligoland Bight |
| `HOL` | Holland |
| `KIE` | Kiel |
| `LON` | London |
| `LVP` | Liverpool |
| `MUN` | Munich |
| `NTH` | North Sea |
| `NWG` | Norwegian Sea |
| `NWY` | Norway |
| `SKA` | Skagerrak |
| `SWE` | Sweden |
| `WAL` | Wales |
| `BUL` | Bulgaria |

## Status messages

| Message | Meaning |
| --- | --- |
| `ENGLAND S2171M: validated Ollama orders` | Ollama returned a complete set of orders that passed the bot's legal-choice checks for England in that phase. |
| `bot1 game 6: submitted [...]` | The bot sent those orders to game 6. This is not a report that the moves succeeded. |
| `bot1 game 6: dry run {...}` | Proposed submission only; no orders were sent. |
| `bot1 game 6: skipped` | No submission occurred in that invocation. The line alone does not identify why. |
| `ENGLAND: DumbBot handles retreat/build phase` | The phase uses DumbBot instead of Ollama. |
| `model unavailable/invalid; using DumbBot` | With fallback enabled, the model failed and the bot used its validated DumbBot movement plan. |
| `all units holding; review strategic progress` | Every chosen movement order is a hold; review whether that is useful defense or a stalled plan. |

In a dry-run payload, `"ready": "Yes"` describes the proposed submission.
It does not mean the dry run marked the country ready.

**Submitted orders are attempts, not results.** Use the next map or the game's
resolved-order history to see which moves succeeded, bounced, or were disrupted.
