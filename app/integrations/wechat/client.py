from __future__ import annotations

import json
import secrets
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import Settings, get_settings
from app.integrations.wechat.crypto import WeChatCrypto, WeChatCryptoError


class WeChatApiError(RuntimeError):
    pass


@dataclass(slots=True)
class WeChatCallbackResult:
    verified: bool
    resource: dict[str, Any]
    raw: dict[str, Any]


class WeChatMiniClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._token_cache: dict[str, Any] = {'value': None, 'expires_at': 0}

    @property
    def mock_mode(self) -> bool:
        return self.settings.WECHAT_API_MOCK

    async def code_to_session(self, code: str) -> dict[str, Any]:
        if self.mock_mode:
            tail = code[-8:] if code else 'mockcode'
            return {
                'openid': f'mini_{tail}',
                'unionid': f'union_{tail}',
                'session_key': f'session_{tail}',
            }

        params = {
            'appid': self.settings.WECHAT_MINIAPP_APPID,
            'secret': self.settings.WECHAT_MINIAPP_SECRET,
            'js_code': code,
            'grant_type': 'authorization_code',
        }
        data = await self._request_json('GET', f'{self.settings.WECHAT_API_BASE_URL}/sns/jscode2session', params=params)
        self._raise_for_wechat_error(data)
        return data

    async def get_access_token(self) -> str:
        if self.mock_mode:
            return 'mock-access-token'

        now = int(time.time())
        if self._token_cache['value'] and now < int(self._token_cache['expires_at']):
            return str(self._token_cache['value'])

        params = {
            'grant_type': 'client_credential',
            'appid': self.settings.WECHAT_MINIAPP_APPID,
            'secret': self.settings.WECHAT_MINIAPP_SECRET,
        }
        data = await self._request_json('GET', f'{self.settings.WECHAT_API_BASE_URL}/cgi-bin/token', params=params)
        self._raise_for_wechat_error(data)
        access_token = str(data['access_token'])
        expires_in = int(data.get('expires_in', self.settings.WECHAT_ACCESS_TOKEN_CACHE_SECONDS))
        self._token_cache = {
            'value': access_token,
            'expires_at': now + max(60, expires_in - 120),
        }
        return access_token

    async def get_user_phone_number(self, phone_code: str) -> dict[str, Any]:
        if self.mock_mode:
            tail = phone_code[-4:] if phone_code else '0000'
            return {
                'phone_info': {
                    'phoneNumber': f'1380000{tail}',
                    'purePhoneNumber': f'1380000{tail}',
                    'countryCode': '86',
                }
            }

        access_token = await self.get_access_token()
        data = await self._request_json(
            'POST',
            f'{self.settings.WECHAT_API_BASE_URL}/wxa/business/getuserphonenumber',
            params={'access_token': access_token},
            json={'code': phone_code},
        )
        self._raise_for_wechat_error(data)
        return data

    async def create_miniapp_jsapi_order(
        self,
        *,
        description: str,
        out_trade_no: str,
        total_fee_fen: int,
        payer_openid: str,
        attach: str | None = None,
    ) -> dict[str, Any]:
        if self.mock_mode:
            prepay_id = f'wx_mock_{out_trade_no}'
            return {
                'prepay_id': prepay_id,
                'pay_params': self.build_miniapp_pay_params(prepay_id),
                'mock': True,
            }

        body = {
            'appid': self.settings.WECHAT_MINIAPP_APPID,
            'mchid': self.settings.WECHAT_MCH_ID,
            'description': description,
            'out_trade_no': out_trade_no,
            'notify_url': self.settings.WECHAT_NOTIFY_URL,
            'amount': {
                'total': total_fee_fen,
                'currency': self.settings.WECHAT_PAY_CURRENCY,
            },
            'payer': {'openid': payer_openid},
        }
        if attach:
            body['attach'] = attach

        data = await self._request_wechatpay_json('POST', '/v3/pay/transactions/jsapi', body)
        prepay_id = str(data['prepay_id'])
        data['pay_params'] = self.build_miniapp_pay_params(prepay_id)
        return data

    def build_miniapp_pay_params(self, prepay_id: str) -> dict[str, str]:
        package = f'prepay_id={prepay_id}'
        timestamp = str(int(time.time()))
        nonce_str = secrets.token_hex(16)

        if self.mock_mode:
            pay_sign = 'mock-pay-sign'
        else:
            private_key = WeChatCrypto.load_private_key(self.settings.WECHAT_MCH_PRIVATE_KEY_PATH)
            message = '\n'.join(
                [
                    self.settings.WECHAT_MINIAPP_APPID,
                    timestamp,
                    nonce_str,
                    package,
                    '',
                ]
            )
            pay_sign = WeChatCrypto.sign_rsa_sha256(message, private_key)

        return {
            'timeStamp': timestamp,
            'nonceStr': nonce_str,
            'package': package,
            'signType': 'RSA',
            'paySign': pay_sign,
        }

    def parse_payment_callback(self, *, headers: dict[str, str], body: str) -> WeChatCallbackResult:
        payload = json.loads(body)
        verified = False

        if self.mock_mode and not self.settings.WECHAT_PAY_VERIFY_CALLBACK_SIGNATURE:
            verified = True
        else:
            verified = self.verify_callback_signature(headers=headers, body=body)
            if not verified:
                raise WeChatApiError('微信支付回调签名校验失败')

        resource = payload.get('resource') or {}
        if resource:
            decrypted_text = WeChatCrypto.decrypt_aes_gcm(
                api_v3_key=self.settings.WECHAT_MCH_API_V3_KEY,
                nonce=resource['nonce'],
                ciphertext=resource['ciphertext'],
                associated_data=resource.get('associated_data', ''),
            )
            resource_data = json.loads(decrypted_text)
        else:
            resource_data = payload

        return WeChatCallbackResult(verified=verified, resource=resource_data, raw=payload)

    def verify_callback_signature(self, *, headers: dict[str, str], body: str) -> bool:
        timestamp = headers.get('Wechatpay-Timestamp') or headers.get('wechatpay-timestamp')
        nonce = headers.get('Wechatpay-Nonce') or headers.get('wechatpay-nonce')
        signature = headers.get('Wechatpay-Signature') or headers.get('wechatpay-signature')

        if not timestamp or not nonce or not signature:
            return False

        if self.mock_mode and not self.settings.WECHAT_PAY_VERIFY_CALLBACK_SIGNATURE:
            return True

        try:
            public_key = WeChatCrypto.load_public_key(self.settings.WECHAT_PAY_PLATFORM_PUBLIC_KEY_PATH)
        except WeChatCryptoError:
            if self.settings.WECHAT_PAY_VERIFY_CALLBACK_SIGNATURE:
                raise
            return False

        message = f'{timestamp}\n{nonce}\n{body}\n'
        return WeChatCrypto.verify_rsa_sha256(message, signature, public_key)

    async def _request_json(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.settings.WECHAT_HTTP_TIMEOUT_SECONDS) as client:
            response = await client.request(method, url, params=params, json=json, headers=headers)
        response.raise_for_status()
        return response.json()

    async def _request_wechatpay_json(self, method: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.WECHAT_PAYMENT_ENABLED:
            raise WeChatApiError('未配置完整的微信支付商户参数，无法发起真实微信支付')

        body_text = json.dumps(body, ensure_ascii=False, separators=(',', ':'))
        headers = self._build_wechatpay_headers(method=method, path=path, body=body_text)
        return await self._request_json(
            method,
            f'{self.settings.WECHAT_PAY_API_BASE_URL}{path}',
            json=body,
            headers=headers,
        )

    def _build_wechatpay_headers(self, *, method: str, path: str, body: str) -> dict[str, str]:
        nonce_str = secrets.token_hex(16)
        timestamp = str(int(time.time()))
        private_key = WeChatCrypto.load_private_key(self.settings.WECHAT_MCH_PRIVATE_KEY_PATH)
        canonical_url = urlparse(path)
        path_with_query = canonical_url.path if not canonical_url.query else f'{canonical_url.path}?{canonical_url.query}'
        message = '\n'.join([method.upper(), path_with_query, timestamp, nonce_str, body, ''])
        signature = WeChatCrypto.sign_rsa_sha256(message, private_key)
        authorization = (
            'WECHATPAY2-SHA256-RSA2048 '
            f'mchid="{self.settings.WECHAT_MCH_ID}",'
            f'nonce_str="{nonce_str}",'
            f'signature="{signature}",'
            f'timestamp="{timestamp}",'
            f'serial_no="{self.settings.WECHAT_MCH_SERIAL_NO}"'
        )
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': authorization,
            'User-Agent': 'fastapi-mall-enterprise-starter/0.2.0',
        }

    @staticmethod
    def _raise_for_wechat_error(payload: dict[str, Any]) -> None:
        errcode = payload.get('errcode')
        if errcode in (None, 0, '0'):
            return
        errmsg = payload.get('errmsg', '未知微信接口错误')
        raise WeChatApiError(f'微信接口调用失败: errcode={errcode}, errmsg={errmsg}')


client = WeChatMiniClient()
