# 架构设计说明

## 1. 系统角色
- C 端用户：小程序、App、Web 用户端
- B 端管理员：后台管理系统
- 企业员工：组织架构中的员工身份

## 2. 认证与授权
- C 端：`client` 场景 JWT
- 后台：`admin` 场景 JWT
- 登录身份统一落在 `user_identity`
- 后台权限采用 RBAC + 数据权限

## 3. 模块边界
- `iam`：账号、登录、微信绑定、扫码登录
- `org`：公司、部门、员工关系
- `rbac`：角色、菜单、按钮、数据范围
- `mall`：商品、购物车、订单
- `payment`：支付单、退款单、回调
- `notify`：短信、微信、Push 通知
- `cms`：Banner、公告、文章
- `file`：文件元数据与上传凭证
- `audit`：登录日志、操作日志、API 访问日志

## 4. Web 扫码登录建议
1. Web 请求生成 `login_ticket`
2. Web 展示 ticket 对应二维码
3. 用户用小程序扫码
4. 小程序调用确认登录接口
5. Web 轮询 ticket 状态
6. ticket 确认后签发 client token

## 5. 数据权限建议范围
- `ALL`
- `ORG`
- `ORG_AND_CHILD`
- `DEPT`
- `DEPT_AND_CHILD`
- `SELF`
- `CUSTOM`
