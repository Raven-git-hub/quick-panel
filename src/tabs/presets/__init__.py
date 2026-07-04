"""
Preset registry — automatically loads all presets from this directory.
Drop a new .py file in here with a PRESET dict to add a new preset.
"""

import importlib
import pkgutil
from pathlib import Path


def load_all() -> list:
    """Return a list of all preset dicts, sorted by label."""
    presets = []
    package_dir = Path(__file__).parent

    for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
        try:
            mod = importlib.import_module(f'tabs.presets.{module_name}')
            if hasattr(mod, 'PRESET'):
                presets.append(mod.PRESET)
        except Exception as e:
            print(f"Warning: failed to load preset '{module_name}': {e}")

    return sorted(presets, key=lambda p: p.get('label', ''))
