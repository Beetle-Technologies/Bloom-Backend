from typing import Union
from uuid import UUID

from .guid import GUID

IDType = Union[GUID, UUID, int, str]
