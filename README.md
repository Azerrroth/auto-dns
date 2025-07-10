# IPv6 DNS 自动更新脚本

[![Tests](https://github.com/Azerrroth/auto-dns/actions/workflows/test.yml/badge.svg)](https://github.com/Azerrroth/auto-dns/actions/workflows/test.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

这个脚本用于自动获取本机的公网IPv6地址，并通过阿里云DNS API更新域名解析记录。特别适用于家庭宽带等动态IPv6环境。

## 🚀 功能特点

- **智能IPv6获取**: 通过多个外部服务获取真实公网IPv6地址，支持备用方案
- **变化检测**: 只在IPv6地址发生变化时才更新DNS，避免不必要的API调用
- **完善的日志系统**: 详细的运行日志，支持按月分割，便于问题排查
- **重试机制**: 网络请求失败时自动重试，提高成功率
- **配置验证**: 启动前验证所有配置项，及早发现问题
- **多平台支持**: 支持Windows、Linux、macOS自动启动
- **健康检查**: 可选的DNS更新验证功能
- **安全可靠**: 完善的错误处理和异常恢复机制

## 📋 环境要求

- Python 3.8+
- 网络支持IPv6
- 阿里云账号和DNS管理权限

## 🛠️ 安装和配置

### 1. 克隆仓库
```bash
git clone https://github.com/Azerrroth/auto-dns.git
cd auto-dns
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制环境变量示例文件：
```bash
cp .env.example .env
```

编辑 `.env` 文件，填入以下信息：

#### 必需参数
- `ALIYUN_ACCESS_KEY_ID`: 阿里云访问密钥ID
- `ALIYUN_ACCESS_KEY_SECRET`: 阿里云访问密钥密码
- `DOMAIN_NAME`: 你的域名（例如：example.com）
- `RR`: 子域名（例如：www）

#### 可选参数
- `TTL`: 解析生效时间，单位为秒，默认为600秒（10分钟）
- `LINE`: 解析线路，默认为default
- `LANG`: 请求和接收消息的语言类型，默认为zh
- `REGION`: 阿里云区域，默认为cn-hangzhou
- `MAX_RETRIES`: 最大重试次数，默认为3
- `RETRY_DELAY`: 重试延迟秒数，默认为5
- `VERIFY_DNS_UPDATE`: 是否验证DNS更新，默认为false

### 4. 验证配置
运行配置检查脚本：
```bash
python check_config.py
```

这个脚本会检查：
- 环境变量配置
- 网络连接
- 阿里云凭证
- DNS记录
- 文件权限

## 📖 使用方法

### 手动运行
```bash
python update_dns.py
```

### 自动启动设置

#### Windows
以管理员身份运行 PowerShell：
```powershell
Set-ExecutionPolicy RemoteSigned -Scope Process
.\setup_autostart.ps1
```

#### Linux/macOS
```bash
chmod +x setup_autostart.sh
./setup_autostart.sh
```

这将设置系统服务，每10分钟自动检查IPv6地址变化并更新DNS记录。

### 移除自动启动

#### Windows
```powershell
Set-ExecutionPolicy RemoteSigned -Scope Process
.\remove_autostart.ps1
```

#### Linux/macOS
```bash
chmod +x remove_autostart.sh
./remove_autostart.sh
```

## 🧪 测试

运行单元测试：
```bash
python -m pytest test_update_dns.py -v
```

运行配置检查：
```bash
python check_config.py
```

## ⚠️ 注意事项

1. **网络要求**: 确保你的网络支持IPv6并能获取到公网IPv6地址
2. **权限配置**: 确保阿里云访问密钥具有DNS管理权限
3. **DNS记录**: 需要先在阿里云DNS控制台创建一个AAAA类型的解析记录
4. **TTL设置**: TTL值建议不要设置过小（建议≥300秒），以免影响DNS解析性能
5. **解析线路**: 根据实际需求设置LINE参数：
   - `default`: 默认线路
   - `telecom`: 电信线路
   - `unicom`: 联通线路
   - `mobile`: 移动线路
   - `oversea`: 海外线路

## 🔧 故障排除

### 常见问题

#### 1. 无法获取IPv6地址
- 检查网络是否支持IPv6
- 尝试访问 https://test-ipv6.com/ 测试IPv6连通性
- 检查防火墙设置

#### 2. 阿里云API调用失败
- 验证访问密钥是否正确
- 检查密钥是否有DNS管理权限
- 确认域名是否在阿里云DNS中托管

#### 3. 找不到DNS记录
- 在阿里云DNS控制台创建AAAA记录
- 确认域名和子域名配置正确
- 检查记录状态是否为"正常"

#### 4. 自动启动不工作
**Windows:**
- 检查任务计划程序中是否有"UpdateDNSIPv6"任务
- 确认任务状态和触发器设置
- 查看任务历史记录

**Linux:**
- 检查systemd服务状态：`sudo systemctl status auto-dns-ipv6.timer`
- 查看服务日志：`sudo journalctl -u auto-dns-ipv6.service -f`

**macOS:**
- 检查launchd服务：`launchctl list | grep auto-dns`
- 查看日志文件：`tail -f logs/launchd.log`

### 日志查看

脚本会在 `logs/` 目录下生成详细的运行日志：
```bash
# 查看最新日志
tail -f logs/dns_update_$(date +%Y%m).log

# 查看所有日志文件
ls -la logs/
```

### 调试模式

设置环境变量启用详细日志：
```bash
export PYTHONPATH=.
python -c "import logging; logging.basicConfig(level=logging.DEBUG)" update_dns.py
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

1. Fork 这个仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 📄 许可证

这个项目使用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [阿里云DNS API](https://help.aliyun.com/product/29697.html)
- 各个IPv6检测服务提供商