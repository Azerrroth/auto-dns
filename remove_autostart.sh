#!/bin/bash

# IPv6 DNS自动更新脚本 - Linux/macOS自动启动移除
# 支持systemd (Linux) 和 launchd (macOS)

set -e

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

# 移除Linux systemd服务
remove_linux_systemd() {
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    TIMER_FILE="/etc/systemd/system/${SERVICE_NAME}.timer"
    
    echo "移除systemd服务..."
    
    # 停止并禁用服务
    if sudo systemctl is-active --quiet "${SERVICE_NAME}.timer"; then
        sudo systemctl stop "${SERVICE_NAME}.timer"
    fi
    
    if sudo systemctl is-enabled --quiet "${SERVICE_NAME}.timer"; then
        sudo systemctl disable "${SERVICE_NAME}.timer"
    fi
    
    # 删除服务文件
    if [[ -f "$SERVICE_FILE" ]]; then
        sudo rm "$SERVICE_FILE"
        echo "已删除服务文件: $SERVICE_FILE"
    fi
    
    if [[ -f "$TIMER_FILE" ]]; then
        sudo rm "$TIMER_FILE"
        echo "已删除定时器文件: $TIMER_FILE"
    fi
    
    # 重新加载systemd
    sudo systemctl daemon-reload
    
    echo "systemd服务移除完成！"
}

# 移除macOS launchd服务
remove_macos_launchd() {
    PLIST_FILE="$HOME/Library/LaunchAgents/com.${SERVICE_NAME}.plist"
    
    echo "移除launchd服务..."
    
    # 卸载服务
    if launchctl list | grep -q "${SERVICE_NAME}"; then
        launchctl unload "$PLIST_FILE" 2>/dev/null || true
        echo "已卸载launchd服务"
    fi
    
    # 删除plist文件
    if [[ -f "$PLIST_FILE" ]]; then
        rm "$PLIST_FILE"
        echo "已删除配置文件: $PLIST_FILE"
    fi
    
    echo "launchd服务移除完成！"
}

# 主函数
main() {
    echo "=== IPv6 DNS自动更新脚本 - 移除自动启动 ==="
    
    OS=$(detect_os)
    echo "检测到操作系统: $OS"
    
    if [[ "$OS" == "unsupported" ]]; then
        echo "错误: 不支持的操作系统"
        exit 1
    fi
    
    case "$OS" in
        "linux")
            remove_linux_systemd
            ;;
        "macos")
            remove_macos_launchd
            ;;
    esac
    
    echo ""
    echo "自动启动移除完成！"
    
    # 手动移除说明
    echo ""
    echo "如果上述自动移除失败，您也可以手动移除："
    if [[ "$OS" == "linux" ]]; then
        echo "Linux (systemd):"
        echo "  sudo systemctl stop ${SERVICE_NAME}.timer"
        echo "  sudo systemctl disable ${SERVICE_NAME}.timer"
        echo "  sudo rm /etc/systemd/system/${SERVICE_NAME}.service"
        echo "  sudo rm /etc/systemd/system/${SERVICE_NAME}.timer"
        echo "  sudo systemctl daemon-reload"
    elif [[ "$OS" == "macos" ]]; then
        echo "macOS (launchd):"
        echo "  launchctl unload ~/Library/LaunchAgents/com.${SERVICE_NAME}.plist"
        echo "  rm ~/Library/LaunchAgents/com.${SERVICE_NAME}.plist"
    fi
}

# 运行主函数
main "$@"