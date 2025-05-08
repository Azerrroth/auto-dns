# IPv6 DNS 自动更新脚本

这个脚本用于自动获取本机的IPv6地址，并通过阿里云DNS API更新域名解析记录。

## 环境要求

- Python 3.x
- Conda 环境（使用 daily 环境）
- 已安装的依赖包（见 requirements.txt）

## 功能特点

- 自动获取本机公网IPv6地址
- 使用阿里云DNS API更新域名解析
- 自动查询域名解析记录ID
- 支持环境变量配置
- 错误处理和日志输出
- 支持自定义TTL和解析线路
- 支持开机自动运行

## 安装依赖

1. 确保已激活 daily 环境：
```bash
conda activate daily
```

2. 安装依赖包：
```bash
pip install -r requirements.txt
```

## 配置说明

1. 复制环境变量示例文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入以下信息：

必需参数：
- `ALIYUN_ACCESS_KEY_ID`: 阿里云访问密钥ID
- `ALIYUN_ACCESS_KEY_SECRET`: 阿里云访问密钥密码
- `DOMAIN_NAME`: 你的域名（例如：example.com）
- `RR`: 子域名（例如：www）

可选参数：
- `TTL`: 解析生效时间，单位为秒，默认为600秒（10分钟）
- `LINE`: 解析线路，默认为default
- `LANG`: 请求和接收消息的语言类型，默认为zh

## 使用方法

### 手动运行
1. 激活 conda 环境：
```bash
conda activate daily
```

2. 运行脚本：
```bash
python update_dns.py
```

### 设置开机自启动（Windows）

1. 确保已安装并配置好 Conda
2. 以管理员身份运行 PowerShell
3. 执行以下命令：
```powershell
Set-ExecutionPolicy RemoteSigned -Scope Process
.\setup_autostart.ps1
```

这将创建一个名为 "UpdateDNSIPv6" 的计划任务，在系统启动时自动运行脚本。脚本会自动使用 conda daily 环境。

### 取消开机自启动

方法一：使用脚本（推荐）
1. 以管理员身份运行 PowerShell
2. 执行以下命令：
```powershell
Set-ExecutionPolicy RemoteSigned -Scope Process
.\remove_autostart.ps1
```

方法二：手动删除
1. 按 Win + R，输入 `taskschd.msc` 打开任务计划程序
2. 在左侧面板中展开"任务计划程序库"
3. 找到名为 "UpdateDNSIPv6" 的任务
4. 右键点击任务，选择"删除"

### 设置定时任务

#### Windows
使用任务计划程序创建一个定时任务，定期运行此脚本。

#### Linux
使用crontab添加定时任务，例如每小时运行一次：
```bash
0 * * * * /path/to/conda/envs/daily/bin/python /path/to/update_dns.py
```

## 注意事项

1. 确保你的网络支持IPv6
2. 确保阿里云访问密钥具有DNS管理权限
3. 建议将脚本设置为定时运行，以保持DNS记录的及时更新
4. TTL值建议不要设置过小，以免影响DNS解析性能
5. 解析线路(LINE)参数需要根据你的实际需求设置，常见值包括：
   - default: 默认线路
   - telecom: 电信线路
   - unicom: 联通线路
   - mobile: 移动线路
   - oversea: 海外线路
6. 如果开机自启动任务无法运行，请检查：
   - Conda 是否正确安装并添加到系统环境变量
   - daily 环境是否存在并包含所需依赖
   - 是否以管理员权限运行设置脚本
   - 计划任务是否在任务计划程序中正确创建
7. 如果脚本无法找到域名解析记录，请检查：
   - 域名是否正确配置
   - 是否已创建AAAA类型的解析记录
   - 子域名(RR)是否正确 