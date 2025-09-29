from io import BytesIO
from tempfile import SpooledTemporaryFile
from typing import BinaryIO, Union

FileContent = Union[BinaryIO, BytesIO, SpooledTemporaryFile[bytes], bytes]
