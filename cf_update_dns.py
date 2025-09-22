import requests
import json
import time
import os
import sys

# ======= 配置部分 =======
# 从环境变量获取API_TOKEN，如果没有则使用默认值（建议使用环境变量）
API_TOKEN = os.getenv("API_TOKEN", "PruReKED4nCaC2q-Ehw4Buv-WUGnLknTdsac7u7F")
DOMAIN = "ssssb.ggff.net"  # 主域名
SUBDOMAIN = "yx"            # 子域名前缀，如 *, www, yx
IP_FILE = "ip.txt"          # 存放 IP 文件路径
PROXIED = False             # 是否开启 Cloudflare 代理 (橙色云)
MAX_RECORDS = 200           # 只保留前 200 条
RETRY_DELAY = 3              # 出错后重试等待时间（秒）
SLEEP_TIME = 0.3             # 操作间隔防止封锁
# ========================

BASE_URL = "https://api.cloudflare.com/client/v4"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}

# ========== 获取 Zone ID ==========
def get_zone_id(domain):
    url = f"{BASE_URL}/zones"
    params = {"name": domain}
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()

    if not data["success"] or len(data["result"]) == 0:
        print(f"[Error] 无法获取域名 {domain} 的 Zone ID，返回信息：{data}")
        sys.exit(1)

    return data["result"][0]["id"]

# ========== 分页获取所有 DNS A 记录 ==========
def get_all_dns_records(zone_id, subdomain):
    dns_name = f"{subdomain}.{DOMAIN}" if subdomain != "@" else DOMAIN
    page = 1
    all_records = []

    while True:
        url = f"{BASE_URL}/zones/{zone_id}/dns_records"
        params = {"type": "A", "name": dns_name, "page": page, "per_page": 100}
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("success"):
            print(f"[Error] 获取 DNS 记录失败：{data}")
            break

        records = data["result"]
        all_records.extend(records)

        if len(records) < 100:
            break
        page += 1

    return all_records

# ========== 添加新记录 ==========
def add_record(zone_id, subdomain, ip):
    dns_name = f"{subdomain}.{DOMAIN}" if subdomain != "@" else DOMAIN
    url = f"{BASE_URL}/zones/{zone_id}/dns_records"
    data = {
        "type": "A",
        "name": dns_name,
        "content": ip,
        "ttl": 120,
        "proxied": PROXIED
    }
    resp = requests.post(url, headers=headers, json=data)
    result = resp.json()

    if result.get("success"):
        print(f"[Add] 添加成功：{ip}")
        return True
    else:
        print(f"[Error] 添加失败：{ip} - {result}")
        return False

# ========== 删除记录 ==========
def delete_record(zone_id, record_id, ip):
    url = f"{BASE_URL}/zones/{zone_id}/dns_records/{record_id}"
    resp = requests.delete(url, headers=headers)
    result = resp.json()

    if result.get("success"):
        print(f"[Delete] 删除成功：{ip}")
        return True
    else:
        print(f"[Error] 删除失败：{ip} - {result}")
        return False

# ========== 主流程 ==========
def main():
    # 检查 ip.txt 是否存在
    if not os.path.exists(IP_FILE):
        print(f"[Error] 找不到文件 {IP_FILE}")
        sys.exit(1)

    # 读取 IP 文件，去重并保持顺序
    with open(IP_FILE, "r", encoding="utf-8") as f:
        ip_list = list(dict.fromkeys([line.strip() for line in f if line.strip()]))

    if not ip_list:
        print("[Error] IP 文件为空")
        sys.exit(1)

    print(f"[Info] 从文件读取到 {len(ip_list)} 个唯一 IP")

    # 限制前 200 条
    if len(ip_list) > MAX_RECORDS:
        print(f"[Warning] 超过 {MAX_RECORDS} 条，仅保留前 {MAX_RECORDS} 条")
        ip_list = ip_list[:MAX_RECORDS]

    # 获取 Zone ID
    zone_id = get_zone_id(DOMAIN)
    print(f"[Info] Zone ID: {zone_id}")

    # 获取当前已有的 A 记录
    existing_records = get_all_dns_records(zone_id, SUBDOMAIN)
    print(f"[Info] 当前已有 {len(existing_records)} 条记录")

    existing_ips = {r["content"]: r for r in existing_records}  # IP -> 记录

    failed_ips = []

    # === 添加或跳过新 IP ===
    print("[Info] 开始处理新增记录...")
    for ip in ip_list:
        if ip in existing_ips:
            print(f"[Skip] {ip} 已存在，跳过")
            continue
        success = add_record(zone_id, SUBDOMAIN, ip)
        if not success:
            failed_ips.append(ip)
        time.sleep(SLEEP_TIME)

    # === 删除不在前200的新列表的旧IP ===
    print("[Info] 开始删除多余旧记录...")
    for record in existing_records:
        old_ip = record["content"]
        if old_ip not in ip_list:
            delete_record(zone_id, record["id"], old_ip)
            time.sleep(SLEEP_TIME)

    # === 重试失败 IP ===
    if failed_ips:
        print(f"[Retry] 准备重试 {len(failed_ips)} 条失败的记录...")
        time.sleep(RETRY_DELAY)
        for ip in failed_ips:
            success = add_record(zone_id, SUBDOMAIN, ip)
            if not success:
                print(f"[Error] 重试失败：{ip}")
            time.sleep(SLEEP_TIME)

    print("[Info] 所有操作完成！")

if __name__ == "__main__":
    main()