from __future__ import annotations

import base64
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class WeChatCryptoError(RuntimeError):
    pass


class WeChatCrypto:
    @staticmethod
    def load_private_key(path: str):
        try:
            data = Path(path).read_bytes()
        except FileNotFoundError as exc:
            raise WeChatCryptoError(f'未找到微信支付私钥文件: {path}') from exc
        return serialization.load_pem_private_key(data, password=None)

    @staticmethod
    def load_public_key(path: str):
        try:
            data = Path(path).read_bytes()
        except FileNotFoundError as exc:
            raise WeChatCryptoError(f'未找到微信支付平台公钥文件: {path}') from exc
        return serialization.load_pem_public_key(data)

    @staticmethod
    def sign_rsa_sha256(message: str, private_key) -> str:
        signature = private_key.sign(
            message.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode('utf-8')

    @staticmethod
    def verify_rsa_sha256(message: str, signature_b64: str, public_key) -> bool:
        try:
            public_key.verify(
                base64.b64decode(signature_b64),
                message.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            return True
        except Exception:
            return False

    @staticmethod
    def decrypt_aes_gcm(*, api_v3_key: str, nonce: str, ciphertext: str, associated_data: str = '') -> str:
        aesgcm = AESGCM(api_v3_key.encode('utf-8'))
        plaintext = aesgcm.decrypt(
            nonce=nonce.encode('utf-8'),
            data=base64.b64decode(ciphertext),
            associated_data=associated_data.encode('utf-8'),
        )
        return plaintext.decode('utf-8')
