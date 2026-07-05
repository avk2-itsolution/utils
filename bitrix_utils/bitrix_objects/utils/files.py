from io import BytesIO
import base64
import mimetypes
from typing import Text, Tuple, List, Dict
from urllib.parse import unquote, urlparse
import requests


class FileObject(BytesIO):
    def __init__(self, content: bytes, filename: Text, extension: Text):
        super().__init__(content)
        self.filename = filename
        self.extension = extension

    @property
    def full_filename(self) -> Text:
        return f"{self.filename}.{self.extension}"

    @property
    def to_base64(self) -> Text:
        base64_bytes = base64.b64encode(self.getvalue())
        return base64_bytes.decode("utf-8")

    @property
    def to_list(self) -> List[Text]:
        return [self.full_filename, self.to_base64]

    @classmethod
    def from_base64(cls, base64_str: Text, filename: Text, extension: Text) -> "FileObject":
        content = base64.b64decode(base64_str)
        return cls(content, filename, extension)

    @classmethod
    def from_list(cls, file_list: List[Text]) -> "FileObject":
        """Получить объект на основе списка вида [название_файла.расширение, контент_в_base64]"""
        full_filename, base64_str = file_list
        filename, extension = full_filename.rsplit(".", maxsplit=1)
        return cls.from_base64(base64_str, filename, extension)

    @classmethod
    def from_url(cls, url: Text) -> "FileObject":
        """Получить объект по урлу"""
        response = requests.get(url)
        content_disposition = response.headers.get("Content-Disposition")
        filename, extension = cls.get_full_filename_from_content_disposition(content_disposition) \
            if content_disposition else cls.get_full_filename_from_url(response.url)

        if not extension:
            extension = mimetypes.guess_extension(response.headers.get("Content-Type", "").split(";", 1)[0]) or ".bin"
            extension = extension.lstrip(".")

        return cls(response.content, filename, extension)

    @staticmethod
    def get_full_filename_from_content_disposition(content_disposition: Text) -> Tuple[Text, Text]:
        """Получить кортеж вида (название_файла, расширение из заголовка Content-Disposition)"""
        for string in (part.strip() for part in content_disposition.split(";")):
            if string.startswith("filename*="):
                full_filename = unquote(string.split("''", maxsplit=1)[-1]).replace("\"", "")
                return FileObject.split_full_filename(full_filename)
            if string.startswith("filename="):
                full_filename = string.replace("filename=", "").replace("\"", "")
                return FileObject.split_full_filename(full_filename)

        return FileObject.get_full_filename_from_url("")

    @staticmethod
    def get_full_filename_from_url(url: Text) -> Tuple[Text, Text]:
        """Получить имя файла из пути URL, если сервер не отдал Content-Disposition."""
        full_filename = unquote(urlparse(url).path.rsplit("/", maxsplit=1)[-1])
        return FileObject.split_full_filename(full_filename)

    @staticmethod
    def split_full_filename(full_filename: Text) -> Tuple[Text, Text]:
        if "." in full_filename:
            filename, extension = full_filename.rsplit(".", maxsplit=1)
            return filename or "file", extension

        return full_filename or "file", ""

    def to_dict(self) -> Dict:
        return {"filename": self.filename, "extension": self.extension}
