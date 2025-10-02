"""
DEPRECATED: penin/equations/caos_plus.py
======================================================================

This module has been CONSOLIDATED into penin/core/caos.py.

Maintained only for backward compatibility.
All new development should use:

    from penin.core.caos import ...

This file will be removed in version 2.0.0.

Migration:
----------
Update all imports from this module to use the canonical location above.
"""

# Import from canonical location for compatibility
try:
    from penin.core.caos import *
except ImportError:
    pass
