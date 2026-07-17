class UploadTooLargeError(Exception):
    def __init__(self, max_size_bytes: int) -> None:
        self.max_size_bytes = max_size_bytes
        max_size_mb = max_size_bytes // (1024 * 1024)
        super().__init__(f"File exceeds the maximum allowed size of {max_size_mb} MB")
