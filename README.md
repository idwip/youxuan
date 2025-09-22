✅ 需要设置的 GitHub 配置
1. Secrets（敏感信息，必须设置）：
CLOUDFLARE_API_TOKEN - 你的 Cloudflare API Token

CLOUDFLARE_ZONE_ID - 你的域名 Zone ID（可选，不设置会自动获取）

2. Variables（可选配置）：
DOMAIN - 主域名（默认：ssssb.ggff.net）

SUBDOMAIN - 子域名（默认：yx）

主要改动说明
只改了重要参数：API_TOKEN、ZONE_ID、DOMAIN、SUBDOMAIN 改为环境变量

功能完全不变：分页获取、去重、限制200条、重试机制等都保留

ZONE_ID 可选：如果不设置环境变量，会自动通过 API 获取

保持原有逻辑：所有业务逻辑和错误处理都保持不变

这样既保证了安全性（敏感信息不暴露），又保持了原有的所有功能！


