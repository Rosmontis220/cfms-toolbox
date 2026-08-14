# CFMS工具箱

![GitHub License](https://img.shields.io/github/license/Rosmontis220/cfms-toolbox?link=https%3A%2F%2Fgithub.com%2FRosmontis220%2Fcfms-toolbox%2Fblob%2Fmaster%2FLICENSE)
![Python](https://img.shields.io/badge/Python-3.14+-blue.svg)
![GitHub Tag](https://img.shields.io/github/v/tag/Rosmontis220/cfms-toolbox?link=https%3A%2F%2Fgithub.com%2FRosmontis220%2Fcfms-toolbox%2Freleases)

通用版聊天数据工具箱：适配任意同类 CFMS 服务器，集下载、快速查看、生成网页于一体。

## 功能

- **下载**：连接 CFMS 服务器（WebSocket + AES-GCM 加密传输），扫描并增量下载文件；支持自动刷新、任务栏托盘通知
- **快速查看**：本地聊天记录气泡浏览，支持房间/用户重命名、可点击链接、附件打开
- **生成网页**：把下载的 `.runtime/chatbox` 数据生成微信风格 HTML 页面（生成模块已内置，无需外部文件），保存到程序目录并自动打开

## 运行要求

- Windows 10/11，Python 3.14+
- 安装依赖：`pip install -r requirements.txt`

## 使用

1. 运行：双击程序
2. 在「下载」页填写服务器地址、端口、用户名、密码，点击「连接并扫描」
3. 勾选需要的文件，点击「下载所选文件」
4. 下载完成后，「快速查看」页可直接浏览聊天室；「生成网页」页一键生成 HTML 并自动用浏览器打开

## 配置

- 所有设置保存在程序同目录的 `cfms_toolbox_config_regular.json`（单个 JSON 文件）
- 包含服务器设置、聊天数据路径、房间/用户改名、日期标签等，程序关闭时自动保存

## 打包为 exe

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "CFMS工具箱_v1.5.0" CFMS工具箱_v1.5.0.pyw
```

## 隐私说明

- 本版本（常规版）源码内不含任何服务器凭据或个人路径，首次使用全部手动设置
- 请勿将本机生成的 `cfms_toolbox_config_regular.json` 等配置文件随源码分发

## 许可证

本项目以 [Apache License 2.0](LICENSE) 开源发布。

开发过程中参考了以下开源项目：

- [cfms-dev/cfms_client_tauri](https://github.com/cfms-dev/cfms_client_tauri)（Apache License 2.0）
- [cfms-dev/cfms_on_websocket](https://github.com/cfms-dev/cfms_on_websocket)（仓库未附带许可证文件，仅作为协议实现参考）
