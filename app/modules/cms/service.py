class CMSService:
    def list_banners(self) -> list[dict]:
        return [
            {'id': 1, 'title': '首页活动', 'image_url': 'https://example.com/banner1.png'},
            {'id': 2, 'title': '新人礼包', 'image_url': 'https://example.com/banner2.png'},
        ]

    def list_notices(self) -> list[dict]:
        return [
            {'id': 1, 'title': '系统升级公告', 'content': '本周五凌晨进行系统升级。'},
            {'id': 2, 'title': '积分活动', 'content': '下单即送积分。'},
        ]


service = CMSService()
