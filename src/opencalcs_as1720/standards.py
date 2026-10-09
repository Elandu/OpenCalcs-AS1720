"""Compatibility import for ``opencalcs_as1720.standards``."""

import sys as _sys
from importlib import import_module as _import_module

_sys.modules[__name__] = _import_module("engcalcs_as1720.standards")
