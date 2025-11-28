"""
File Manager API Routes
Handles file operations: upload, view, delete, create folders, list contents, navigate
"""
import os
import asyncio
import mimetypes
from pathlib import Path
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import FileResponse, JSONResponse
import aiofiles
import aiofiles.os

from app.schemas.file_manager import (
    FileInfo,
    FolderContents,
    UploadResponse,
    DeleteResponse,
    CreateFolderResponse,
    FileViewResponse,
    ErrorResponse,
)
from app.routes.auth import get_current_user
from app.models.user import User
from app.response_formatter import success_response, created_response, list_response, deleted_response, error_response

router = APIRouter(prefix="/api/v1/filemanager", tags=["File Manager"])

# Configuration
ROOT_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
BLOCKED_PATHS = {"..", "etc", "root", "sys", "home", "var"}


def validate_path(requested_path: str) -> Path:
    """
    Validate and sanitize the requested path to prevent directory traversal attacks.
    
    Args:
        requested_path: The path requested by the user
        
    Returns:
        Path: Validated absolute path
        
    Raises:
        HTTPException: If path is invalid or attempts directory traversal
    """
    # Remove leading/trailing slashes and normalize
    requested_path = requested_path.strip("/").strip("\\")
    
    # Check for directory traversal attempts
    if ".." in requested_path or requested_path.startswith("/"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Directory traversal not allowed"
        )
    
    # Check for blocked paths
    for blocked in BLOCKED_PATHS:
        if requested_path.lower().startswith(blocked):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access to '{blocked}' is not allowed"
            )
    
    # Resolve full path
    full_path = (ROOT_DIR / requested_path).resolve()
    
    # Ensure the path is within the root directory
    if not str(full_path).startswith(str(ROOT_DIR.resolve())):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: path outside root directory"
        )
    
    return full_path


def validate_filename(filename: str) -> bool:
    """
    Validate filename safety.
    
    Args:
        filename: The filename to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Check for invalid characters
    invalid_chars = {"<", ">", ":", '"', "/", "\\", "|", "?", "*"}
    if any(char in filename for char in invalid_chars):
        return False
    
    # Check for hidden files (starting with dot)
    if filename.startswith("."):
        return False
    
    return True


async def get_file_info(file_path: Path) -> FileInfo:
    """
    Get file information asynchronously.
    
    Args:
        file_path: Path to the file
        
    Returns:
        FileInfo: File information object
    """
    stat = await aiofiles.os.stat(str(file_path))
    name = file_path.name
    mime_type, _ = mimetypes.guess_type(str(file_path))
    
    return FileInfo(
        name=name,
        path=str(file_path.relative_to(ROOT_DIR)),
        size=stat.st_size,
        type="file" if file_path.is_file() else "folder",
        mime_type=mime_type,
        created_at=datetime.fromtimestamp(stat.st_ctime),
        modified_at=datetime.fromtimestamp(stat.st_mtime),
        is_image=file_path.suffix.lower() in ALLOWED_EXTENSIONS,
    )


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image file",
    description="Upload an image file (jpg, jpeg, png, gif, webp) to the uploads directory"
)
async def upload_file(
    file: UploadFile = File(...),
    folder: str = "",
    current_user: User = Depends(get_current_user),
):
    """
    Upload an image file to a specified folder.
    
    Only image files (jpg, jpeg, png, gif, webp) are allowed.
    Maximum file size: 10MB
    
    Args:
        file: The image file to upload
        folder: Optional folder path within uploads/
        current_user: Current authenticated user
        
    Returns:
        UploadResponse: Upload status and file information
    """
    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{file_ext}' not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Validate filename
        if not validate_filename(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename characters"
            )
        
        # Validate folder path
        if folder:
            folder_path = validate_path(folder)
        else:
            folder_path = ROOT_DIR
        
        # Create directory if it doesn't exist
        folder_path.mkdir(parents=True, exist_ok=True)
        
        # Read and validate file size
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Generate unique filename if it already exists
        file_path = folder_path / file.filename
        counter = 1
        while file_path.exists():
            name = Path(file.filename).stem
            ext = Path(file.filename).suffix
            file_path = folder_path / f"{name}_{counter}{ext}"
            counter += 1
        
        # Write file asynchronously
        async with aiofiles.open(str(file_path), "wb") as f:
            await f.write(contents)
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        return UploadResponse(
            success=True,
            message="File uploaded successfully",
            file_name=file_path.name,
            file_path=str(file_path.relative_to(ROOT_DIR)),
            file_size=len(contents),
            mime_type=mime_type or "application/octet-stream",
            url=f"/api/v1/filemanager/view/{file_path.relative_to(ROOT_DIR)}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get(
    "/view/{file_path:path}",
    summary="View/Download image file",
    description="Get image file by path or filename"
)
async def view_file(
    file_path: str,
    current_user: User = Depends(get_current_user),
):
    """
    View or download an image file by its path.
    
    Returns the file with appropriate content-type headers.
    
    Args:
        file_path: Path to the file within uploads/
        current_user: Current authenticated user
        
    Returns:
        FileResponse: The image file with correct MIME type
    """
    try:
        # Validate path
        validated_path = validate_path(file_path)
        
        # Check if file exists
        if not validated_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Ensure it's a file, not a directory
        if not validated_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path points to a directory, not a file"
            )
        
        # Check if file is an image
        if validated_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only image files can be viewed through this endpoint"
            )
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(validated_path))
        
        return FileResponse(
            path=str(validated_path),
            media_type=mime_type or "image/jpeg",
            filename=validated_path.name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving file: {str(e)}"
        )


@router.get(
    "/view-metadata/{file_path:path}",
    response_model=FileViewResponse,
    summary="Get file metadata",
    description="Get metadata of an image file without downloading it"
)
async def view_file_metadata(
    file_path: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get metadata for a file without downloading it.
    
    Args:
        file_path: Path to the file within uploads/
        current_user: Current authenticated user
        
    Returns:
        FileViewResponse: File metadata
    """
    try:
        # Validate path
        validated_path = validate_path(file_path)
        
        # Check if file exists
        if not validated_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Get file info
        file_info = await get_file_info(validated_path)
        
        return FileViewResponse(
            file_name=file_info.name,
            file_path=file_info.path,
            file_size=file_info.size,
            mime_type=file_info.mime_type or "application/octet-stream",
            created_at=file_info.created_at,
            modified_at=file_info.modified_at,
            is_image=file_info.is_image,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving file metadata: {str(e)}"
        )


@router.delete(
    "/delete/{file_path:path}",
    response_model=DeleteResponse,
    summary="Delete a file",
    description="Delete a file or folder by path"
)
async def delete_file(
    file_path: str,
    recursive: bool = False,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a file or folder.
    
    Args:
        file_path: Path to the file/folder to delete
        recursive: If True, delete folder and all contents; if False, only delete empty folders
        current_user: Current authenticated user
        
    Returns:
        DeleteResponse: Deletion status
    """
    try:
        # Validate path
        validated_path = validate_path(file_path)
        
        # Check if path exists
        if not validated_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File or folder not found"
            )
        
        # Delete file or folder
        if validated_path.is_file():
            await aiofiles.os.remove(str(validated_path))
            item_type = "file"
        elif validated_path.is_dir():
            if recursive:
                # Delete folder and all contents
                import shutil
                shutil.rmtree(str(validated_path))
            else:
                # Only delete if empty
                if list(validated_path.iterdir()):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Folder is not empty. Use recursive=true to delete with contents."
                    )
                await aiofiles.os.rmdir(str(validated_path))
            item_type = "folder"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unknown item type"
            )
        
        return DeleteResponse(
            success=True,
            message=f"{item_type.capitalize()} deleted successfully",
            deleted_path=str(validated_path.relative_to(ROOT_DIR)),
            type=item_type,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deletion failed: {str(e)}"
        )


@router.post(
    "/create-folder",
    response_model=CreateFolderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new folder",
    description="Create a new folder at specified path"
)
async def create_folder(
    folder_name: str,
    parent_path: str = "",
    current_user: User = Depends(get_current_user),
):
    """
    Create a new folder.
    
    Args:
        folder_name: Name of the folder to create
        parent_path: Parent folder path (default: root uploads/)
        current_user: Current authenticated user
        
    Returns:
        CreateFolderResponse: Folder creation status
    """
    try:
        # Validate folder name
        if not validate_filename(folder_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid folder name characters"
            )
        
        # Get parent path
        if parent_path:
            parent = validate_path(parent_path)
        else:
            parent = ROOT_DIR
        
        # Create full folder path
        folder_path = parent / folder_name
        
        # Check if folder already exists
        if folder_path.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Folder already exists"
            )
        
        # Create folder
        folder_path.mkdir(parents=True, exist_ok=False)
        
        return CreateFolderResponse(
            success=True,
            message="Folder created successfully",
            folder_name=folder_name,
            folder_path=str(folder_path.relative_to(ROOT_DIR)),
            created_at=datetime.now(),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Folder creation failed: {str(e)}"
        )


@router.get(
    "/list/{folder_path:path}",
    response_model=FolderContents,
    summary="List folder contents",
    description="List all files and subfolders in a given folder"
)
async def list_folder_contents(
    folder_path: str = "",
    current_user: User = Depends(get_current_user),
):
    """
    List all files and folders in a directory.
    
    Returns both subfolders and files with metadata.
    Supports parent directory navigation.
    
    Args:
        folder_path: Path to the folder (default: root uploads/)
        current_user: Current authenticated user
        
    Returns:
        FolderContents: Folder contents with files and subfolders
    """
    try:
        # Get folder path
        if folder_path:
            current_folder = validate_path(folder_path)
        else:
            current_folder = ROOT_DIR
        
        # Check if path is a directory
        if not current_folder.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )
        
        if not current_folder.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path is not a directory"
            )
        
        # Get parent path
        parent_path = None
        if current_folder != ROOT_DIR:
            parent_path = str(current_folder.parent.relative_to(ROOT_DIR))
        
        # List contents
        files = []
        folders = []
        
        for item in sorted(current_folder.iterdir()):
            try:
                info = await get_file_info(item)
                if item.is_file():
                    files.append(info)
                elif item.is_dir():
                    folders.append(info)
            except Exception as e:
                # Skip items that can't be read
                continue
        
        return FolderContents(
            path=str(current_folder.relative_to(ROOT_DIR)) if current_folder != ROOT_DIR else "",
            parent_path=parent_path,
            files=files,
            folders=folders,
            total_items=len(files) + len(folders),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing folder: {str(e)}"
        )


@router.get(
    "/navigate/{folder_path:path}",
    response_model=FolderContents,
    summary="Navigate folders",
    description="Navigate through folders with parent directory support (..)"
)
async def navigate_folders(
    folder_path: str,
    current_user: User = Depends(get_current_user),
):
    """
    Navigate through folders with support for '..' parent directory.
    
    Args:
        folder_path: Path to navigate (supports .. for parent)
        current_user: Current authenticated user
        
    Returns:
        FolderContents: Contents of the navigated folder
    """
    try:
        # Handle parent directory navigation
        if folder_path == "..":
            # Go to parent of root - just return root
            return await list_folder_contents("", current_user)
        
        # Check if path ends with /..
        if folder_path.endswith("/.."):
            # Remove the /.. and navigate to parent
            base_path = folder_path[:-3].rstrip("/")
            if base_path:
                current = validate_path(base_path)
            else:
                current = ROOT_DIR
            
            if current == ROOT_DIR:
                return await list_folder_contents("", current_user)
            else:
                parent = current.parent
                if parent.resolve() == ROOT_DIR.resolve():
                    return await list_folder_contents("", current_user)
                else:
                    return await list_folder_contents(
                        str(parent.relative_to(ROOT_DIR)),
                        current_user
                    )
        
        # Normal folder listing
        return await list_folder_contents(folder_path, current_user)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Navigation failed: {str(e)}"
        )


@router.get(
    "/info/{file_path:path}",
    response_model=FileInfo,
    summary="Get file/folder info",
    description="Get detailed information about a file or folder"
)
async def get_info(
    file_path: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed information about a file or folder.
    
    Args:
        file_path: Path to the file/folder
        current_user: Current authenticated user
        
    Returns:
        FileInfo: Detailed file/folder information
    """
    try:
        # Validate path
        validated_path = validate_path(file_path)
        
        # Check if path exists
        if not validated_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File or folder not found"
            )
        
        return await get_file_info(validated_path)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting info: {str(e)}"
        )


@router.post(
    "/rename/{file_path:path}",
    response_model=dict,
    summary="Rename file or folder",
    description="Rename a file or folder"
)
async def rename_item(
    file_path: str,
    new_name: str,
    current_user: User = Depends(get_current_user),
):
    """
    Rename a file or folder.
    
    Args:
        file_path: Path to the file/folder to rename
        new_name: New name for the item
        current_user: Current authenticated user
        
    Returns:
        dict: Rename status and new path
    """
    try:
        # Validate path and new name
        validated_path = validate_path(file_path)
        if not validate_filename(new_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename characters"
            )
        
        # Check if item exists
        if not validated_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File or folder not found"
            )
        
        # Create new path
        new_path = validated_path.parent / new_name
        
        # Check if new name already exists
        if new_path.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A file or folder with that name already exists"
            )
        
        # Rename using aiofiles
        import shutil
        shutil.move(str(validated_path), str(new_path))
        
        return {
            "success": True,
            "message": "Item renamed successfully",
            "old_path": str(validated_path.relative_to(ROOT_DIR)),
            "new_path": str(new_path.relative_to(ROOT_DIR)),
            "new_name": new_name,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rename failed: {str(e)}"
        )
