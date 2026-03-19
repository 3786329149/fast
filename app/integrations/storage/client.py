class StorageClient:
    def sign_upload(self, object_key: str, content_type: str) -> dict:
        return {'object_key': object_key, 'content_type': content_type, 'signed': True}
