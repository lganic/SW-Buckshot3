import os
import sys

# Allow both `python -m Buckshot3` and `python Buckshot3` / `python Buckshot3/__main__.py`.
if __package__ in (None, ''):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from Buckshot3.app import main
else:
    from .app import main

sys.exit(main())
