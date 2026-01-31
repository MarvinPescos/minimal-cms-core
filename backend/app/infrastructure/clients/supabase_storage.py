from supabase import create_client, Client
from app.core import settings
import uuid

class SupabaseStorageClient:
    """Client for Supabase Storage operations - create fresh client each time"""
    def __init__(self, bucket_name: str = "images"):
        self.bucket_name = bucket_name

    def _get_client(self) -> Client:
        """Create a fresh Supabase admin client"""
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    
    async def upload_image(
        self,
        file_bytes: bytes,
        user_id: uuid.UUID,
        folder: str ,
        file_name : str | None = None,
        content_type: str = "image/jpeg",
    ) -> str :
        """
            Upload iamge to supabase storage 

            Args:
            file_bytes: Raw image bytes
            file_name: Optional custom filename, auto-generated if not provided
            content_type: MIME type of the image
            folder: Subfolder in the bucket
            
        Returns:
            Public URL of the uploaded image
        """
        if not file_name:
            extension = content_type.split("/")[-1]
            file_name = f"{uuid.uuid4()}.{extension}"
        
        file_path = f"{user_id}/{folder}/{file_name}"

        client = self._get_client()
        client.storage.from_(self.bucket_name).upload(
            path=file_path,
            file=file_bytes,
            file_options={"content-type": content_type}
        )
        
        url_response = client.storage.from_(self.bucket_name).get_public_url(file_path)
        
        return url_response

    async def delete_image(self, file_path: str) -> bool:
        """Delete an image from storage"""
        try:
            client = self._get_client()
            client.storage.from_(self.bucket_name).remove(file_path)
            return True
        except Exception:
            return False
        
def get_storage_client() -> SupabaseStorageClient:
    """Returns a storage client (wrapper is lightweight, client created per-operation)"""
    return SupabaseStorageClient()

