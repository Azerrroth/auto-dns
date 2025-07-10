#!/usr/bin/env python3
import os
import json
import socket
import requests
import logging
import time
import re
from datetime import datetime
from pathlib import Path
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
from aliyunsdkalidns.request.v20150109.UpdateDomainRecordRequest import UpdateDomainRecordRequest
from aliyunsdkalidns.request.v20150109.DescribeDomainRecordsRequest import DescribeDomainRecordsRequest
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 阿里云配置
ACCESS_KEY_ID = os.getenv('ALIYUN_ACCESS_KEY_ID')
ACCESS_KEY_SECRET = os.getenv('ALIYUN_ACCESS_KEY_SECRET')
DOMAIN_NAME = os.getenv('DOMAIN_NAME')  # 例如：example.com
RR = os.getenv('RR')  # 子域名，例如：www
TTL = int(os.getenv('TTL', '600'))  # TTL值，默认600秒
LINE = os.getenv('LINE', 'default')  # 解析线路，默认default
LANG = os.getenv('LANG', 'zh')  # 语言，默认zh
REGION = os.getenv('REGION', 'cn-hangzhou')  # 阿里云区域，默认杭州
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))  # 最大重试次数
RETRY_DELAY = int(os.getenv('RETRY_DELAY', '5'))  # 重试延迟秒数
VERIFY_DNS_UPDATE = os.getenv('VERIFY_DNS_UPDATE', 'false').lower() == 'true'  # 是否验证DNS更新
SKIP_PROXY = os.getenv('SKIP_PROXY', 'false').lower() == 'true'  # 是否跳过系统代理

# IPv6检测服务列表（按优先级排序）
IPV6_SERVICES = [
    'https://api64.ipify.org',
    'https://v6.ident.me',
    'https://ipv6.icanhazip.com',
    'https://api.ipify.org?format=json',
]

# 设置日志
def setup_logging():
    """设置日志配置"""
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f'dns_update_{datetime.now().strftime("%Y%m")}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# 初始化日志
logger = setup_logging()

# 缓存文件路径
CACHE_FILE = Path(__file__).parent / '.last_ipv6'

def validate_config():
    """验证配置的有效性"""
    errors = []
    
    # 检查必需的环境变量
    required_vars = {
        'ALIYUN_ACCESS_KEY_ID': ACCESS_KEY_ID,
        'ALIYUN_ACCESS_KEY_SECRET': ACCESS_KEY_SECRET,
        'DOMAIN_NAME': DOMAIN_NAME,
        'RR': RR
    }
    
    for var_name, var_value in required_vars.items():
        if not var_value:
            errors.append(f"缺少必要的环境变量: {var_name}")
    
    # 验证域名格式
    if DOMAIN_NAME:
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(domain_pattern, DOMAIN_NAME):
            errors.append(f"域名格式不正确: {DOMAIN_NAME}")
    
    # 验证RR格式
    if RR:
        rr_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'
        if not re.match(rr_pattern, RR):
            errors.append(f"子域名格式不正确: {RR}")
    
    # 验证TTL值
    if TTL < 1 or TTL > 86400:
        errors.append(f"TTL值应在1-86400之间: {TTL}")
    
    if errors:
        for error in errors:
            logger.error(error)
        raise ValueError("配置验证失败: " + "; ".join(errors))
    
    logger.info("配置验证通过")

def get_cached_ipv6():
    """获取缓存的IPv6地址"""
    try:
        if CACHE_FILE.exists():
            return CACHE_FILE.read_text().strip()
    except Exception as e:
        logger.warning(f"读取缓存IPv6地址失败: {e}")
    return None

def save_cached_ipv6(ipv6):
    """保存IPv6地址到缓存"""
    try:
        CACHE_FILE.write_text(ipv6)
        logger.debug(f"IPv6地址已缓存: {ipv6}")
    except Exception as e:
        logger.warning(f"保存缓存IPv6地址失败: {e}")

def get_ipv6_from_service(service_url, timeout=10):
    """从指定服务获取IPv6地址"""
    try:
        # 根据配置决定是否跳过代理
        proxies = {} if SKIP_PROXY else None
        response = requests.get(service_url, timeout=timeout, proxies=proxies)
        response.raise_for_status()
        
        # 处理不同服务的响应格式
        if 'json' in service_url:
            data = response.json()
            ipv6 = data.get('ip', '').strip()
        else:
            ipv6 = response.text.strip()
        
        # 验证IPv6地址格式
        if is_valid_ipv6(ipv6):
            return ipv6
        else:
            logger.warning(f"从 {service_url} 获取的不是有效的IPv6地址: {ipv6}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.warning(f"从 {service_url} 获取IPv6地址失败: {e}")
        return None
    except Exception as e:
        logger.warning(f"处理 {service_url} 响应时出错: {e}")
        return None

def is_valid_ipv6(ip):
    """验证IPv6地址格式"""
    try:
        socket.inet_pton(socket.AF_INET6, ip)
        # 排除本地回环和链路本地地址
        return not (ip.startswith('::1') or ip.startswith('fe80:') or ip.startswith('fc00:') or ip.startswith('fd00:'))
    except socket.error:
        return False

def get_ipv6():
    """获取本机的公网IPv6地址"""
    logger.info("开始获取IPv6地址...")
    
    # 尝试从多个服务获取IPv6地址
    for service_url in IPV6_SERVICES:
        logger.debug(f"尝试从 {service_url} 获取IPv6地址")
        ipv6 = get_ipv6_from_service(service_url)
        if ipv6:
            logger.info(f"成功从 {service_url} 获取IPv6地址: {ipv6}")
            return ipv6
    
    # 如果所有外部服务都失败，尝试本地方法作为备选
    logger.warning("所有外部IPv6服务都不可用，尝试本地方法...")
    return get_local_ipv6()

def get_local_ipv6():
    """获取本地IPv6地址（备选方法）"""
    try:
        # 获取所有网络接口
        interfaces = socket.getaddrinfo(socket.gethostname(), None)
        
        # 遍历所有接口，查找IPv6地址
        for interface in interfaces:
            if interface[0] == socket.AF_INET6:
                ipv6 = interface[4][0]
                if is_valid_ipv6(ipv6):
                    logger.info(f"使用本地方法获取IPv6地址: {ipv6}")
                    return ipv6
                    
        logger.error("未找到有效的IPv6地址")
        return None
    except Exception as e:
        logger.error(f"获取本地IPv6地址失败: {e}")
        return None

def retry_on_failure(func, max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """重试装饰器"""
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"第 {attempt + 1} 次尝试失败: {e}，{delay}秒后重试...")
                time.sleep(delay)
        return None
    return wrapper

@retry_on_failure
def get_record_id(client, domain_name, rr):
    """获取域名解析记录的ID"""
    logger.info(f"查询域名记录: {rr}.{domain_name}")
    
    request = DescribeDomainRecordsRequest()
    request.set_accept_format('json')
    request.set_DomainName(domain_name)
    request.set_RRKeyWord(rr)
    request.set_Type('AAAA')  # 只查询IPv6记录

    response = client.do_action_with_exception(request)
    response_json = json.loads(response.decode('utf-8'))
    
    if 'DomainRecords' in response_json and 'Record' in response_json['DomainRecords']:
        records = response_json['DomainRecords']['Record']
        for record in records:
            if record['RR'] == rr and record['Type'] == 'AAAA':
                logger.info(f"找到域名记录，RecordId: {record['RecordId']}")
                return record['RecordId']
    
    logger.error(f"未找到域名 {rr}.{domain_name} 的AAAA记录")
    return None

@retry_on_failure
def update_dns_record(client, record_id, ipv6):
    """更新阿里云DNS记录"""
    logger.info(f"更新DNS记录: {RR}.{DOMAIN_NAME} -> {ipv6}")
    
    # 创建API请求并设置参数
    request = UpdateDomainRecordRequest()
    request.set_accept_format('json')
    
    # 必需参数
    request.set_RecordId(record_id)
    request.set_RR(RR)
    request.set_Type('AAAA')  # IPv6记录类型
    request.set_Value(ipv6)
    
    # 可选参数
    request.set_TTL(TTL)  # 设置TTL
    request.set_Line(LINE)  # 设置解析线路
    request.set_Lang(LANG)  # 设置语言

    logger.debug(f"请求参数: {request._params}")
    
    # 发起API请求
    response = client.do_action_with_exception(request)
    response_json = json.loads(response.decode('utf-8'))
    
    if response_json.get('RequestId'):
        logger.info(f"DNS更新成功！RequestId: {response_json['RequestId']}")
        return True
    else:
        logger.error("DNS更新失败：未收到有效的响应")
        return False

def verify_dns_update(domain, expected_ipv6, timeout=30):
    """验证DNS更新是否生效"""
    logger.info(f"验证DNS更新: {domain}")
    
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # 查询DNS记录
            result = socket.getaddrinfo(domain, None, socket.AF_INET6)
            for addr_info in result:
                if addr_info[4][0] == expected_ipv6:
                    logger.info(f"DNS更新验证成功: {domain} -> {expected_ipv6}")
                    return True
        except socket.gaierror:
            pass
        
        time.sleep(5)  # 等待5秒后重试
    
    logger.warning(f"DNS更新验证超时: {domain}")
    return False

def main():
    """主函数"""
    try:
        logger.info("=== DNS更新脚本开始运行 ===")
        
        # 验证配置
        validate_config()
        
        # 创建AcsClient实例
        client = AcsClient(ACCESS_KEY_ID, ACCESS_KEY_SECRET, REGION)
        logger.info(f"已连接到阿里云区域: {REGION}")

        # 获取当前IPv6地址
        current_ipv6 = get_ipv6()
        if not current_ipv6:
            logger.error("无法获取IPv6地址，脚本退出")
            return False

        # 检查IPv6地址是否有变化
        cached_ipv6 = get_cached_ipv6()
        if cached_ipv6 == current_ipv6:
            logger.info(f"IPv6地址未发生变化: {current_ipv6}，跳过DNS更新")
            return True

        logger.info(f"检测到IPv6地址变化: {cached_ipv6} -> {current_ipv6}")

        # 获取记录ID
        record_id = get_record_id(client, DOMAIN_NAME, RR)
        if not record_id:
            logger.error("无法获取记录ID，请检查域名和RR配置是否正确")
            return False

        logger.info(f"配置信息 - 域名: {RR}.{DOMAIN_NAME}, TTL: {TTL}秒, 解析线路: {LINE}")
        
        # 更新DNS记录
        if update_dns_record(client, record_id, current_ipv6):
            # 保存新的IPv6地址到缓存
            save_cached_ipv6(current_ipv6)
            
            # 验证DNS更新（可选）
            full_domain = f"{RR}.{DOMAIN_NAME}"
            if os.getenv('VERIFY_DNS_UPDATE', 'false').lower() == 'true':
                verify_dns_update(full_domain, current_ipv6)
            
            logger.info("=== DNS更新脚本执行成功 ===")
            return True
        else:
            logger.error("DNS更新失败")
            return False
            
    except Exception as e:
        logger.error(f"脚本执行出错: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    main()