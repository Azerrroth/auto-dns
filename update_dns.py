 #!/usr/bin/env python3
import os
import json
import socket
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
        
        print(f"未找到域名 {rr}.{domain_name} 的AAAA记录")
        return None
    except (ClientException, ServerException) as e:
        print(f"查询域名记录失败: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"解析响应失败: {e}")
        return None

def get_ipv6():
    """获取本机的IPv6地址"""
    try:
        # 获取所有网络接口
        interfaces = socket.getaddrinfo(socket.gethostname(), None)
        
        # 遍历所有接口，查找IPv6地址
        for interface in interfaces:
            # interface[0] 是地址族，10 表示 IPv6
            if interface[0] == socket.AF_INET6:
                ipv6 = interface[4][0]
                # 过滤掉本地回环地址和链路本地地址
                if not ipv6.startswith('::1') and not ipv6.startswith('fe80:'):
                    return ipv6
                    
        print("未找到有效的IPv6地址")
        return None
    except Exception as e:
        print(f"获取IPv6地址失败: {e}")
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

        print("请求参数:", request._params)
        
        # 发起API请求
        response = client.do_action_with_exception(request)
        response_json = json.loads(response.decode('utf-8'))
        
        if response_json.get('RequestId'):
            print(f"DNS更新成功！")
            print(f"RequestId: {response_json['RequestId']}")
            print(f"RecordId: {response_json['RecordId']}")
            return True
        else:
            print("DNS更新失败：未收到有效的响应")
            return False
            
    except (ClientException, ServerException) as e:
        print(f"更新DNS记录失败: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"解析响应失败: {e}")
        return False

def main():
    # 检查必要的环境变量
    required_vars = ['ALIYUN_ACCESS_KEY_ID', 'ALIYUN_ACCESS_KEY_SECRET', 'DOMAIN_NAME', 'RR']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"缺少必要的环境变量: {', '.join(missing_vars)}")
        return

    # 创建AcsClient实例
    client = AcsClient(ACCESS_KEY_ID, ACCESS_KEY_SECRET, 'cn-hangzhou')

    # 获取记录ID
    record_id = get_record_id(client, DOMAIN_NAME, RR)
    if not record_id:
        print("无法获取记录ID，请检查域名和RR配置是否正确")
        return

    # 获取IPv6地址
    ipv6 = get_ipv6()
    if not ipv6:
        print("无法获取IPv6地址")
        return

    print(f"当前IPv6地址: {ipv6}")
    print(f"TTL: {TTL}秒")
    print(f"解析线路: {LINE}")
    
    # 更新DNS记录
    update_dns_record(client, record_id, ipv6)

if __name__ == "__main__":
    main()