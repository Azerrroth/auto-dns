#!/usr/bin/env python3
"""
DNS更新脚本的单元测试
"""

import unittest
import socket
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# 导入要测试的模块
import update_dns

class TestIPv6Functions(unittest.TestCase):
    """测试IPv6相关功能"""
    
    def test_is_valid_ipv6(self):
        """测试IPv6地址验证"""
        # 有效的IPv6地址
        valid_ipv6s = [
            '2001:db8::1',
            '2001:0db8:85a3:0000:0000:8a2e:0370:7334',
            '2001:db8:85a3::8a2e:370:7334',
            'fe80::1%lo0',  # 这个会被过滤掉，但格式是有效的
        ]
        
        # 无效的IPv6地址
        invalid_ipv6s = [
            '192.168.1.1',  # IPv4
            'invalid',
            '2001:db8::g1',  # 包含无效字符
            '',
            None,
        ]
        
        for ipv6 in valid_ipv6s:
            if not ipv6.startswith('fe80:'):  # 排除链路本地地址
                self.assertTrue(update_dns.is_valid_ipv6(ipv6), f"{ipv6} should be valid")
        
        for ipv6 in invalid_ipv6s:
            if ipv6 is not None:
                self.assertFalse(update_dns.is_valid_ipv6(ipv6), f"{ipv6} should be invalid")
    
    def test_is_valid_ipv6_filters_local_addresses(self):
        """测试IPv6地址验证过滤本地地址"""
        local_addresses = [
            '::1',  # 回环地址
            'fe80::1',  # 链路本地地址
            'fc00::1',  # 唯一本地地址
            'fd00::1',  # 唯一本地地址
        ]
        
        for addr in local_addresses:
            self.assertFalse(update_dns.is_valid_ipv6(addr), f"{addr} should be filtered out")

class TestConfigValidation(unittest.TestCase):
    """测试配置验证功能"""
    
    def setUp(self):
        """设置测试环境"""
        self.original_env = {}
        # 保存原始环境变量
        for key in ['ALIYUN_ACCESS_KEY_ID', 'ALIYUN_ACCESS_KEY_SECRET', 'DOMAIN_NAME', 'RR']:
            self.original_env[key] = os.environ.get(key)
    
    def tearDown(self):
        """清理测试环境"""
        # 恢复原始环境变量
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]
    
    @patch.dict(os.environ, {
        'ALIYUN_ACCESS_KEY_ID': 'test_key_id',
        'ALIYUN_ACCESS_KEY_SECRET': 'test_key_secret',
        'DOMAIN_NAME': 'example.com',
        'RR': 'www'
    })
    def test_validate_config_success(self):
        """测试配置验证成功"""
        # 重新加载模块以获取新的环境变量
        import importlib
        importlib.reload(update_dns)
        
        try:
            update_dns.validate_config()
        except ValueError:
            self.fail("validate_config() raised ValueError unexpectedly!")
    
    @patch.dict(os.environ, {}, clear=True)
    def test_validate_config_missing_vars(self):
        """测试缺少必需环境变量"""
        import importlib
        importlib.reload(update_dns)
        
        with self.assertRaises(ValueError):
            update_dns.validate_config()
    
    @patch.dict(os.environ, {
        'ALIYUN_ACCESS_KEY_ID': 'test_key_id',
        'ALIYUN_ACCESS_KEY_SECRET': 'test_key_secret',
        'DOMAIN_NAME': 'invalid..domain',  # 无效域名
        'RR': 'www'
    })
    def test_validate_config_invalid_domain(self):
        """测试无效域名"""
        import importlib
        importlib.reload(update_dns)
        
        with self.assertRaises(ValueError):
            update_dns.validate_config()

class TestCacheOperations(unittest.TestCase):
    """测试缓存操作"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_file = Path(self.temp_dir) / '.last_ipv6'
        
        # 模拟CACHE_FILE
        update_dns.CACHE_FILE = self.cache_file
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_get_cached_ipv6(self):
        """测试保存和获取缓存的IPv6地址"""
        test_ipv6 = '2001:db8::1'
        
        # 保存IPv6地址
        update_dns.save_cached_ipv6(test_ipv6)
        
        # 获取IPv6地址
        cached_ipv6 = update_dns.get_cached_ipv6()
        
        self.assertEqual(cached_ipv6, test_ipv6)
    
    def test_get_cached_ipv6_no_file(self):
        """测试获取不存在的缓存文件"""
        cached_ipv6 = update_dns.get_cached_ipv6()
        self.assertIsNone(cached_ipv6)

class TestRetryMechanism(unittest.TestCase):
    """测试重试机制"""
    
    def test_retry_on_failure_success_first_try(self):
        """测试第一次尝试就成功"""
        @update_dns.retry_on_failure
        def success_func():
            return "success"
        
        result = success_func()
        self.assertEqual(result, "success")
    
    def test_retry_on_failure_success_after_retries(self):
        """测试重试后成功"""
        call_count = 0
        
        @update_dns.retry_on_failure
        def retry_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = retry_func()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)
    
    def test_retry_on_failure_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        @update_dns.retry_on_failure
        def always_fail():
            raise Exception("Always fails")
        
        with self.assertRaises(Exception):
            always_fail()

class TestIPv6Services(unittest.TestCase):
    """测试IPv6服务获取"""
    
    @patch.dict(os.environ, {'SKIP_PROXY': 'false'}, clear=False)
    @patch('update_dns.requests.get')
    def test_get_ipv6_from_service_success(self, mock_get):
        """测试从服务成功获取IPv6"""
        # 重新加载模块以获取新的环境变量
        import importlib
        importlib.reload(update_dns)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '2001:db8::1'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = update_dns.get_ipv6_from_service('https://test.service')
        self.assertEqual(result, '2001:db8::1')
        
        # 验证默认情况下不跳过代理
        mock_get.assert_called_with('https://test.service', timeout=10, proxies=None)
    
    @patch('update_dns.requests.get')
    def test_get_ipv6_from_service_json_response(self, mock_get):
        """测试从JSON服务获取IPv6"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ip': '2001:db8::1'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = update_dns.get_ipv6_from_service('https://test.service?format=json')
        self.assertEqual(result, '2001:db8::1')
    
    @patch('update_dns.requests.get')
    def test_get_ipv6_from_service_failure(self, mock_get):
        """测试从服务获取IPv6失败"""
        mock_get.side_effect = Exception("Network error")
        
        result = update_dns.get_ipv6_from_service('https://test.service')
        self.assertIsNone(result)
    
    @patch.dict(os.environ, {'SKIP_PROXY': 'true'})
    @patch('update_dns.requests.get')
    def test_get_ipv6_from_service_skip_proxy(self, mock_get):
        """测试跳过代理获取IPv6"""
        # 重新加载模块以获取新的环境变量
        import importlib
        importlib.reload(update_dns)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '2001:db8::1'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = update_dns.get_ipv6_from_service('https://test.service')
        self.assertEqual(result, '2001:db8::1')
        
        # 验证跳过代理时传递空的proxies字典
        mock_get.assert_called_with('https://test.service', timeout=10, proxies={})

if __name__ == '__main__':
    # 设置日志级别以减少测试输出
    import logging
    logging.getLogger().setLevel(logging.CRITICAL)
    
    unittest.main(verbosity=2)