# API 概览

## Admin
- `POST /api/admin/v1/auth/login`
- `GET /api/admin/v1/auth/me`
- `GET /api/admin/v1/org/departments`
- `GET /api/admin/v1/rbac/menus`
- `GET /api/admin/v1/mall/products`

## Client
- `POST /api/client/v1/auth/send-code`
- `POST /api/client/v1/auth/login-by-code`
- `POST /api/client/v1/auth/login-by-password`
- `GET /api/client/v1/products`
- `POST /api/client/v1/orders`

## WeChat
- `POST /api/wechat/v1/auth/login`
- `POST /api/wechat/v1/auth/bind-mobile`
- `POST /api/wechat/v1/qr-login/scan`
- `POST /api/wechat/v1/qr-login/confirm`

## Open
- `POST /api/open/v1/pay/wechat/callback`
