#!/bin/bash

# IPv6 DNS自动更新脚本 - Linux/macOS自动启动设置
# 支持systemd (Linux) 和 launchd (macOS)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="update_dns.py"
SERVICE_NAME="auto-dns-ipv6"

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unsupported"
    fi
}

# 检查Python环境
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "错误: 未找到Python解释器"
        exit 1
    fi
    
    echo "使用Python解释器: $(which $PYTHON_CMD)"
}

# 安装依赖
install_dependencies() {
    echo "安装Python依赖..."
    $PYTHON_CMD -m pip install -r "$SCRIPT_DIR/requirements.txt"
}

# 设置Linux systemd服务
setup_linux_systemd() {
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    TIMER_FILE="/etc/systemd/system/${SERVICE_NAME}.timer"
    
    echo "创建systemd服务文件..."
    
    # 创建服务文件
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=IPv6 DNS Auto Update Service
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$USER
WorkingDirectory=$SCRIPT_DIR
Environment=PATH=/usr/local/bin:/usr/bin:/bin
ExecStart=$PYTHON_CMD $SCRIPT_DIR/$SCRIPT_NAME
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # 创建定时器文件（每10分钟运行一次）
    sudo tee "$TIMER_FILE" > /dev/null <<EOF
[Unit]
Description=Run IPv6 DNS Auto Update Service every 10 minutes
Requires=${SERVICE_NAME}.service

[Timer]
OnBootSec=2min
OnUnitActiveSec=10min
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # 重新加载systemd并启用服务
    sudo systemctl daemon-reload
    sudo systemctl enable "${SERVICE_NAME}.timer"
    sudo systemctl start "${SERVICE_NAME}.timer"
    
    echo "systemd服务设置完成！"
    echo "服务状态: $(sudo systemctl is-active ${SERVICE_NAME}.timer)"
    echo "查看日志: sudo journalctl -u ${SERVICE_NAME}.service -f"
}

# 设置macOS launchd服务
setup_macos_launchd() {
    PLIST_FILE="$HOME/Library/LaunchAgents/com.${SERVICE_NAME}.plist"
    
    echo "创建launchd配置文件..."
    
    # 创建plist文件
    tee "$PLIST_FILE" > /dev/null <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.${SERVICE_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_CMD</string>
        <string>$SCRIPT_DIR/$SCRIPT_NAME</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    <key>StartInterval</key>
    <integer>600</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/logs/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/logs/launchd.error.log</string>
</dict>
</plist>
EOF

    # 创建日志目录
    mkdir -p "$SCRIPT_DIR/logs"
    
    # 加载服务
    launchctl load "$PLIST_FILE"
    
    echo "launchd服务设置完成！"
    echo "服务状态: $(launchctl list | grep ${SERVICE_NAME} || echo '未运行')"
    echo "查看日志: tail -f $SCRIPT_DIR/logs/launchd.log"
}

# 主函数
main() {
    echo "=== IPv6 DNS自动更新脚本 - 自动启动设置 ==="
    
    OS=$(detect_os)
    echo "检测到操作系统: $OS"
    
    if [[ "$OS" == "unsupported" ]]; then
        echo "错误: 不支持的操作系统"
        exit 1
    fi
    
    # 检查是否有管理员权限（Linux需要）
    if [[ "$OS" == "linux" ]] && [[ $EUID -eq 0 ]]; then
        echo "错误: 请不要使用root用户运行此脚本"
        echo "脚本会在需要时提示输入sudo密码"
        exit 1
    fi
    
    check_python
    install_dependencies
    
    case "$OS" in
        "linux")
            setup_linux_systemd
            ;;
        "macos")
            setup_macos_launchd
            ;;
    esac
    
    echo ""
    echo "自动启动设置完成！"
    echo "脚本将每10分钟运行一次，检查IPv6地址变化并更新DNS记录。"
}

# 运行主函数
main "$@"