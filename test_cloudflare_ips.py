# final_solution_enhanced.py - 增强版CloudFlare优选IP解决方案
import requests
import re
import time
import threading
import json
from datetime import datetime
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

print("🎯 CloudFlare优选IP完整解决方案 - 增强版")
print("=" * 60)

# 所有可用的网站配置
WEBSITES = [
    # 主要网站（确认可用）
    {"name": "IP排行榜", "url": "https://ip.164746.xyz/ipTop10.html", "type": "html", "enabled": True},
    {"name": "CF优选列表", "url": "https://cf.090227.xyz", "type": "text", "enabled": True},
    {"name": "Uouin优选", "url": "https://api.uouin.com/cloudflare.html", "type": "html", "enabled": True},
    {"name": "WeTest优选", "url": "https://www.wetest.vip/page/cloudflare/address_v4.html", "type": "html", "enabled": True},
    
    # 特殊网站（需要专门解析）
    {"name": "移动优化", "url": "https://ipdb.030101.xyz/bestcfv4", "type": "special_html", "enabled": True},
    {"name": "BestCF", "url": "https://bestcf.herocore.com/", "type": "special_html", "enabled": True},
]

def is_valid_ip(ip):
    """验证IP地址格式是否正确"""
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

def extract_ips_basic(response_text):
    """基础IP提取，增加验证"""
    ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', response_text)
    return [ip for ip in ips if is_valid_ip(ip)]

def extract_ips_special(response_text, site_name):
    """特殊网站IP提取"""
    ips = []
    
    if "移动" in site_name:
        # 移动优化网站的特殊解析
        rows = re.findall(r'<tr>(.*?)</tr>', response_text, re.DOTALL)
        for row in rows:
            if 'ms' in row or 'KB/s' in row:
                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', row)
                if ip_match and is_valid_ip(ip_match.group(1)):
                    ips.append(ip_match.group(1))
    
    elif "BestCF" in site_name:
        # BestCF网站的特殊解析
        rows = re.findall(r'<tr>(.*?)</tr>', response_text, re.DOTALL)
        for row in rows[1:]:  # 跳过表头
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', row)
            if ip_match and is_valid_ip(ip_match.group(1)):
                ips.append(ip_match.group(1))
    
    return ips

def get_ips_from_website(site):
    """从单个网站获取IP"""
    if not site['enabled']:
        return set()
    
    print(f"📡 获取: {site['name']}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(site['url'], headers=headers, timeout=15)
        if response.status_code == 200:
            if site['type'] == 'special_html':
                ips = extract_ips_special(response.text, site['name'])
            else:
                ips = extract_ips_basic(response.text)
            
            if ips:
                print(f"   ✅ 成功获取 {len(ips)} 个IP")
                return set(ips)
            else:
                print(f"   ⚠️  找到 0 个IP")
        else:
            print(f"   ❌ 状态码: {response.status_code}")
    except requests.exceptions.Timeout:
        print(f"   ⏰ 请求超时")
    except requests.exceptions.ConnectionError:
        print(f"   🔌 连接错误")
    except Exception as e:
        print(f"   ❌ 错误: {str(e)[:50]}...")
    
    return set()

def save_ips_to_file(ips, filename="ip.txt"):
    """保存IP到文件（只保存IP地址，一行一个）"""
    with open(filename, 'w', encoding='utf-8') as f:
        for ip, latency in ips:
            f.write(f"{ip}\n")
    
    return filename

def test_ip_speed(ip, timeout=3):
    """测试IP延迟"""
    try:
        start_time = time.time()
        socket.create_connection((ip, 443), timeout=timeout)
        end_time = time.time()
        return (ip, round((end_time - start_time) * 1000, 2))
    except socket.timeout:
        return (ip, float('inf'))
    except ConnectionRefusedError:
        return (ip, float('inf'))
    except Exception:
        return (ip, float('inf'))

def test_ips_in_batches(ips, batch_size=50, max_workers=30):
    """分批测试IP延迟"""
    all_results = []
    total_ips = len(ips)
    
    for batch_start in range(0, total_ips, batch_size):
        batch_end = min(batch_start + batch_size, total_ips)
        batch_ips = ips[batch_start:batch_end]
        
        print(f"⏱️  正在测试第 {batch_start//batch_size + 1} 批 IP ({batch_start}-{batch_end-1})...")
        
        batch_results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ip = {executor.submit(test_ip_speed, ip): ip for ip in batch_ips}
            for i, future in enumerate(as_completed(future_to_ip)):
                ip, latency = future.result()
                batch_results.append((ip, latency))
                
                # 显示进度
                if (i + 1) % 10 == 0 or (i + 1) == len(batch_ips):
                    print(f"   已测试: {i + 1}/{len(batch_ips)}")
        
        all_results.extend(batch_results)
        time.sleep(1)  # 批次间短暂休息
    
    return all_results

def main():
    print("开始从所有网站获取优选IP...")
    print("=" * 50)
    
    all_ips = set()
    successful_sites = 0
    
    # 使用多线程获取IP
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_site = {executor.submit(get_ips_from_website, site): site for site in WEBSITES if site['enabled']}
        
        for future in as_completed(future_to_site):
            site = future_to_site[future]
            try:
                ips = future.result()
                if ips:
                    all_ips.update(ips)
                    successful_sites += 1
            except Exception as e:
                print(f"   ❌ {site['name']} 处理异常: {e}")
    
    print(f"\n🎉 完成! 从 {successful_sites}/{len([s for s in WEBSITES if s['enabled']])} 个网站获取到 {len(all_ips)} 个唯一IP")
    
    if not all_ips:
        print("❌ 未能获取到任何IP，请检查网络连接")
        return
    
    # 测试所有IP的延迟
    all_ips_list = list(all_ips)
    print(f"\n⏱️  开始测试所有 {len(all_ips_list)} 个IP的延迟...")
    print("这可能需要一些时间，请耐心等待...")
    
    # 分批测试IP延迟
    tested_results = test_ips_in_batches(all_ips_list, batch_size=30, max_workers=30)
    
    # 按延迟排序（从低到高）
    tested_results.sort(key=lambda x: x[1])
    
    # 保存测试结果到ip.txt（只保存IP地址）
    filename = save_ips_to_file(tested_results, "ip.txt")
    print(f"💾 所有IP已按延迟排序保存到: {filename}")
    
    # 显示延迟测试结果
    print(f"\n📊 延迟测试结果 (前{min(20, len(tested_results))}个最佳IP):")
    print("-" * 50)
    for i, (ip, latency) in enumerate(tested_results[:20], 1):
        if latency == float('inf'):
            status = "❌ 超时"
        elif latency < 100:
            status = "✅ 优秀 (<100ms)"
        elif latency < 200:
            status = "✅ 良好 (100-200ms)"
        elif latency < 300:
            status = "⚠️  一般 (200-300ms)"
        else:
            status = "❌ 较差 (>300ms)"
        print(f"   {i:2d}. {ip:<15} {latency:>6}ms {status}")
    
    # 显示统计信息
    successful_tests = len([r for r in tested_results if r[1] != float('inf')])
    excellent_ips = len([r for r in tested_results if r[1] < 100])
    good_ips = len([r for r in tested_results if 100 <= r[1] < 200])
    average_ips = len([r for r in tested_results if 200 <= r[1] < 300])
    poor_ips = len([r for r in tested_results if r[1] >= 300 and r[1] != float('inf')])
    timeout_ips = len([r for r in tested_results if r[1] == float('inf')])
    
    print(f"\n📈 测试统计:")
    print(f"   总测试IP: {len(tested_results)}")
    print(f"   成功响应: {successful_tests}")
    print(f"   超时IP: {timeout_ips}")
    print(f"   优秀(<100ms): {excellent_ips}")
    print(f"   良好(100-200ms): {good_ips}")
    print(f"   一般(200-300ms): {average_ips}")
    print(f"   较差(>300ms): {poor_ips}")
    
    # 推荐最佳IP
    best_ips = [ip for ip, latency in tested_results if latency < 200][:10]
    if best_ips:
        print(f"\n🌟 推荐使用的最佳IP (延迟<200ms):")
        for i, ip in enumerate(best_ips[:5], 1):
            latency = next((lat for ip_addr, lat in tested_results if ip_addr == ip), float('inf'))
            print(f"   {i}. {ip} ({latency}ms)")

if __name__ == "__main__":
    main()