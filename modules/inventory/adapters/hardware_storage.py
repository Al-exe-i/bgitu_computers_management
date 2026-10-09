from modules.inventory.constants import MAX_HARDWARE_FILE_SIZE_BYTES
from modules.inventory.ports import UploadedHardwareFile
from services.object_storage import ObjectStorage


class HardwareFileStorage:
    def __init__(self, storage: ObjectStorage, *, prefix: str = "uploads") -> None:
        self.storage = storage
        self.prefix = prefix

    async def save(self, file: UploadedHardwareFile, *, extension: str) -> str:
        return await self.storage.save_upload(
            file,
            prefix=self.prefix,
            extension=extension,
            max_size_bytes=MAX_HARDWARE_FILE_SIZE_BYTES,
        )

    def delete(self, file_path: str) -> bool:
        return self.storage.delete(file_path)
