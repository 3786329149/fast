class OrgService:
    def list_departments(self) -> list[dict]:
        return [
            {'id': 1, 'name': '总经办', 'parent_id': None, 'leader_user_id': 1},
            {'id': 2, 'name': '研发部', 'parent_id': 1, 'leader_user_id': 2},
            {'id': 3, 'name': '运营部', 'parent_id': 1, 'leader_user_id': 3},
        ]

    def list_employees(self) -> list[dict]:
        return [
            {'id': 1, 'user_id': 1, 'name': '管理员', 'dept_id': 1, 'title': 'CEO'},
            {'id': 2, 'user_id': 2, 'name': '张三', 'dept_id': 2, 'title': '后端工程师'},
        ]


service = OrgService()
