import importlib
import logging
from functools import lru_cache
from typing import List, Dict
from django.apps import apps
from django.conf import settings

logger = logging.getLogger(__name__)


def _discover_features() -> List[Dict]:
    features: List[Dict] = []
    for app_config in apps.get_app_configs():
        module_name = f"{app_config.name}.portal_features"
        try:
            mod = importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue
        except Exception as e:
            logger.warning("Error importing %s: %s", module_name, e)
            continue
        get_fn = getattr(mod, "get_portal_features", None)
        if callable(get_fn):
            try:
                items = get_fn() or []
                for item in items:
                    item.setdefault("order", 1000)
                    item.setdefault("required_perms", [])
                    item.setdefault("icon", "")
                    item.setdefault("key", item.get("urlname", ""))
                    features.append(item)
            except Exception as e:
                logger.warning("Error reading features from %s: %s", module_name, e)

    flags = getattr(settings, "PORTAL_FEATURE_FLAGS", {})
    out = []
    for f in features:
        key = f.get("key")
        if key in flags and flags[key] is False:
            continue
        out.append(f)

    out.sort(key=lambda x: (x.get("order", 1000), x.get("label", "")))
    return out


@lru_cache(maxsize=1)
def get_all_features() -> List[Dict]:
    return _discover_features()
