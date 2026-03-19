from enum import StrEnum


class TokenScene(StrEnum):
    CLIENT = "client"
    ADMIN = "admin"


class LoginIdentityType(StrEnum):
    MOBILE_CODE = "mobile_code"
    PASSWORD = "password"
    WECHAT_MINIAPP = "wechat_miniapp"
    WECHAT_APP = "wechat_app"
    WEB_ACCOUNT = "web_account"


class DataScope(StrEnum):
    ALL = "ALL"
    ORG = "ORG"
    ORG_AND_CHILD = "ORG_AND_CHILD"
    DEPT = "DEPT"
    DEPT_AND_CHILD = "DEPT_AND_CHILD"
    SELF = "SELF"
    CUSTOM = "CUSTOM"
