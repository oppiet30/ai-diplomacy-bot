# Reused code

Source: https://github.com/oppiet30/diplomacy-bot

Branch: feature/cpu-webdip-bot, through commit e67876f (retreat and empty-phase fixes).

The CPU API/board adapter, strategy loader, baseline tests and Classic fixture are
reused under that project's MIT license. The adapter gains an injectable order
selector; no original training stack is copied. See diplomacy-bot-LICENSE.

diplomacy_research/players/rulesets/dumbbot_ruleset.py retains Philip Paquette's
original 2019 copyright and MIT notice. No pretrained weights or datasets are included.
