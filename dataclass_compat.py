import sys
from dataclasses import dataclass as _dataclass
from typing import TYPE_CHECKING

try:
    from typing import dataclass_transform
except ImportError:
    from typing_extensions import dataclass_transform  # type: ignore


if TYPE_CHECKING:
    # Let IDE/stubs see the real dataclass signature (with slots on 3.10+).
    dataclass_compat = _dataclass
else:
    @dataclass_transform()
    def dataclass_compat(*args, **kwargs):
        """dataclass with slots support only on Python >=3.10."""
        if sys.version_info < (3, 10):
            kwargs = dict(kwargs)
            kwargs.pop("slots", None)
        return _dataclass(*args, **kwargs)
