import argparse
import json
import sys
from pathlib import Path
from cpu_bot.client import run, validate_config
from .ollama import Ollama
from .player import Player
from .feedback import Feedback


def main():
    parser = argparse.ArgumentParser(description='Ollama player for selected Classic no-press games')
    parser.add_argument('--config', required=True, help='Private configuration path')
    parser.add_argument('--submit', action='store_true', help='Submit orders; default is dry-run')
    args = parser.parse_args()
    try:
        with open(args.config, encoding='utf-8') as source:
            config = json.load(source)
        validate_config(config)
        fallback = config.get('fallback_to_dumbbot', True)
        if type(fallback) is not bool:
            raise ValueError('fallback_to_dumbbot must be boolean')
        # Keep feedback next to private configuration, outside the repository.
        feedback = Feedback(Path(args.config).resolve().with_suffix('.feedback.private.json'))
        player = Player(Ollama(config.get('ollama', {})), fallback=fallback, feedback=feedback)
        return run(config, args.submit, order_selector=player)
    except (OSError, ValueError, TypeError, AttributeError):
        # Config parser exceptions can contain configuration fragments; do not log them.
        print('Startup failed: check private config, API settings and Ollama settings.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
