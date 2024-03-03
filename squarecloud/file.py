from __future__ import annotations

import io
import os

__all__ = ("File",)


class File:
    """Object that represents a file that will be sent in unpload or commit.

    Attributes:
        filename: The file name.
        file: File object.
    """

    __slots__ = ("filename", "fp")

    def __init__(
        self,
        fp: str | bytes | io.IOBase,
        filename: str | None = None,
    ):
        if isinstance(fp, bytes):
            self.fp = io.BytesIO(fp)
        elif isinstance(fp, io.IOBase):
            if not fp.readable():
                raise ValueError("The file must be readable.")
            self.fp = fp
        else:
            self.fp = open(fp, "rb")

        if filename is None:
            if isinstance(fp, str):
                filename = os.path.split(fp)[1]
            else:
                filename = getattr(fp, "name", "unknow")

        self.filename = filename
