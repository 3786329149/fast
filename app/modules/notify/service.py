class NotifyService:
    def send_sms(self, phone: str, template_code: str, params: dict) -> dict:
        return {'channel': 'sms', 'phone': phone, 'template_code': template_code, 'params': params, 'sent': True}

    def send_wechat(self, openid: str, template_code: str, params: dict) -> dict:
        return {'channel': 'wechat', 'openid': openid, 'template_code': template_code, 'params': params, 'sent': True}

    def send_push(self, device_token: str, title: str, body: str) -> dict:
        return {'channel': 'push', 'device_token': device_token, 'title': title, 'body': body, 'sent': True}


service = NotifyService()
