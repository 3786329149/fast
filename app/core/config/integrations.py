from pydantic import BaseModel


class WechatSettings(BaseModel):
    WECHAT_API_MOCK: bool = True
    WECHAT_API_BASE_URL: str = "https://api.weixin.qq.com"
    WECHAT_PAY_API_BASE_URL: str = "https://api.mch.weixin.qq.com"
    WECHAT_MINIAPP_APPID: str = "replace-me"
    WECHAT_MINIAPP_SECRET: str = "replace-me"
    WECHAT_MCH_ID: str = "replace-me"
    WECHAT_MCH_SERIAL_NO: str = ""
    WECHAT_MCH_API_V3_KEY: str = "replace-me"
    WECHAT_MCH_PRIVATE_KEY_PATH: str = "./certs/apiclient_key.pem"
    WECHAT_PAY_PLATFORM_PUBLIC_KEY_PATH: str = "./certs/wechatpay_public_key.pem"
    WECHAT_NOTIFY_URL: str = "https://example.com/api/open/v1/pay/wechat/callback"
    WECHAT_PAY_CURRENCY: str = "CNY"
    WECHAT_HTTP_TIMEOUT_SECONDS: int = 8
    WECHAT_ACCESS_TOKEN_CACHE_SECONDS: int = 7000
    WECHAT_PAY_VERIFY_CALLBACK_SIGNATURE: bool = False

    @property
    def WECHAT_PAYMENT_ENABLED(self) -> bool:
        return not self.WECHAT_API_MOCK and all(
            [
                self.WECHAT_MINIAPP_APPID != "replace-me",
                self.WECHAT_MCH_ID != "replace-me",
                self.WECHAT_MCH_API_V3_KEY != "replace-me",
                bool(self.WECHAT_MCH_SERIAL_NO),
            ]
        )


class ProviderSettings(BaseModel):
    SMS_PROVIDER: str = "mock"
    STORAGE_PROVIDER: str = "mock"
    PUSH_PROVIDER: str = "mock"
