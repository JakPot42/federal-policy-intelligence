"""Entry point for running the unified CLI without installing:

    py main.py comments demo
    py main.py policy analyze --file draft.txt
    py main.py velocity series BIS

Once installed (`pip install -e .`), the same commands are available as
`fpi comments demo`, etc.
"""
from fpi.cli import cli

if __name__ == "__main__":
    cli()
