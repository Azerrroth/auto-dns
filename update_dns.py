 #!/usr/bin/env python3
import os
import json
import socket
import logging
import requests
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

def get_record_id(client, domain_name, rr):
    """获取域名解析记录的ID"""
    try:
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
                    return record['RecordId']
        
        logging.warning(f"未找到域名 {rr}.{domain_name} 的AAAA记录")
        return None
    except (ClientException, ServerException) as e:
        logging.error(f"查询域名记录失败: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"解析响应失败: {e}")
        return None

def get_ipv6():
    """获取本机的IPv6地址"""
    # 首先尝试从 api6.ipify.org 获取 IPv6 地址
    try:
        logging.info("尝试从 https://api6.ipify.org 获取 IPv6 地址...")
        response = requests.get('https://api6.ipify.org', timeout=5)
        response.raise_for_status()  # 如果请求失败则引发 HTTPError 异常
        ipv6_address = response.text.strip()
        # 简单验证是否是有效的 IPv6 地址 (可以根据需要添加更严格的验证)
        if ':' in ipv6_address and '.' not in ipv6_address: # 基本的IPv6格式检查
            logging.info(f"通过 API 获取到 IPv6 地址: {ipv6_address}")
            return ipv6_address
        else:
            logging.warning(f"从 API 获取到的内容不是有效的 IPv6 地址: {ipv6_address}")
    except requests.exceptions.RequestException as e:
        logging.error(f"通过 API 获取 IPv6 地址失败: {e}")
    except Exception as e:
        logging.error(f"处理 API 响应时发生未知错误: {e}")

    # 如果 API 调用失败或未返回有效 IPv6 地址，则回退到本地接口方法
    logging.info("API 调用失败或未返回有效 IPv6, 尝试从本地网络接口获取...")
    try:
        # 获取所有网络接口
        interfaces = socket.getaddrinfo(socket.gethostname(), None)
        
        # 遍历所有接口，查找IPv6地址
        for interface in interfaces:
            # interface[0] 是地址族，AF_INET6 表示 IPv6
            if interface[0] == socket.AF_INET6:
                ipv6 = interface[4][0]
                # 过滤掉本地回环地址和链路本地地址
                if not ipv6.startswith('::1') and not ipv6.startswith('fe80:'):
                    logging.info(f"通过本地接口获取到 IPv6 地址: {ipv6}")
                    return ipv6
                    
        logging.warning("本地接口未找到有效的IPv6地址")
        return None
    except Exception as e:
        logging.error(f"通过本地接口获取IPv6地址失败: {e}")
        return None

def update_dns_record(client, record_id, ipv6):
    """更新阿里云DNS记录"""
    try:
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

        logging.debug(f"请求参数: {request._params}")
        
        # 发起API请求
        response = client.do_action_with_exception(request)
        response_json = json.loads(response.decode('utf-8'))
        
        if response_json.get('RequestId'):
            logging.info(f"DNS更新成功！ RequestId: {response_json['RequestId']}, RecordId: {response_json['RecordId']}")
            return True
        else:
            logging.error("DNS更新失败：未收到有效的响应")
            return False
            
    except (ClientException, ServerException) as e:
        logging.error(f"更新DNS记录失败: {e}")
        return False
    except json.JSONDecodeError as e:
        logging.error(f"解析响应失败: {e}")
        return False

def main():
    # 配置日志记录
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 创建一个 Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # 创建一个 FileHandler，用于写入日志文件
    file_handler = logging.FileHandler('update_dns.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 创建一个 StreamHandler，用于输出到控制台
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # 检查必要的环境变量
    required_vars = ['ALIYUN_ACCESS_KEY_ID', 'ALIYUN_ACCESS_KEY_SECRET', 'DOMAIN_NAME', 'RR']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logging.error(f"缺少必要的环境变量: {', '.join(missing_vars)}")
        return

    # 创建AcsClient实例
    client = AcsClient(ACCESS_KEY_ID, ACCESS_KEY_SECRET, 'cn-hangzhou')

    # 获取记录ID
    record_id = get_record_id(client, DOMAIN_NAME, RR)
    if not record_id:
        logging.error("无法获取记录ID，请检查域名和RR配置是否正确")
        return

    # 获取IPv6地址
    ipv6 = get_ipv6()
    if not ipv6:
        logging.error("无法获取IPv6地址")
        return

    logging.info(f"当前IPv6地址: {ipv6}")
    logging.info(f"TTL: {TTL}秒")
    logging.info(f"解析线路: {LINE}")
    
    # 更新DNS记录
    update_dns_record(client, record_id, ipv6)

if __name__ == "__main__":
    main()