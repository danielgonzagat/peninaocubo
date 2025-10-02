"""
DEPRECATED: penin/equations/linf_meta.py
======================================================================

This module has been CONSOLIDATED into penin/math/linf.py.

Maintained only for backward compatibility.
All new development should use:

    from penin.math.linf import ...

This file will be removed in version 2.0.0.

Migration:
----------
Update all imports from this module to use the canonical location above.
"""

# Import from canonical location for compatibility
try:
    from penin.math.linf import *
except ImportError:
    pass
