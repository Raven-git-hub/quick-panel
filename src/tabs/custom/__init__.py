"""
Custom tab plugin router.
Loads the correct custom module based on custom_id in the tab config.
Each custom module must implement a build(tab: dict) -> Gtk.Widget function.
"""

import importlib
import pkgutil
from pathlib import Path
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def build(tab: dict) -> Gtk.Widget:
    custom_id = tab.get('custom_id', '')

    try:
        mod = importlib.import_module(f'tabs.custom.{custom_id}')
        return mod.build(tab)
    except ModuleNotFoundError:
        label = Gtk.Label(label=f"Custom plugin '{custom_id}' not found.")
        label.set_valign(Gtk.Align.CENTER)
        return label
    except Exception as e:
        label = Gtk.Label(label=f"Error loading plugin '{custom_id}':\n{e}")
        label.set_valign(Gtk.Align.CENTER)
        return label


def available_plugins() -> list:
    """
    Returns a list of available custom plugin ids.
    Scans src/tabs/custom/ for .py files, excludes __init__.py.
    Each entry is a dict with 'id' and 'label'.
    """
    plugins = []
    package_dir = Path(__file__).parent

    for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
        try:
            mod = importlib.import_module(f'tabs.custom.{module_name}')
            label = getattr(mod, 'PLUGIN_LABEL', module_name.replace('_', ' ').title())
            plugins.append({
                'id':    module_name,
                'label': label,
            })
        except Exception as e:
            print(f"Warning: could not load plugin '{module_name}': {e}")

    return sorted(plugins, key=lambda p: p['label'])
