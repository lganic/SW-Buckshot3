import os
import sys

# Supports `python -m Buckshot3` (run from the folder that contains the package) and
# `python <repo folder>` / `python <repo folder>/__main__.py`. The repo is cloned as
# `SW-Buckshot3`, which isn't an importable name, so when run as a script the folder is
# loaded as the `Buckshot3` package whatever it's called on disk.
if __package__ in (None, ''):
    import importlib.util
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(
        'Buckshot3', os.path.join(pkg_dir, '__init__.py'),
        submodule_search_locations=[pkg_dir])
    pkg = importlib.util.module_from_spec(spec)
    sys.modules['Buckshot3'] = pkg
    spec.loader.exec_module(pkg)
    from Buckshot3.app import main
else:
    from .app import main

sys.exit(main())
