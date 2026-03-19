class AuditService:
    def list_operation_logs(self) -> list[dict]:
        return [
            {'id': 1, 'module': 'mall', 'action': 'create_product', 'path': '/api/admin/v1/mall/products'},
            {'id': 2, 'module': 'org', 'action': 'update_department', 'path': '/api/admin/v1/org/departments/2'},
        ]


service = AuditService()
