# CFMS工具箱

[![GitHub License](https://img.shields.io/github/license/Rosmontis220/cfms-toolbox)](https://github.com/Rosmontis220/cfms-toolbox/blob/master/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.14+-blue.svg)](https://github.com/Rosmontis220/cfms-toolbox)
[![GitHub Tag](https://img.shields.io/github/v/tag/Rosmontis220/cfms-toolbox)](https://github.com/Rosmontis220/cfms-toolbox/releases)

通用版聊天数据工具箱：适配任意同类 CFMS 服务器，集下载、聊天记录、网页查看于一体。

## 功能

- **下载**：连接 CFMS 服务器（WebSocket + AES-GCM 加密传输），扫描并增量下载文件；支持自动刷新、任务栏托盘通知；下载后区分本次下载的文件是新文件还是已修改文件
- **聊天记录**：本地聊天气泡浏览，支持房间/用户重命名、可点击链接、附件打开；自动检测聊天记录中混入的非格式文本，可在附件栏一键查看
- **网页查看**：点击「网页查看」直接在浏览器中打开聊天记录 WebUI，支持附件图片/音频预览、房间倒序展示；无需生成 HTML 文件
- **小工具**：矩阵生成（IP/端口编码为 7×7 谜题矩阵，含干扰数据、校验和与汉明码纠错行）、ASCII、A1Z26、进制转换、BASE 系列（BASE64/BASE58/BASE62/BASE85/BASE91）、摩斯电码、培根密码、凯撒密码、埃特巴什码、维吉尼亚密码（支持 Gronsfeld 数字密钥）、关键字密码、简单换位、ADFGVX 密码、编码转换、SHA-256 等；界面支持中文 / English / 日本語 切换

## 运行要求

- Windows 10/11，Python 3.14+
- 安装依赖：`pip install -r requirements.txt`

## 使用

1. 运行：双击程序
2. 在「下载文件」页填写服务器地址、端口、用户名、密码，点击「连接并扫描」
3. 勾选需要的文件，点击「下载所选文件」
4. 下载完成后，「聊天记录」页可直接浏览聊天室；点击「网页查看」用浏览器打开 WebUI；矩阵生成与各类加解密工具集中在「小工具」页

## 配置

- 所有设置保存在程序同目录的 `cfms_toolbox_config_regular.json`（单个 JSON 文件）
- 包含服务器设置、聊天数据路径、房间/用户改名、日期标签等，程序关闭时自动保存

## 打包为 exe

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "CFMS_Toolbox_v1.10.0" CFMS_Toolbox.pyw
```

## 隐私说明

- 本版本（常规版）源码内不含任何服务器凭据或个人路径，首次使用全部手动设置
- 请勿将本机生成的 `cfms_toolbox_config_regular.json` 等配置文件随源码分发

## 许可证

本项目以 [Apache License 2.0](LICENSE) 开源发布。

开发过程中参考了以下开源项目：

- [cfms-dev/cfms_client_tauri](https://github.com/cfms-dev/cfms_client_tauri)（Apache License 2.0）
- [cfms-dev/cfms_on_websocket](https://github.com/cfms-dev/cfms_on_websocket)（仓库未附带许可证文件，仅作为协议实现参考）
