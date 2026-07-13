from tutoring_manager_api.config import Settings
from tutoring_manager_api.storage.base import LocalObjectStorage, ObjectStorage


def get_object_storage(settings: Settings) -> ObjectStorage:
    if settings.storage_backend == "local":
        return LocalObjectStorage(settings.local_storage_path)
    raise NotImplementedError(f"storage backend {settings.storage_backend!r} is not implemented yet")
