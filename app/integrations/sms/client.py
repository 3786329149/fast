class SMSClient:
    def send_code(self, phone: str, code: str) -> dict:
        return {'phone': phone, 'code': code, 'sent': True}
