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

## All 75 standard-map territories

The standard map has **56 land provinces and 19 sea spaces**. Coastal provinces
are land provinces that fleets can also occupy. This list is a code reference;
it does not mean a unit can move directly to every territory.

Armies move between adjacent land provinces or reach coastal provinces by convoy.
Fleets move between connected sea spaces and coastal provinces along fleet-valid
connections. Inland provinces are available only to armies.

| Code | Territory | Type |
| --- | --- | --- |
| `ADR` | Adriatic Sea | Sea |
| `AEG` | Aegean Sea | Sea |
| `ALB` | Albania | Coastal |
| `ANK` | Ankara | Coastal |
| `APU` | Apulia | Coastal |
| `ARM` | Armenia | Coastal |
| `BAL` | Baltic Sea | Sea |
| `BAR` | Barents Sea | Sea |
| `BEL` | Belgium | Coastal |
| `BER` | Berlin | Coastal |
| `BLA` | Black Sea | Sea |
| `BOH` | Bohemia | Inland |
| `BOT` | Gulf of Bothnia | Sea |
| `BRE` | Brest | Coastal |
| `BUD` | Budapest | Inland |
| `BUL` | Bulgaria | Coastal |
| `BUR` | Burgundy | Inland |
| `CLY` | Clyde | Coastal |
| `CON` | Constantinople | Coastal |
| `DEN` | Denmark | Coastal |
| `EAS` | Eastern Mediterranean | Sea |
| `EDI` | Edinburgh | Coastal |
| `ENG` | English Channel | Sea |
| `FIN` | Finland | Coastal |
| `GAL` | Galicia | Inland |
| `GAS` | Gascony | Coastal |
| `GRE` | Greece | Coastal |
| `HEL` | Helgoland Bight | Sea |
| `HOL` | Holland | Coastal |
| `ION` | Ionian Sea | Sea |
| `IRI` | Irish Sea | Sea |
| `KIE` | Kiel | Coastal |
| `LON` | London | Coastal |
| `LVN` | Livonia | Coastal |
| `LVP` | Liverpool | Coastal |
| `LYO` | Gulf of Lyon | Sea |
| `MAO` | Mid-Atlantic Ocean | Sea |
| `MAR` | Marseilles | Coastal |
| `MOS` | Moscow | Inland |
| `MUN` | Munich | Inland |
| `NAF` | North Africa | Coastal |
| `NAO` | North Atlantic Ocean | Sea |
| `NAP` | Naples | Coastal |
| `NTH` | North Sea | Sea |
| `NWG` | Norwegian Sea | Sea |
| `NWY` | Norway | Coastal |
| `PAR` | Paris | Inland |
| `PIC` | Picardy | Coastal |
| `PIE` | Piedmont | Coastal |
| `POR` | Portugal | Coastal |
| `PRU` | Prussia | Coastal |
| `ROM` | Rome | Coastal |
| `RUH` | Ruhr | Inland |
| `RUM` | Rumania | Coastal |
| `SER` | Serbia | Inland |
| `SEV` | Sevastopol | Coastal |
| `SIL` | Silesia | Inland |
| `SKA` | Skagerrak | Sea |
| `SMY` | Smyrna | Coastal |
| `SPA` | Spain | Coastal |
| `STP` | St Petersburg | Coastal |
| `SWE` | Sweden | Coastal |
| `SYR` | Syria | Coastal |
| `TRI` | Trieste | Coastal |
| `TUN` | Tunis | Coastal |
| `TUS` | Tuscany | Coastal |
| `TYR` | Tyrolia | Inland |
| `TYS` | Tyrrhenian Sea | Sea |
| `UKR` | Ukraine | Inland |
| `VEN` | Venice | Coastal |
| `VIE` | Vienna | Inland |
| `WAL` | Wales | Coastal |
| `WAR` | Warsaw | Inland |
| `WES` | Western Mediterranean | Sea |
| `YOR` | Yorkshire | Coastal |

### Provinces with separate coasts

Coast suffixes identify a fleet's coast; they do not add extra provinces to the
75-territory total. Armies use the province code without a coast suffix.

| Province | Fleet coast codes |
| --- | --- |
| Bulgaria | `BUL/EC` (east), `BUL/SC` (south) |
| Spain | `SPA/NC` (north), `SPA/SC` (south) |
| St Petersburg | `STP/NC` (north), `STP/SC` (south) |

Switzerland (`SWI`) is impassable and is not included in the 75 playable
territories. Rumania is also commonly spelled Romania; Helgoland Bight is also
called Heligoland Bight.

Codes and terrain types follow the [Diplomacy engine's standard map](https://github.com/diplomacy/diplomacy/blob/master/diplomacy/maps/standard.map).

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
