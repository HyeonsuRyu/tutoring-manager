from abc import ABC, abstractmethod
from pathlib import Path


class ObjectStorage(ABC):
    """S3-shaped interface; local filesystem is the default implementation."""

    @abstractmethod
    def put(self, key: str, data: bytes, *, content_type: str | None = None) -> str:
        """Store object and return its key."""

    @abstractmethod
    def get(self, key: str) -> bytes:
        """Read object bytes by key."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete object by key."""


class LocalObjectStorage(ObjectStorage):
    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self._root / key).resolve()
        if not str(path).startswith(str(self._root.resolve())):
            raise ValueError("invalid storage key")
        return path

    def put(self, key: str, data: bytes, *, content_type: str | None = None) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()
