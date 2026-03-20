class PushClient:
    def send(self, device_token: str, title: str, body: str) -> dict:
        return {'device_token': device_token, 'title': title, 'body': body, 'sent': True}
