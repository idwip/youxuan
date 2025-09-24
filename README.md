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

修改总结
在 fetch-ips.yml 中的修改：
工作流名称：Every 2 Hours → Every 3 Hours

Cron表达式：'50 */2 * * *' → '0 */3 * * *'（每3小时运行一次）

新增步骤：添加了3分钟等待步骤

新增步骤：添加了触发DNS更新工作流的步骤

在 update-dns.yml 中的修改：
触发器类型：移除原来的schedule，改为workflow_run

触发条件：现在由IP获取工作流成功完成后触发

运行条件：添加了成功条件判断if: ${{ github.event.workflow_run.conclusion == 'success' }}

新的工作流程
每3小时 → fetch-ips.yml 自动运行获取IP

获取成功 → 等待3分钟

3分钟后 → 自动触发 update-dns.yml 更新DNS

DNS更新 → 使用新的IP文件更新Cloudflare记录

时间修改说明
IP获取频率：每3小时运行一次（00:00, 03:00, 06:00... UTC时间）

DNS更新延迟：IP获取成功后等待3分钟

自动触发：DNS更新不再依赖定时任务，而是由IP获取工作流触发

这样的设置确保了IP获取和DNS更新的顺序执行，并且有3分钟的延迟缓冲期


