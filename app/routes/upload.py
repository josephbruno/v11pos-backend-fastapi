from fastapi import APIRouter, File, UploadFile, HTTPException, status

from app.services.storage_service import upload_file, delete_file, get_file_url


router = APIRouter(tags=["Upload"])


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    """Upload a file to MinIO and return its public URL."""
    try:
        object_name = await upload_file(file, folder="files")
        url = get_file_url(object_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    return {
        "success": True,
        "file_name": object_name,
        "url": url,
    }


@router.delete("/upload/{file_name}")
def remove(file_name: str):
    """Delete a file from MinIO by name."""
    try:
        delete_file(file_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    return {
        "success": True,
        "file_name": file_name,
    }
