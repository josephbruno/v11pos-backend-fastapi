"""
Pydantic schemas for File Manager API responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class FileInfo(BaseModel):
    """Schema for file information"""
    name: str = Field(..., description="File name")
    path: str = Field(..., description="Full file path")
    size: int = Field(..., description="File size in bytes")
    type: str = Field(..., description="File type (file/folder)")
    mime_type: Optional[str] = Field(None, description="MIME type for files")
    created_at: datetime = Field(..., description="Creation timestamp")
    modified_at: datetime = Field(..., description="Modification timestamp")
    is_image: bool = Field(..., description="Whether file is an image")

    class Config:
        from_attributes = True


class FolderContents(BaseModel):
    """Schema for folder contents response"""
    path: str = Field(..., description="Current folder path")
    parent_path: Optional[str] = Field(None, description="Parent folder path")
    files: List[FileInfo] = Field(..., description="List of files in folder")
    folders: List[FileInfo] = Field(..., description="List of subfolders")
    total_items: int = Field(..., description="Total number of items")

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    """Schema for file upload response"""
    success: bool = Field(..., description="Whether upload was successful")
    message: str = Field(..., description="Response message")
    file_name: str = Field(..., description="Uploaded file name")
    file_path: str = Field(..., description="Full path to uploaded file")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type of file")
    url: str = Field(..., description="URL to access the file")

    class Config:
        from_attributes = True


class DeleteResponse(BaseModel):
    """Schema for file/folder deletion response"""
    success: bool = Field(..., description="Whether deletion was successful")
    message: str = Field(..., description="Response message")
    deleted_path: str = Field(..., description="Path of deleted item")
    type: str = Field(..., description="Type of deleted item (file/folder)")

    class Config:
        from_attributes = True


class CreateFolderResponse(BaseModel):
    """Schema for folder creation response"""
    success: bool = Field(..., description="Whether folder creation was successful")
    message: str = Field(..., description="Response message")
    folder_name: str = Field(..., description="Name of created folder")
    folder_path: str = Field(..., description="Full path of created folder")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class FileViewResponse(BaseModel):
    """Schema for file view metadata response"""
    file_name: str = Field(..., description="File name")
    file_path: str = Field(..., description="Full file path")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    created_at: datetime = Field(..., description="Creation timestamp")
    modified_at: datetime = Field(..., description="Modification timestamp")
    is_image: bool = Field(..., description="Whether file is image")

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    success: bool = Field(False, description="Success flag (always False)")
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")

    class Config:
        from_attributes = True
