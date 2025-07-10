#!/usr/bin/env python3
"""
配置检查脚本
用于验证DNS更新脚本的配置是否正确
"""

import os
import sys
import socket
import requests
from pathlib import Path
from dotenv import load_dotenv
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
from aliyunsdkalidns.request.v20150109.DescribeDomainRecordsRequest import DescribeDomainRecordsRequest

# 加载环境变量
load_dotenv()

def check_environment_variables():
    """检查环境变量配置"""
    print("=== 检查环境变量配置 ===")
    
    required_vars = {
        'ALIYUN_ACCESS_KEY_ID': os.getenv('ALIYUN_ACCESS_KEY_ID'),
        'ALIYUN_ACCESS_KEY_SECRET': os.getenv('ALIYUN_ACCESS_KEY_SECRET'),
        'DOMAIN_NAME': os.getenv('DOMAIN_NAME'),
        'RR': os.getenv('RR')
    }
    
    optional_vars = {
        'TTL': os.getenv('TTL', '600'),
        'LINE': os.getenv('LINE', 'default'),
        'LANG': os.getenv('LANG', 'zh'),
        'REGION': os.getenv('REGION', 'cn-hangzhou'),
        'MAX_RETRIES': os.getenv('MAX_RETRIES', '3'),
        'RETRY_DELAY': os.getenv('RETRY_DELAY', '5'),
        'VERIFY_DNS_UPDATE': os.getenv('VERIFY_DNS_UPDATE', 'false'),
        'SKIP_PROXY': os.getenv('SKIP_PROXY', 'false')
    }
    
    all_good = True
    
    # 检查必需变量
    for var_name, var_value in required_vars.items():
        if var_value:
            print(f"✓ {var_name}: {'*' * min(len(var_value), 10)}...")
        else:
            print(f"✗ {var_name}: 未设置")
            all_good = False
    
    # 显示可选变量
    print("\n可选配置:")
    for var_name, var_value in optional_vars.items():
        print(f"  {var_name}: {var_value}")
    
    return all_good

def check_network_connectivity():
    """检查网络连接"""
    print("\n=== 检查网络连接 ===")
    
    # 测试IPv6连接
    ipv6_services = [
        'https://api64.ipify.org',
        'https://v6.ident.me',
        'https://ipv6.icanhazip.com'
    ]
    
    ipv6_working = False
    skip_proxy = os.getenv('SKIP_PROXY', 'false').lower() == 'true'
    proxies = {} if skip_proxy else None
    
    for service in ipv6_services:
        try:
            response = requests.get(service, timeout=10, proxies=proxies)
            if response.status_code == 200:
                ipv6 = response.text.strip()
                if is_valid_ipv6(ipv6):
                    print(f"✓ IPv6连接正常: {ipv6} (来源: {service})")
                    ipv6_working = True
                    break
        except Exception as e:
            print(f"✗ {service}: {e}")
    
    if not ipv6_working:
        print("✗ 无法获取IPv6地址，请检查网络连接")
    
    return ipv6_working

def is_valid_ipv6(ip):
    """验证IPv6地址格式"""
    try:
        socket.inet_pton(socket.AF_INET6, ip)
        return not (ip.startswith('::1') or ip.startswith('fe80:') or 
                   ip.startswith('fc00:') or ip.startswith('fd00:'))
    except socket.error:
        return False

def check_aliyun_credentials():
    """检查阿里云凭证"""
    print("\n=== 检查阿里云凭证 ===")
    
    access_key_id = os.getenv('ALIYUN_ACCESS_KEY_ID')
    access_key_secret = os.getenv('ALIYUN_ACCESS_KEY_SECRET')
    region = os.getenv('REGION', 'cn-hangzhou')
    
    if not access_key_id or not access_key_secret:
        print("✗ 阿里云凭证未配置")
        return False
    
    try:
        client = AcsClient(access_key_id, access_key_secret, region)
        
        # 尝试调用API
        request = DescribeDomainRecordsRequest()
        request.set_accept_format('json')
        request.set_DomainName('test.example.com')  # 使用一个不存在的域名测试
        
        try:
            client.do_action_with_exception(request)
        except ServerException as e:
            if 'InvalidDomainName.NoExist' in str(e):
                print("✓ 阿里云凭证验证成功")
                return True
            else:
                print(f"✗ 阿里云API调用失败: {e}")
                return False
        except ClientException as e:
            print(f"✗ 阿里云客户端错误: {e}")
            return False
            
    except Exception as e:
        print(f"✗ 阿里云凭证验证失败: {e}")
        return False

def check_dns_records():
    """检查DNS记录"""
    print("\n=== 检查DNS记录 ===")
    
    domain_name = os.getenv('DOMAIN_NAME')
    rr = os.getenv('RR')
    access_key_id = os.getenv('ALIYUN_ACCESS_KEY_ID')
    access_key_secret = os.getenv('ALIYUN_ACCESS_KEY_SECRET')
    region = os.getenv('REGION', 'cn-hangzhou')
    
    if not all([domain_name, rr, access_key_id, access_key_secret]):
        print("✗ 配置不完整，无法检查DNS记录")
        return False
    
    try:
        client = AcsClient(access_key_id, access_key_secret, region)
        
        request = DescribeDomainRecordsRequest()
        request.set_accept_format('json')
        request.set_DomainName(domain_name)
        request.set_RRKeyWord(rr)
        request.set_Type('AAAA')
        
        response = client.do_action_with_exception(request)
        import json
        response_json = json.loads(response.decode('utf-8'))
        
        if 'DomainRecords' in response_json and 'Record' in response_json['DomainRecords']:
            records = response_json['DomainRecords']['Record']
            aaaa_records = [r for r in records if r['RR'] == rr and r['Type'] == 'AAAA']
            
            if aaaa_records:
                for record in aaaa_records:
                    print(f"✓ 找到AAAA记录: {record['RR']}.{domain_name} -> {record['Value']}")
                    print(f"  RecordId: {record['RecordId']}")
                    print(f"  TTL: {record['TTL']}")
                    print(f"  状态: {record['Status']}")
                return True
            else:
                print(f"✗ 未找到 {rr}.{domain_name} 的AAAA记录")
                print("请先在阿里云DNS控制台创建一个AAAA记录")
                return False
        else:
            print(f"✗ 域名 {domain_name} 没有DNS记录")
            return False
            
    except Exception as e:
        print(f"✗ 检查DNS记录失败: {e}")
        return False

def check_file_permissions():
    """检查文件权限"""
    print("\n=== 检查文件权限 ===")
    
    script_dir = Path(__file__).parent
    
    # 检查脚本文件
    script_file = script_dir / 'update_dns.py'
    if script_file.exists() and os.access(script_file, os.R_OK):
        print(f"✓ 主脚本可读: {script_file}")
    else:
        print(f"✗ 主脚本不可读: {script_file}")
        return False
    
    # 检查日志目录
    log_dir = script_dir / 'logs'
    if not log_dir.exists():
        try:
            log_dir.mkdir()
            print(f"✓ 创建日志目录: {log_dir}")
        except Exception as e:
            print(f"✗ 无法创建日志目录: {e}")
            return False
    else:
        print(f"✓ 日志目录存在: {log_dir}")
    
    # 检查缓存文件权限
    cache_file = script_dir / '.last_ipv6'
    try:
        cache_file.touch()
        print(f"✓ 缓存文件可写: {cache_file}")
    except Exception as e:
        print(f"✗ 缓存文件不可写: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("IPv6 DNS自动更新脚本 - 配置检查工具")
    print("=" * 50)
    
    checks = [
        ("环境变量", check_environment_variables),
        ("网络连接", check_network_connectivity),
        ("阿里云凭证", check_aliyun_credentials),
        ("DNS记录", check_dns_records),
        ("文件权限", check_file_permissions)
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"✗ {check_name}检查出错: {e}")
            results[check_name] = False
    
    # 总结
    print("\n" + "=" * 50)
    print("检查结果总结:")
    
    all_passed = True
    for check_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {check_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有检查都通过了！脚本应该可以正常运行。")
        print("您可以运行 'python update_dns.py' 来测试脚本。")
    else:
        print("\n⚠️  有些检查未通过，请根据上述信息修复配置。")
        print("修复后可以重新运行此检查脚本。")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())