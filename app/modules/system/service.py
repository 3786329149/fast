class SystemService:
    def list_configs(self) -> list[dict]:
        return [
            {'key': 'mall.order_auto_cancel_minutes', 'value': '30'},
            {'key': 'upload.max_file_size_mb', 'value': '20'},
        ]

    def list_dicts(self) -> list[dict]:
        return [
            {'type': 'order_status', 'label': '待支付', 'value': 'pending'},
            {'type': 'order_status', 'label': '已支付', 'value': 'paid'},
        ]


service = SystemService()
