class RBACService:
    def list_roles(self) -> list[dict]:
        return [
            {'id': 1, 'name': '超级管理员', 'code': 'super_admin', 'data_scope': 'ALL'},
            {'id': 2, 'name': '运营管理员', 'code': 'ops_admin', 'data_scope': 'ORG_AND_CHILD'},
        ]

    def list_menus(self) -> list[dict]:
        return [
            {'id': 1, 'name': '系统管理', 'type': 'directory', 'path': '/system'},
            {'id': 2, 'name': '商品管理', 'type': 'menu', 'path': '/mall/products'},
            {'id': 3, 'name': '订单列表', 'type': 'button', 'permission_code': 'mall:order:list'},
        ]

    def list_permissions(self) -> list[dict]:
        return [
            {'id': 1, 'code': 'mall:product:list', 'name': '查看商品'},
            {'id': 2, 'code': 'mall:order:list', 'name': '查看订单'},
            {'id': 3, 'code': 'org:department:list', 'name': '查看部门'},
        ]


service = RBACService()
