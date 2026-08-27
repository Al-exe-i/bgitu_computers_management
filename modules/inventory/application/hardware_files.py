from modules.inventory.ports import (
    DownloadableHardwareFile,
    HardwareFileStreamingServicePort,
    StreamableHardwareVideo,
)


class InventoryHardwareFileQueries:
    def __init__(self, service: HardwareFileStreamingServicePort) -> None:
        self.service = service

    async def get_download(self, *, file_id: int) -> DownloadableHardwareFile:
        return await self.service.get_download(file_id)

    async def prepare_video_stream(
        self,
        *,
        file_id: int,
        range_header: str | None,
    ) -> StreamableHardwareVideo:
        return await self.service.prepare_video_stream(
            file_id=file_id,
            range_header=range_header,
        )
