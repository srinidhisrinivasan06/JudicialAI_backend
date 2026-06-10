from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


BASE_UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"


def ensure_upload_directory(category: str) -> Path:
    directory = BASE_UPLOAD_DIR / category
    directory.mkdir(parents=True, exist_ok=True)
    return directory


async def save_upload_file(upload_file: UploadFile, category: str) -> str:
    directory = ensure_upload_directory(category)
    original_name = Path(upload_file.filename or "upload.bin").name
    safe_name = f"{uuid4().hex}_{original_name}"
    file_path = directory / safe_name

    content = await upload_file.read()
    file_path.write_bytes(content)
    await upload_file.close()
    return str(file_path)
