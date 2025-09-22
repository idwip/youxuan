✅ 一、准备 GitHub 仓库文件结构
创建以下文件结构：

text
your-repo/
├── .github/
│   └── workflows/
│       ├── fetch-ips.yml
│       └── update-dns.yml
├── test_cloudflare_ips.py
├── cf_update_dns.py
├── ip.txt
└── requirements.txt
✅ 二、创建 requirements.txt
text
requests
✅ 三、创建 GitHub Actions 工作流文件
1. 获取 IP 的工作流：.github/workflows/fetch-ips.yml
yaml
name: Fetch Cloudflare IPs Every 2 Hours

on:
  schedule:
    - cron: '0 */2 * * *'  # 每2小时运行一次
  workflow_dispatch:        # 允许手动触发

jobs:
  fetch-ips:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: pip install -r requirements.txt

    - name: Run IP fetcher
      run: python test_cloudflare_ips.py

    - name: Commit and push if changed
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add ip.txt
        git diff --staged --quiet || git commit -m "Update IPs - $(date)"
        git push
2. 更新 DNS 的工作流：.github/workflows/update-dns.yml
yaml
name: Update Cloudflare DNS Every 2 Hours 10 Minutes

on:
  schedule:
    - cron: '10 */2 * * *'  # 每2小时10分钟运行一次
  workflow_dispatch:

jobs:
  update-dns:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: pip install -r requirements.txt

    - name: Run DNS Updater
      env:
        API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
      run: python cf_update_dns.py
✅ 四、设置 GitHub Secrets
在仓库设置中设置 CLOUDFLARE_API_TOKEN：

进入仓库 → Settings → Secrets and variables → Actions → New repository secret

Name: CLOUDFLARE_API_TOKEN

Value: 你的 Cloudflare API Token

✅ 五、修改 cf_update_dns.py 以使用环境变量
将：

python
API_TOKEN = "PruReKED4nCaC2q-Ehw4Buv-WUGnLknTdsac7u7F"
改为：

python
import os
API_TOKEN = os.getenv("API_TOKEN", "PruReKED4nCaC2q-Ehw4Buv-WUGnLknTdsac7u7F")
✅ 六、推送代码到 GitHub
bash
git add .
git commit -m "Add Cloudflare IP automation"
git push origin main
✅ 七、验证工作流
进入仓库 → Actions

你应该会看到两个工作流：Fetch Cloudflare IPs 和 Update Cloudflare DNS

可以手动触发测试是否正常运行

✅ 八、注意事项
确保 ip.txt 会被 test_cloudflare_ips.py 正确生成并覆盖。

确保 cf_update_dns.py 能读取到最新的 ip.txt。

GitHub Actions 的 cron 使用的是 UTC 时间，请根据需要调整时区或 cron 表达式。
