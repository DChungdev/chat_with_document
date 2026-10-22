from typing import BinaryIO


class InMemoryFileStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.fail_delete = False  # để test đường lỗi xóa

    async def put(self, key: str, content: BinaryIO, content_type: str) -> None:
        self.objects[key] = content.read()

    async def get(self, key: str) -> bytes:
        return self.objects[key]

    async def delete(self, key: str) -> None:
        if self.fail_delete:
            raise ConnectionError("storage down")
        self.objects.pop(key, None)

    async def exists(self, key: str) -> bool:
        return key in self.objects
