from uuid import uuid4


class FileService:
    def create_upload_token(self, file_name: str, content_type: str) -> dict:
        object_key = f'uploads/{uuid4().hex}/{file_name}'
        return {
            'provider': 'mock',
            'upload_url': f'https://storage.example.com/{object_key}',
            'object_key': object_key,
            'content_type': content_type,
        }


service = FileService()
