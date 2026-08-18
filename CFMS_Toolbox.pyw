

from __future__ import annotations

import base64
import collections
import hashlib
import http.server
import io
import json
import os
import re
import secrets
import ssl
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
from datetime import datetime
from ipaddress import IPv4Address
from pathlib import Path
from random import Random
from typing import Sequence

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.simpledialog as simpledialog
from tkinter import filedialog, messagebox as mb

import websocket
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

try:
    import pystray
    from PIL import Image
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False


def _app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


APP_DIR = _app_dir()


APP_VERSION = "1.10.0"
VARIANT_NAME = ""            

SPECIAL = VARIANT_NAME == "遗闻特供版"
APP_TITLE = f"CFMS工具箱 v{APP_VERSION}"
if VARIANT_NAME:
    APP_TITLE += f" {VARIANT_NAME}"


LANG = "zh"

LANG_DISPLAY = {"中文": "zh", "English": "en", "日本語": "ja"}
LANG_NAMES = {v: k for k, v in LANG_DISPLAY.items()}

TRANSLATIONS = {
    "en": {
        "CFMS工具箱": "CFMS Toolbox",
        "下载": "Download",
        "下载文件": "Download Files",
        "小工具": "Tools",
        "参考仓库：": "Reference Repos: ",
        "服务端：": "Server: ",
        "客户端：": "Client: ",
        "QQ群：": "QQ Group: ",
        "生成网页": "Generate HTML",
        "加解密": "Encrypt/Decrypt",
        "显示窗口": "Show Window",
        "退出": "Quit",
        "程序已最小化到托盘，自动刷新仍在运行。": "Minimized to tray; auto-refresh is still running.",
        "地址：": "Address: ",
        "端口：": "Port: ",
        "用户名：": "Username: ",
        "密码：": "Password: ",
        "连接并扫描": "Connect & Scan",
        "全选": "Select All",
        "取消选择": "Deselect",
        "全选改动": "Select Changed",
        "筛选:": "Filter:",
        "全部": "All",
        "新文件": "New",
        "已修改": "Modified",
        "已下载": "Downloaded",
        "已下载（已修改）": "Downloaded (Modified)",
        "隐藏": "Hidden",
        "下载所选文件": "Download Selected",
        "取消": "Cancel",
        "输出：": "Output: ",
        "自定义文件夹": "Browse…",
        "自动刷新": "Auto Refresh",
        "间隔(分):": "Interval (min):",
        "文件名": "File",
        "状态": "Status",
        "就绪，请连接并扫描。": "Ready. Connect and scan.",
        "提示": "Notice",
        "请先选择要下载的文件": "Please select files to download first",
        "请先设置输出文件夹（点击「自定义文件夹」选择保存位置）。": "Please set the output folder first (click “Browse…” to choose).",
        "错误": "Error",
        "下载出错": "Download error",
        "预览: ": "Preview: ",
        "无法预览二进制文件:\n": "Cannot preview binary file:\n",
        "正在下载 {sp} 用于预览...": "Downloading {sp} for preview...",
        "就绪。": "Ready.",
        "正在连接...": "Connecting...",
        "正在扫描服务器...": "Scanning server...",
        "自动刷新中...": "Auto-refreshing...",
        "自动刷新扫描服务器...": "Auto-refresh scanning server...",
        "请先在顶部填写服务器地址和端口": "Please enter the server address and port at the top first",
        "请先填写用户名和密码": "Please enter username and password first",
        "正在扫描...": "Scanning...",
        "共找到 {n} 个文件": "Found {n} files",
        "扫描结束，共找到 {n} 个文件。蓝色-新文件，紫色-隐藏文件，红色-已修改文件": "Scan finished: {n} files. Blue=new, purple=hidden, red=modified",
        "自动刷新失败": "Auto-refresh failed",
        "自动刷新错误：": "Auto-refresh error: ",
        "扫描错误": "Scan error",
        "失败": "Failed",
        "正在下载 [{i}/{n}] {sp} ...": "Downloading [{i}/{n}] {sp} ...",
        "下载完成：{d} 个文件成功，{f} 个失败，跳过 {s} 个": "Done: {d} downloaded, {f} failed, {s} skipped",
        "正在取消...": "Cancelling...",
        "发现 {n} 个新文件 / {m} 个已修改": "Found {n} new / {m} modified",
        "扫描发现": "Scan found",
        "新增 {n} 个文件，{m} 个已修改。": "{n} new files, {m} modified.",
        "chatbox 文件夹路径:": "Chatbox folder path:",
        "选择文件夹": "Choose Folder",
        "刷新": "Refresh",
        "设置": "Settings",
        "帮助": "Help",
        "就绪": "Ready",
        "请选择 chatbox 文件夹": "Please choose the chatbox folder",
        "未选择文件夹": "No folder selected",
        "共 {n} 个聊天室": "{n} rooms",
        "附件:": "Attachments: ",
        "无附件": "No attachments",
        "非格式文本 ({n})": "Non-format text ({n})",
        "非格式文本": "Non-format Text",
        "当前聊天室没有检测到非格式文本。": "No non-format text detected in this room.",
        "暂无消息": "No messages",
        "文件夹": "Folder",
        "房间名": "Room Name",
        "用户名": "Username",
        "浏览…": "Browse…",
        "双击列表项可编辑房间名": "Double-click an item to edit the room name",
        "双击列表项可编辑用户名": "Double-click an item to edit the username",
        "重命名房间": "Rename Room",
        "重命名用户": "Rename User",
        "输入自定义房间名:": "Enter a custom room name:",
        "为 {uid}… 输入自定义名称:": "Enter a custom name for {uid}…:",
        "房间 {r}…\n输入自定义名称(留空恢复默认):": "Room {r}…\nEnter a custom name (blank resets):",
        "用户 {u}…\n输入自定义名称(留空恢复默认):": "User {u}…\nEnter a custom name (blank resets):",
        "确定": "OK",
        "链接": "Link",
        "打开链接": "Open Link",
        "复制链接": "Copy Link",
        "生成微信风格聊天记录网页": "Generate WeChat-style Chat HTML",
        "数据源为下载后的 .runtime/chatbox 文件夹，HTML 将保存到本程序所在目录并自动用浏览器打开。": "Source: the downloaded .runtime/chatbox folder. HTML is saved next to the program and opened automatically in your browser.",
        "聊天数据：": "Chat data: ",
        "⚙  生成 HTML 并自动打开": "⚙  Generate HTML & Open",
        "输出文件：": "Output file: ",
        "请选择 chatbox 文件夹（含各聊天室子文件夹）": "Choose the chatbox folder (containing room subfolders)",
        "聊天数据文件夹不存在：\n{path}\n\n": "Chat data folder not found:\n{path}\n\n",
        "请先在「下载」页下载数据，或点击「选择文件夹」手动指定。": "Download data on the Download tab first, or click “Choose Folder” to select it manually.",
        "未找到任何聊天数据（chatbox 目录为空或无消息）": "No chat data found (the chatbox folder is empty or has no messages)",
        "生成失败": "Generation failed",
        "✅ 已生成：": "✅ Generated: ",
        "共 {n} 个会话房间，{m} 条消息": "{n} rooms, {m} messages",
        "已用默认浏览器打开。": "Opened in the default browser.",
        "自动打开失败（可手动打开）：": "Auto-open failed (open it manually): ",
        "开始生成……": "Generating...",
        "进制转换": "Base Conversion",
        "摩斯电码": "Morse Code",
        "凯撒密码": "Caesar Cipher",
        "维吉尼亚密码": "Vigenère Cipher",
        "ADFGVX密码": "ADFGVX Cipher",
        "编码转换": "Encoding Conversion",
        "ASCII：字符与数字编码互相转换（支持 Unicode）。": "ASCII: convert between characters and numeric codes (Unicode supported).",
        "进制转换：2-36 进制互转（加密=源进制→目标进制，解密=反向）。": "Base conversion: convert between bases 2-36 (Encrypt=source→target, Decrypt=reverse).",
        "BASE64：文本与 BASE64 编码互相转换。": "BASE64: convert between text and BASE64.",
        "BASE：支持 BASE64 / BASE58 / BASE62 / BASE85 / BASE91 互转。": "BASE: supports BASE64 / BASE58 / BASE62 / BASE85 / BASE91 conversions.",
        "编码：": "Encoding: ",
        "不支持的编码：{e}": "Unsupported encoding: {e}",
        "解码失败，请检查输入内容和编码类型": "Decode failed; check the input and encoding type",
        "无效的 Base58 字符：{c}": "Invalid Base58 character: {c}",
        "无效的 Base62 字符：{c}": "Invalid Base62 character: {c}",
        "无效的 Base91 字符：{c}": "Invalid Base91 character: {c}",
        "摩斯电码：字母/数字/常用符号与摩斯码互相转换，单词间用 / 分隔。": "Morse code: letters/digits/common symbols; words are separated by /.",
        "凯撒密码：把字母按位移量循环平移（0-25）。": "Caesar cipher: shift letters by an offset (0-25).",
        "维吉尼亚密码：字母或数字密钥逐字符位移，纯数字密钥即为 Gronsfeld 密码。": "Vigenère cipher: shift each letter by a letter or digit key; an all-digit key uses Gronsfeld.",
        "ADFGVX 密码：密钥生成 6×6 方阵，KeySquare 做列置换，解密自动去除填充。": "ADFGVX cipher: a key builds the 6×6 grid, KeySquare drives columnar transposition; padding is removed automatically on decrypt.",
        "编码转换：按源编码取字节、再按目标编码显示（常用于乱码修复）。": "Encoding conversion: get bytes in the source encoding, display in the target encoding (handy for fixing mojibake).",
        "SHA-256：对输入文本计算 SHA-256 哈希（十六进制），不可逆。": "SHA-256: compute the SHA-256 hash (hex) of the input; irreversible.",
        "位移：": "Shift: ",
        "密钥：": "Key: ",
        "源进制：": "Source base: ",
        "目标进制：": "Target base: ",
        "源编码：": "Source encoding: ",
        "目标编码：": "Target encoding: ",
        "加密": "Encrypt",
        "解密": "Decrypt",
        "计算": "Compute",
        "复制结果": "Copy Result",
        "清空": "Clear",
        "位移必须是整数": "Shift must be an integer",
        "密钥必须包含字母或数字": "Key must contain letters or digits",
        "BASE64 解码失败，请检查输入内容": "BASE64 decode failed; check your input",
        "请输入密钥": "Please enter a key",
        "没有可解析的数字": "No parseable numbers",
        "无法解析的数字：{p}": "Unparseable number: {p}",
        "超出 Unicode 范围：{n}": "Out of Unicode range: {n}",
        "进制必须是整数": "Bases must be integers",
        "进制必须在 2-36 之间": "Bases must be between 2 and 36",
        "请输入数字": "Please enter a number",
        "无法按 {n} 进制解析输入": "Cannot parse the input as base {n}",
        "转换失败：{e}": "Conversion failed: {e}",
        "输入中没有任何可加密的字母或数字": "No encryptable letters or digits in the input",
        "请输入转置密钥": "Please enter the transposition key (KeySquare)",
        "密文长度不是 KeySquare 长度的整数倍（请检查 KeySquare）": "Ciphertext length is not a multiple of the KeySquare length (check KeySquare)",
        "操作失败：{e}": "Operation failed: {e}",
        "界面语言：": "Language: ",
        "应用": "Apply",
        "开发者：": "Developer: ",
        "切换语言后界面将自动重建，当前页签会保留。": "The UI rebuilds automatically after switching languages; the current tab is kept.",
        "培根密码": "Baconian Cipher",
        "埃特巴什码": "Atbash Cipher",
        "A1Z26": "A1Z26",
        "关键字密码": "Keyword Cipher",
        "简单换位": "Simple Substitution",
        "埃特巴什码：字母表反转（A↔Z）。": "Atbash: reverse the alphabet (A↔Z).",
        "A1Z26：字母与数字互转（A=1 … Z=26）。": "A1Z26: convert between letters and numbers (A=1 … Z=26).",
        "关键字密码：关键字生成替换字母表。": "Keyword cipher: a keyword builds the substitution alphabet.",
        "简单换位：输入 26 个不重复字母作为替换字母表。": "Simple substitution: enter 26 unique letters as the substitution alphabet.",
        "培根密码：字母转 5 位 A/B 编码（也接受 0/1）。": "Baconian: letters to 5-bit A/B codes (0/1 also accepted).",
        "替换字母表：": "Substitution alphabet: ",
        "数字必须在 1-26 之间：{n}": "Number must be between 1 and 26: {n}",
        "替换字母表必须恰好包含 26 个不重复字母": "The substitution alphabet must contain exactly 26 unique letters",
        "没有可解析的培根码": "No Baconian code to parse",
        "培根码长度必须是 5 的倍数": "Baconian input length must be a multiple of 5",
        "无效的培根码：{g}": "Invalid Baconian code: {g}",
        "矩阵生成": "Matrix Generator",
        "IP 地址：": "IP address: ",
        "修订：": "Revision: ",
        "干扰密钥：": "Decoy key: ",
        "生成矩阵": "Generate Matrix",
        "解码": "Decode",
        "转置": "Transpose",
        "已生成 7×7 矩阵。": "7×7 matrix generated.",
        "端点：": "Endpoint: ",
        "校验和：": "Checksum: ",
        "RBF：": "RBF: ",
        "不确定": "uncertain",
        "距离": "distance",
        "校验结果：有效": "Checksum: valid",
        "校验结果：无效": "Checksum: invalid",
        "矩阵每个格子必须填 0-9 的一位数字": "Each cell must contain a single digit 0-9",
        "把 IP 与端口编码为 7×7 谜题矩阵（含干扰数据），也可解码还原与转置。": "Encode an IP and port into a 7×7 puzzle matrix (with decoys); decode and transpose are also supported.",
        "网页查看": "Web View",
        "打开网页查看失败：{e}": "Failed to open Web View: {e}",
        "CFMS聊天记录": "CFMS Chat Log",
        "条消息": "messages",
        "最后：": "Last: ",
        "选择一个房间": "Select a room",
        "聊天记录": "Chat History",
        "附件": "Attachments",
    },
    "ja": {
        "CFMS工具箱": "CFMSツールボックス",
        "下载": "ダウンロード",
        "下载文件": "ファイルダウンロード",
        "小工具": "ツール",
        "参考仓库：": "参考リポジトリ：",
        "服务端：": "サーバー：",
        "客户端：": "クライアント：",
        "QQ群：": "QQグループ：",
        "生成网页": "HTML生成",
        "加解密": "暗号化・復号",
        "显示窗口": "ウィンドウ表示",
        "退出": "終了",
        "程序已最小化到托盘，自动刷新仍在运行。": "トレイに最小化しました。自動更新は継続中です。",
        "地址：": "アドレス：",
        "端口：": "ポート：",
        "用户名：": "ユーザー名：",
        "密码：": "パスワード：",
        "连接并扫描": "接続してスキャン",
        "全选": "全選択",
        "取消选择": "選択解除",
        "全选改动": "変更を選択",
        "筛选:": "フィルタ：",
        "全部": "すべて",
        "新文件": "新規",
        "已修改": "変更済み",
        "已下载": "DL済み",
        "已下载（已修改）": "DL済み（変更）",
        "隐藏": "非表示",
        "下载所选文件": "選択をDL",
        "取消": "キャンセル",
        "输出：": "出力：",
        "自定义文件夹": "参照…",
        "自动刷新": "自動更新",
        "间隔(分):": "間隔(分)：",
        "文件名": "ファイル名",
        "状态": "状態",
        "就绪，请连接并扫描。": "準備完了。接続してスキャンしてください。",
        "提示": "お知らせ",
        "请先选择要下载的文件": "ダウンロードするファイルを選択してください",
        "请先设置输出文件夹（点击「自定义文件夹」选择保存位置）。": "出力フォルダを先に設定してください（「参照…」で選択）。",
        "错误": "エラー",
        "下载出错": "ダウンロードエラー",
        "预览: ": "プレビュー：",
        "无法预览二进制文件:\n": "バイナリファイルをプレビューできません：\n",
        "正在下载 {sp} 用于预览...": "{sp} をプレビュー用にダウンロード中...",
        "就绪。": "準備完了。",
        "正在连接...": "接続中...",
        "正在扫描服务器...": "サーバーをスキャン中...",
        "自动刷新中...": "自動更新中...",
        "自动刷新扫描服务器...": "自動更新でサーバーをスキャン中...",
        "请先在顶部填写服务器地址和端口": "上部でサーバーアドレスとポートを入力してください",
        "请先填写用户名和密码": "ユーザー名とパスワードを入力してください",
        "正在扫描...": "スキャン中...",
        "共找到 {n} 个文件": "{n} 個のファイルが見つかりました",
        "扫描结束，共找到 {n} 个文件。蓝色-新文件，紫色-隐藏文件，红色-已修改文件": "スキャン完了：{n} 個。青=新規、紫=非表示、赤=変更",
        "自动刷新失败": "自動更新に失敗しました",
        "自动刷新错误：": "自動更新エラー：",
        "扫描错误": "スキャンエラー",
        "失败": "失敗",
        "正在下载 [{i}/{n}] {sp} ...": "[{i}/{n}] {sp} をダウンロード中 ...",
        "下载完成：{d} 个文件成功，{f} 个失败，跳过 {s} 个": "完了：{d} 成功、{f} 失敗、{s} スキップ",
        "正在取消...": "キャンセル中...",
        "发现 {n} 个新文件 / {m} 个已修改": "新規 {n} 個 / 変更 {m} 個",
        "扫描发现": "スキャン結果",
        "新增 {n} 个文件，{m} 个已修改。": "新規 {n} 個、変更 {m} 個。",
        "chatbox 文件夹路径:": "chatbox フォルダパス：",
        "选择文件夹": "フォルダ選択",
        "刷新": "更新",
        "设置": "設定",
        "帮助": "ヘルプ",
        "就绪": "準備完了",
        "请选择 chatbox 文件夹": "chatbox フォルダを選択してください",
        "未选择文件夹": "フォルダ未選択",
        "共 {n} 个聊天室": "{n} 部屋",
        "附件:": "添付：",
        "无附件": "添付なし",
        "非格式文本 ({n})": "非定型テキスト ({n})",
        "非格式文本": "非定型テキスト",
        "当前聊天室没有检测到非格式文本。": "この部屋に非定型テキストは検出されませんでした。",
        "暂无消息": "メッセージなし",
        "文件夹": "フォルダ",
        "房间名": "部屋名",
        "用户名": "ユーザー名",
        "浏览…": "参照…",
        "双击列表项可编辑房间名": "項目をダブルクリックで部屋名を編集",
        "双击列表项可编辑用户名": "項目をダブルクリックでユーザー名を編集",
        "重命名房间": "部屋名を変更",
        "重命名用户": "ユーザー名を変更",
        "输入自定义房间名:": "カスタム部屋名を入力：",
        "为 {uid}… 输入自定义名称:": "{uid}… のカスタム名を入力：",
        "房间 {r}…\n输入自定义名称(留空恢复默认):": "部屋 {r}…\nカスタム名を入力（空欄でリセット）：",
        "用户 {u}…\n输入自定义名称(留空恢复默认):": "ユーザー {u}…\nカスタム名を入力（空欄でリセット）：",
        "确定": "OK",
        "链接": "リンク",
        "打开链接": "リンクを開く",
        "复制链接": "リンクをコピー",
        "生成微信风格聊天记录网页": "微信風チャットHTMLを生成",
        "数据源为下载后的 .runtime/chatbox 文件夹，HTML 将保存到本程序所在目录并自动用浏览器打开。": "データ元：ダウンロード済み .runtime/chatbox フォルダ。HTMLはプログラムと同じ場所に保存され、ブラウザで自動的に開きます。",
        "聊天数据：": "チャットデータ：",
        "⚙  生成 HTML 并自动打开": "⚙  HTML生成して開く",
        "输出文件：": "出力ファイル：",
        "请选择 chatbox 文件夹（含各聊天室子文件夹）": "chatbox フォルダ（各ルームのサブフォルダを含む）を選択",
        "聊天数据文件夹不存在：\n{path}\n\n": "チャットデータフォルダが見つかりません：\n{path}\n\n",
        "请先在「下载」页下载数据，或点击「选择文件夹」手动指定。": "「ダウンロード」タブでデータを取得するか、「フォルダ選択」で手動指定してください。",
        "未找到任何聊天数据（chatbox 目录为空或无消息）": "チャットデータが見つかりません（chatbox フォルダが空かメッセージなし）",
        "生成失败": "生成に失敗しました",
        "✅ 已生成：": "✅ 生成：",
        "共 {n} 个会话房间，{m} 条消息": "{n} 部屋、{m} メッセージ",
        "已用默认浏览器打开。": "デフォルトブラウザで開きました。",
        "自动打开失败（可手动打开）：": "自動オープン失敗（手動で開いてください）：",
        "开始生成……": "生成中...",
        "进制转换": "進数変換",
        "摩斯电码": "モールス信号",
        "凯撒密码": "シーザー暗号",
        "维吉尼亚密码": "ヴィジュネル暗号",
        "ADFGVX密码": "ADFGVX暗号",
        "编码转换": "文字コード変換",
        "ASCII：字符与数字编码互相转换（支持 Unicode）。": "ASCII：文字と数値コードを相互変換（Unicode対応）。",
        "进制转换：2-36 进制互转（加密=源进制→目标进制，解密=反向）。": "進数変換：2〜36進数を相互変換（暗号化=元→先、復号=逆方向）。",
        "BASE64：文本与 BASE64 编码互相转换。": "BASE64：テキストとBASE64を相互変換。",
        "BASE：支持 BASE64 / BASE58 / BASE62 / BASE85 / BASE91 互转。": "BASE：BASE64/BASE58/BASE62/BASE85/BASE91に対応。",
        "编码：": "エンコード：",
        "不支持的编码：{e}": "未対応のエンコード：{e}",
        "解码失败，请检查输入内容和编码类型": "デコードに失敗しました。入力とエンコード種別を確認してください",
        "无效的 Base58 字符：{c}": "無効なBase58文字：{c}",
        "无效的 Base62 字符：{c}": "無効なBase62文字：{c}",
        "无效的 Base91 字符：{c}": "無効なBase91文字：{c}",
        "摩斯电码：字母/数字/常用符号与摩斯码互相转换，单词间用 / 分隔。": "モールス信号：英字/数字/記号と相互変換。単語間は / で区切ります。",
        "凯撒密码：把字母按位移量循环平移（0-25）。": "シーザー暗号：文字をシフト数で循環移動（0〜25）。",
        "维吉尼亚密码：字母或数字密钥逐字符位移，纯数字密钥即为 Gronsfeld 密码。": "ヴィジュネル暗号：文字または数字キーでずらす。数字のみのキーはグロンスフェルト暗号。",
        "ADFGVX 密码：密钥生成 6×6 方阵，KeySquare 做列置换，解密自动去除填充。": "ADFGVX暗号：キーで6×6方陣を生成、KeySquareで列転置。復号時はパディングを自動除去。",
        "编码转换：按源编码取字节、再按目标编码显示（常用于乱码修复）。": "文字コード変換：元コードでバイト化し、先コードで表示（文字化け修正に便利）。",
        "SHA-256：对输入文本计算 SHA-256 哈希（十六进制），不可逆。": "SHA-256：入力のSHA-256ハッシュ（16進数）を計算。不可逆。",
        "位移：": "シフト：",
        "密钥：": "キー：",
        "源进制：": "元の進数：",
        "目标进制：": "先の進数：",
        "源编码：": "元のコード：",
        "目标编码：": "先のコード：",
        "加密": "暗号化",
        "解密": "復号",
        "计算": "計算",
        "复制结果": "結果をコピー",
        "清空": "クリア",
        "位移必须是整数": "シフト数は整数にしてください",
        "密钥必须包含字母或数字": "キーに英字または数字を含めてください",
        "BASE64 解码失败，请检查输入内容": "BASE64の復号に失敗しました。入力を確認してください",
        "请输入密钥": "キーを入力してください",
        "没有可解析的数字": "解析できる数字がありません",
        "无法解析的数字：{p}": "解析できない数字：{p}",
        "超出 Unicode 范围：{n}": "Unicodeの範囲外：{n}",
        "进制必须是整数": "進数は整数にしてください",
        "进制必须在 2-36 之间": "進数は2〜36の範囲にしてください",
        "请输入数字": "数字を入力してください",
        "无法按 {n} 进制解析输入": "{n}進数として解析できません",
        "转换失败：{e}": "変換に失敗しました：{e}",
        "输入中没有任何可加密的字母或数字": "暗号化できる英字または数字がありません",
        "请输入转置密钥": "転置キー（KeySquare）を入力してください",
        "密文长度不是 KeySquare 长度的整数倍（请检查 KeySquare）": "暗号文の長さがKeySquare長の倍数ではありません（KeySquareを確認）",
        "操作失败：{e}": "操作に失敗しました：{e}",
        "界面语言：": "言語：",
        "应用": "適用",
        "开发者：": "開発者：",
        "切换语言后界面将自动重建，当前页签会保留。": "言語を切り替えるとUIが自動的に再構築され、現在のタブが保持されます。",
        "培根密码": "ベーコン暗号",
        "埃特巴什码": "アトバシュ暗号",
        "A1Z26": "A1Z26",
        "关键字密码": "キーワード暗号",
        "简单换位": "単純換字",
        "埃特巴什码：字母表反转（A↔Z）。": "アトバシュ暗号：アルファベットを反転（A↔Z）。",
        "A1Z26：字母与数字互转（A=1 … Z=26）。": "A1Z26：文字と数字を変換（A=1 … Z=26）。",
        "关键字密码：关键字生成替换字母表。": "キーワード暗号：キーワードで置換アルファベットを生成。",
        "简单换位：输入 26 个不重复字母作为替换字母表。": "単純換字：重複しない26文字を置換アルファベットとして入力。",
        "培根密码：字母转 5 位 A/B 编码（也接受 0/1）。": "ベーコン暗号：文字を5桁のA/Bコードに変換（0/1も可）。",
        "替换字母表：": "置換アルファベット：",
        "数字必须在 1-26 之间：{n}": "数字は1〜26の範囲にしてください：{n}",
        "替换字母表必须恰好包含 26 个不重复字母": "置換アルファベットは重複のない26文字が必要です",
        "没有可解析的培根码": "解析できるベーコンコードがありません",
        "培根码长度必须是 5 的倍数": "ベーコンコードの長さは5の倍数でなければなりません",
        "无效的培根码：{g}": "無効なベーコンコード：{g}",
        "矩阵生成": "行列生成",
        "IP 地址：": "IPアドレス：",
        "修订：": "リビジョン：",
        "干扰密钥：": "デコイキー：",
        "生成矩阵": "行列を生成",
        "解码": "デコード",
        "转置": "転置",
        "已生成 7×7 矩阵。": "7×7行列を生成しました。",
        "端点：": "エンドポイント：",
        "校验和：": "チェックサム：",
        "RBF：": "RBF：",
        "不确定": "不確定",
        "距离": "距離",
        "校验结果：有效": "チェックサム：有効",
        "校验结果：无效": "チェックサム：無効",
        "矩阵每个格子必须填 0-9 的一位数字": "各セルには0〜9の1桁の数字を入力してください",
        "把 IP 与端口编码为 7×7 谜题矩阵（含干扰数据），也可解码还原与转置。": "IPとポートを7×7パズル行列にエンコード（デコイ含む）。デコードと転置も可能。",
        "网页查看": "ウェブ表示",
        "打开网页查看失败：{e}": "Web表示を開けませんでした：{e}",
        "CFMS聊天记录": "CFMSチャットログ",
        "条消息": "件",
        "最后：": "最終：",
        "选择一个房间": "部屋を選択",
        "聊天记录": "チャット履歴",
        "附件": "添付",
    },
}


def set_lang(code: str) -> None:
    global LANG
    if code in LANG_NAMES:
        LANG = code


def tr(key: str) -> str:
    return TRANSLATIONS.get(LANG, {}).get(key, key)


CONFIG_PATH = APP_DIR / (
    "cfms_toolbox_config.json" if SPECIAL else "cfms_toolbox_config_regular.json"
)

DEFAULT_SETTINGS = {
    
    "host": "",
    "port": "",
    "username": "",
    "password": "",
    "output": "",
    "chatbox_path": "",
    "room_names": {},
    "user_names": {},
    "date_labels": {},
    "decoded_ids": {},
    "_legacy_viewer_migrated": 0,
    "html_title": "对话记录",
    "html_subtitle": "内部通讯",
    "auto_refresh": False,
    "interval": "5",
    "proxy_type": "",
    "proxy_host": "",
    "proxy_port": "",
    "language": "zh",
}

def load_config() -> dict:
    
    cfg = json.loads(json.dumps(DEFAULT_SETTINGS))
    if SPECIAL:
        cfg["output"] = str(APP_DIR / "cfms_downloads")
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text("utf-8"))
            if isinstance(data, dict):
                cfg.update({k: v for k, v in data.items() if k in cfg})
        except Exception:
            pass
    set_lang(str(cfg.get("language", "zh")))
    return cfg


def save_config(cfg: dict) -> None:
    try:
        CONFIG_PATH.write_text(
            json.dumps(cfg, indent=2, ensure_ascii=False), "utf-8"
        )
    except OSError:
        pass


ICON_B64 = "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"


_FALLBACK_ICON_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def _icon_bytes() -> bytes:
    b64 = ICON_B64.strip()
    if b64:
        try:
            return base64.b64decode(b64)
        except Exception:
            pass
    cand = APP_DIR / "favicon.ico"
    if cand.exists():
        try:
            return cand.read_bytes()
        except Exception:
            pass
    return base64.b64decode(_FALLBACK_ICON_B64)


FRAME_HEADER_LEN = 5
FRAME_PROCESS = 0x00
FRAME_CONCLUSION = 0x01

SEARCH_CHARS = ["."]


def encode_frame(fid: int, kind: int, payload: bytes) -> bytes:
    return struct.pack(">I", fid) + bytes([kind]) + payload


def decode_frame(data: bytes) -> tuple[int, int, bytes]:
    return struct.unpack(">I", data[:4])[0], data[4], data[FRAME_HEADER_LEN:]


class CFMSClient:
    def __init__(self, host: str, port: int,
                 proxy_type: str = "", proxy_host: str = "", proxy_port: int = 0):
        self.host = host
        self.port = port
        self.proxy_type = proxy_type
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.ws: websocket.WebSocket | None = None
        self.username: str | None = None
        self.password: str | None = None
        self.token: str | None = None
        self._next_sid = 1

    def connect(self):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kw: dict = {
            "url": f"wss://{self.host}:{self.port}",
            "sslopt": {"context": ctx}, "timeout": 15,
        }
        if self.proxy_type and self.proxy_host and self.proxy_port:
            kw["proxy_type"] = self.proxy_type
            kw["http_proxy_host"] = self.proxy_host
            kw["http_proxy_port"] = self.proxy_port
        self.ws = websocket.create_connection(**kw)

    def login(self, username: str, password: str) -> dict:
        r = self._rpc_raw(
            {"action": "login", "data": {"username": username, "password": password}}
        )
        if r.get("code") == 200:
            self.username = username
            self.password = password
            self.token = r["data"]["token"]
        return r

    def _ensure_connection(self):
        if self.ws is None or not self.ws.connected:
            self.connect()
            if self.username and self.password:
                self.login(self.username, self.password)

    def _rpc_raw(self, request: dict) -> dict:
        for attempt in range(2):
            try:
                self._ensure_connection()
                sid = self._next_sid
                self._next_sid += 2
                payload = json.dumps(request, ensure_ascii=False).encode()
                self.ws.send_binary(encode_frame(sid, FRAME_PROCESS, payload))
                chunks = []
                while True:
                    raw = self.ws.recv()
                    if isinstance(raw, bytes):
                        fid, kind, p = decode_frame(raw)
                        if fid == sid:
                            chunks.append(p)
                            if kind == FRAME_CONCLUSION:
                                break
                return json.loads(b"".join(chunks))
            except websocket.WebSocketConnectionClosedException:
                if attempt == 0:
                    self._ensure_connection()
                    continue
                else:
                    raise
            except Exception:
                raise
        raise RuntimeError("RPC 调用失败（重试后仍失败）")

    def rpc(self, action: str, data: dict) -> dict:
        return self._rpc_raw(
            {
                "action": action,
                "data": data,
                "username": self.username,
                "token": self.token,
                "timestamp": int(time.time()),
                "nonce": secrets.token_hex(16),
            }
        )

    def list_directory(self, folder_id: str | None) -> list[dict]:
        r = self.rpc("list_directory", {"folder_id": folder_id})
        if r.get("code") != 200:
            raise RuntimeError(r.get("message", str(r)))
        return r["data"].get("items", [])

    def download(self, document_id: str, progress_cb=None) -> bytes:
        for attempt in range(2):
            try:
                self._ensure_connection()
                r = self.rpc("get_document", {"document_id": document_id})
                if r.get("code") != 200:
                    raise RuntimeError(r.get("message", str(r)))
                task_id = r["data"]["task_data"]["task_id"]

                sid = self._next_sid
                self._next_sid += 2
                self.ws.send_binary(
                    encode_frame(
                        sid, FRAME_PROCESS,
                        json.dumps({
                            "action": "download_file",
                            "data": {"task_id": task_id, "offset": 0, "max_chunk_size": 65536},
                        }).encode(),
                    )
                )

                _, _, p = decode_frame(self.ws.recv())
                meta = json.loads(p)
                if meta.get("action") != "transfer_file":
                    raise RuntimeError(f"意外响应: {meta}")
                fs = meta["data"]["file_size"]
                tc = meta["data"]["total_chunks"]

                self.ws.send_binary(encode_frame(sid, FRAME_PROCESS, b"ready"))

                if fs == 0:
                    self.ws.recv()
                    self.ws.send_binary(encode_frame(sid, FRAME_PROCESS, b"complete"))
                    self.ws.recv()
                    return b""

                chunk_data = []
                total_rcv = 0
                for _ in range(tc):
                    _, _, p = decode_frame(self.ws.recv())
                    cm = json.loads(p)
                    prefix = base64.b64decode(cm["data"]["prefix"] or "")
                    tag = base64.b64decode(cm["data"]["tag"] or "")
                    ct = base64.b64decode(cm["data"]["chunk"])
                    chunk_data.append((cm["data"]["index"], prefix, tag, ct))
                    total_rcv += len(ct)
                    if progress_cb:
                        progress_cb(total_rcv, fs)

                _, _, p = decode_frame(self.ws.recv())
                aes_key = base64.b64decode(json.loads(p)["data"]["key"])

                plaintext = bytearray()
                total_dec = 0
                for idx, prefix, tag, ct in chunk_data:
                    nonce = (prefix[:8] + struct.pack(">I", idx))[:12]
                    aesgcm = AESGCM(aes_key)
                    pt = aesgcm.decrypt(nonce, ct + tag, None)
                    plaintext.extend(pt)
                    total_dec += len(pt)
                    if progress_cb:
                        progress_cb(total_rcv + total_dec, fs + fs)

                self.ws.send_binary(encode_frame(sid, FRAME_PROCESS, b"complete"))
                self.ws.recv()
                return bytes(plaintext)

            except websocket.WebSocketConnectionClosedException:
                if attempt == 0:
                    self._ensure_connection()
                    continue
                else:
                    raise
            except Exception:
                raise
        raise RuntimeError("下载失败（重试后仍失败）")

    def close(self):
        if self.ws:
            self.ws.close()


def sanitize_path(path: str) -> str:
    path = re.sub(r'[<>:"|?*]', "_", path)
    return os.path.join(*(p for p in path.replace("\\", "/").split("/") if p))


def scan_server(client: CFMSClient) -> list[dict]:
    walked = []

    def walk(fid, prefix):
        try:
            items = client.list_directory(fid)
        except RuntimeError:
            return
        dirs = []
        for item in items:
            if item["type"] == "directory":
                dirs.append(item)
            elif item["type"] == "document":
                sp = f"{prefix}/{item['name']}" if prefix else item["name"]
                walked.append(
                    {
                        "path": sp,
                        "id": item["id"],
                        "sha": item.get("sha256", ""),
                        "size": item.get("size"),
                        "hidden": False,
                    }
                )
        for d in dirs:
            sub = f"{prefix}/{d['name']}" if prefix else d["name"]
            walk(d["id"], sub)

    walk(None, "")

    discovered = {}
    for ch in SEARCH_CHARS:
        cursor = None
        while True:
            data = {"query": ch}
            if cursor:
                data["cursor"] = cursor
            r = client.rpc("search", data)
            if r.get("code") != 200:
                break
            for item in r["data"].get("items", []):
                if item["id"] not in discovered:
                    discovered[item["id"]] = item
            if r["data"].get("has_more") and r["data"].get("next_cursor"):
                cursor = r["data"]["next_cursor"]
            else:
                break

    walked_ids = {f["id"] for f in walked}

    path_map = {}
    for item in client.list_directory(None):
        if item["type"] == "directory":
            path_map[item["id"]] = item["name"]
    q = collections.deque((iid, name) for iid, name in list(path_map.items()))
    while q:
        iid, prefix = q.popleft()
        try:
            for item in client.list_directory(iid):
                full = f"{prefix}/{item['name']}"
                if item["id"] not in path_map:
                    path_map[item["id"]] = full
                if item["type"] == "directory":
                    q.append((item["id"], full))
        except RuntimeError:
            pass

    for iid, item in discovered.items():
        if item["type"] == "document" and iid not in walked_ids:
            pid = item.get("parent_id", "")
            pname = path_map.get(pid, "")
            name = item.get("name", item.get("title", "?"))
            sp = f"{pname}/{name}" if pname else f"_hidden/{pid[:8]}_{name}"
            walked.append(
                {
                    "path": sp,
                    "id": iid,
                    "sha": item.get("sha256", ""),
                    "size": item.get("size"),
                    "hidden": True,
                }
            )

    walked.sort(key=lambda f: f["path"])
    return walked


class DownloadPanel:
    

    def __init__(self, parent, toolbox):
        self.toolbox = toolbox
        self.cfg = toolbox.cfg
        self.frame = ttk.Frame(parent)
        self.top = self.frame.winfo_toplevel()

        out = str(self.cfg.get("output") or "")
        self.output_dir: Path = Path(out) if out else APP_DIR / "cfms_downloads"

        self.client: CFMSClient | None = None
        self.files: list[dict] = []
        self.manifest: dict[str, str] = {}
        self.session_downloaded_kinds: dict[str, str] = {}
        self.scanning = False
        self.downloading = False
        self.cancel_download = False
        self._auto_scan = False
        self._refresh_timer_id: str | None = None
        self.all_tree_items = []
        self._proxy_type = ""
        self._proxy_host = ""
        self._proxy_port = ""

        self._build_ui()
        self._load_settings()
        self._load_manifest()
        self._schedule_auto_refresh()

    
    def _build_ui(self):
        row1 = ttk.Frame(self.frame, padding=5)
        row1.pack(fill="x")

        ttk.Label(row1, text=tr("地址：")).pack(side="left")
        self.host_var = tk.StringVar()
        self._host_entry = tk.Entry(row1, textvariable=self.host_var, width=17)
        self._host_entry.pack(side="left", padx=2)

        ttk.Label(row1, text=tr("端口：")).pack(side="left")
        self.port_var = tk.StringVar()
        self._port_entry = tk.Entry(row1, textvariable=self.port_var, width=6)
        self._port_entry.pack(side="left", padx=2)

        ttk.Label(row1, text=tr("用户名：")).pack(side="left")
        self.user_var = tk.StringVar()
        self._user_entry = tk.Entry(row1, textvariable=self.user_var, width=14)
        self._user_entry.pack(side="left", padx=2)

        ttk.Label(row1, text=tr("密码：")).pack(side="left")
        self.pass_var = tk.StringVar()
        self._pass_entry = tk.Entry(row1, textvariable=self.pass_var, width=16, show="*")
        self._pass_entry.pack(side="left", padx=2)

        self.connect_btn = ttk.Button(row1, text=tr("连接并扫描"), command=self._do_scan)
        self.connect_btn.pack(side="left", padx=(8, 2))
        self.scan_status = ttk.Label(row1, text="")
        self.scan_status.pack(side="left", padx=5)

        row2 = ttk.Frame(self.frame, padding=(5, 0))
        row2.pack(fill="x")

        ttk.Button(row2, text=tr("全选"), command=lambda: self._toggle_all(True)).pack(side="left", padx=2)
        ttk.Button(row2, text=tr("取消选择"), command=lambda: self._toggle_all(False)).pack(side="left", padx=2)
        ttk.Button(row2, text=tr("全选改动"), command=self._select_new).pack(side="left", padx=2)
        ttk.Separator(row2, orient="vertical").pack(side="left", fill="y", padx=6)

        ttk.Label(row2, text=tr("筛选:")).pack(side="left", padx=2)
        self.filter_status_var = tk.StringVar(value=tr("全部"))
        self.filter_combo = ttk.Combobox(
            row2,
            textvariable=self.filter_status_var,
            values=[tr("全部"), tr("新文件"), tr("已修改"), tr("已下载"), tr("隐藏")],
            state="readonly",
            width=8,
        )
        self.filter_combo.pack(side="left", padx=2)
        self.filter_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filter())

        ttk.Separator(row2, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(row2, text=tr("下载所选文件"), command=self._do_download).pack(side="left", padx=2)
        ttk.Button(row2, text=tr("取消"), command=self._cancel).pack(side="left", padx=2)

        row3 = ttk.Frame(self.frame, padding=(5, 0))
        row3.pack(fill="x")

        ttk.Label(row3, text=tr("输出：")).pack(side="left")
        self.output_var = tk.StringVar(value=str(self.output_dir))
        ttk.Entry(row3, textvariable=self.output_var, width=30).pack(side="left", padx=2)
        ttk.Button(row3, text=tr("自定义文件夹"), command=self._browse_output).pack(side="left")

        ttk.Separator(row3, orient="vertical").pack(side="left", fill="y", padx=6)
        self.auto_refresh_var = tk.BooleanVar(value=False)
        self.auto_cb = ttk.Checkbutton(
            row3,
            text=tr("自动刷新"),
            variable=self.auto_refresh_var,
            command=self._on_auto_refresh_toggle,
        )
        self.auto_cb.pack(side="left", padx=(2, 2))

        ttk.Label(row3, text=tr("间隔(分):")).pack(side="left")
        self.interval_var = tk.StringVar(value="5")
        self.interval_combo = ttk.Combobox(
            row3,
            textvariable=self.interval_var,
            values=["0.5", "1", "5", "10", "30", "60"],
            state="readonly",
            width=4,
        )
        self.interval_combo.pack(side="left", padx=2)

        tree_frame = ttk.Frame(self.frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)

        columns = ("status",)
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="tree headings",
            selectmode="extended",
        )
        self.tree.heading("#0", text=tr("文件名"), anchor="w")
        self.tree.heading("status", text=tr("状态"), anchor="w")
        self.tree.column("#0", width=600, stretch=True)
        self.tree.column("status", width=120, anchor="w", stretch=False)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self._on_tree_dblclick)
        self.tree.bind("<space>", lambda e: self._toggle_selected())

        bottom_frame = ttk.Frame(self.frame)
        bottom_frame.pack(fill="x", padx=5, pady=(0, 2))

        self.progress = ttk.Progressbar(bottom_frame, mode="determinate")
        self.progress.pack(side="left", fill="x", expand=True)

        self.status_bar = ttk.Label(self.frame, text=tr("就绪，请连接并扫描。"), anchor="w")
        self.status_bar.pack(fill="x", padx=5, pady=(0, 5))

    
    def _get_val(self, var, key):
        
        v = var.get().strip()
        return v if v else self.cfg.get(key, DEFAULT_SETTINGS.get(key, ""))

    def _load_settings(self):
        for var, key in (
            (self.host_var, "host"),
            (self.port_var, "port"),
            (self.user_var, "username"),
            (self.pass_var, "password"),
        ):
            var.set(self.cfg.get(key) or DEFAULT_SETTINGS.get(key, ""))
        self.output_var.set(str(self.cfg.get("output") or ""))
        self.auto_refresh_var.set(bool(self.cfg.get("auto_refresh", False)))
        self.interval_var.set(str(self.cfg.get("interval", "5")))
        self._proxy_type = self.cfg.get("proxy_type", "")
        self._proxy_host = self.cfg.get("proxy_host", "")
        self._proxy_port = self.cfg.get("proxy_port", "")

    def _save_settings(self):
        out = self.output_var.get().strip()
        if out:
            self.output_dir = Path(out)
        self.cfg.update({
            "host": self._get_val(self.host_var, "host"),
            "port": self._get_val(self.port_var, "port"),
            "username": self._get_val(self.user_var, "username"),
            "password": self._get_val(self.pass_var, "password"),
            "output": str(self.output_dir),
            "auto_refresh": bool(self.auto_refresh_var.get()),
            "interval": self.interval_var.get(),
            "proxy_type": self._proxy_type,
            "proxy_host": self._proxy_host,
            "proxy_port": self._proxy_port,
        })
        
        if not self.cfg.get("chatbox_path"):
            self.cfg["chatbox_path"] = str(self.output_dir / ".runtime" / "chatbox")
        self.toolbox.save_config()

    
    def _on_auto_refresh_toggle(self):
        if self._refresh_timer_id:
            try:
                self.top.after_cancel(self._refresh_timer_id)
            except Exception:
                pass
            self._refresh_timer_id = None
        if self.auto_refresh_var.get():
            self._do_scan(auto=True)
            self._schedule_auto_refresh()

    def _schedule_auto_refresh(self):
        if not self.auto_refresh_var.get():
            return
        if not self.scanning and not self.downloading:
            self._do_scan(auto=True)
        try:
            interval_min = float(self.interval_var.get())
            interval_ms = int(interval_min * 60 * 1000)
        except ValueError:
            interval_ms = 300000
        self._refresh_timer_id = self.top.after(interval_ms, self._schedule_auto_refresh)

    
    def _load_manifest(self):
        mf = self.output_dir / ".cfms_manifest.json"
        if mf.exists():
            try:
                data = json.loads(mf.read_text("utf-8"))
            except Exception:
                data = {}
            if isinstance(data, dict) and "shas" in data:
                self.manifest = data.get("shas", {})
            elif isinstance(data, dict):
                self.manifest = data
            else:
                self.manifest = {}
        else:
            self.manifest = {}

    def _save_manifest(self):
        mf = self.output_dir / ".cfms_manifest.json"
        mf.parent.mkdir(parents=True, exist_ok=True)
        mf.write_text(
            json.dumps(self.manifest, indent=2, ensure_ascii=False),
            "utf-8",
        )

    def _file_status(self, f: dict) -> tuple[str, str]:
        sp = f["path"]
        sha = f["sha"]
        if sp in self.manifest:
            if sha and self.manifest[sp] != sha:
                return tr("已修改"), "changed"
            local_path = self.output_dir / sanitize_path(sp)
            if local_path.exists():
                if self.session_downloaded_kinds.get(sp) == "changed":
                    return tr("已下载（已修改）"), "downloaded"
                return tr("已下载"), "downloaded"
            return tr("已修改"), "changed"
        return tr("新文件"), "new"

    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.all_tree_items.clear()
        self._load_manifest()
        for f in self.files:
            status_display, tag = self._file_status(f)
            if f["hidden"]:
                tag = "hidden"
            item_id = self.tree.insert(
                "", "end",
                text=f["path"],
                values=(status_display,),
                tags=(tag,),
            )
            self.all_tree_items.append(item_id)
        self.tree.tag_configure("hidden", foreground="#9370DB")
        self.tree.tag_configure("new", foreground="#0067c0")
        self.tree.tag_configure("changed", foreground="#c42b1c")
        self._apply_filter()

    def _apply_filter(self):
        filter_val = self.filter_status_var.get()
        for item in self.all_tree_items:
            self.tree.reattach(item, "", "end")
        if filter_val == "全部":
            return
        status_map = {
            tr("新文件"): "new",
            tr("已修改"): "changed",
            tr("已下载"): "downloaded",
            tr("隐藏"): "hidden",
        }
        target = status_map.get(filter_val)
        if target is None:
            return
        for item in self.all_tree_items:
            tags = self.tree.item(item, "tags")
            if target not in tags:
                self.tree.detach(item)

    def _toggle_all(self, select: bool):
        for item in self.tree.get_children():
            if select:
                self.tree.selection_add(item)
            else:
                self.tree.selection_remove(item)

    def _select_new(self):
        self.tree.selection_remove(*self.tree.selection())
        for item in self.tree.get_children():
            tags = self.tree.item(item, "tags")
            if "new" in tags or "changed" in tags:
                self.tree.selection_add(item)

    def _toggle_selected(self):
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def _on_tree_dblclick(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        idx = self.tree.index(item)
        if idx >= len(self.files):
            return
        f = self.files[idx]
        sp = f["path"]

        local_path = self.output_dir / sanitize_path(sp)
        if local_path.exists():
            try:
                text = local_path.read_text("utf-8", errors="replace")
            except Exception:
                mb.showinfo(tr("预览: "), tr("无法预览二进制文件:\n") + sp)
                return
        else:
            if not self.client:
                return
            try:
                self.status_bar.config(text=tr("正在下载 {sp} 用于预览...").format(sp=sp))
                data = self.client.download(f["id"])
                text = data.decode("utf-8", errors="replace")
            except Exception as e:
                mb.showerror(tr("错误"), str(e))
                return
            self.status_bar.config(text=tr("就绪。"))

        pw = tk.Toplevel(self.top)
        pw.title(tr("预览: ") + sp)
        pw.geometry("700x500")
        txt = tk.Text(pw, wrap="word", font=("Consolas", 10))
        txt.insert("1.0", text)
        txt.config(state="disabled")
        sb = ttk.Scrollbar(pw, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _browse_output(self):
        d = filedialog.askdirectory(initialdir=str(self.output_dir))
        if d:
            self.output_dir = Path(d).resolve()
            self.output_var.set(str(self.output_dir))
            self.session_downloaded_kinds.clear()
            self._load_manifest()
            if self.files:
                self._populate_tree()

    
    def _do_scan(self, auto=False):
        if self.scanning:
            return
        self.scanning = True
        self._auto_scan = auto
        self.session_downloaded_kinds.clear()

        if not auto:
            self.connect_btn.config(state="disabled")
            self.scan_status.config(text=tr("正在连接..."))
            self.status_bar.config(text=tr("正在扫描服务器..."))
        else:
            self.scan_status.config(text=tr("自动刷新中..."))
            self.status_bar.config(text=tr("自动刷新扫描服务器..."))

        def task():
            try:
                host = self._get_val(self.host_var, "host").strip()
                port_str = self._get_val(self.port_var, "port").strip()
                user = self._get_val(self.user_var, "username").strip()
                pwd = self._get_val(self.pass_var, "password")
                if not host or not port_str:
                    raise RuntimeError(tr("请先在顶部填写服务器地址和端口"))
                if not user or not pwd:
                    raise RuntimeError(tr("请先填写用户名和密码"))
                port = int(port_str)

                c = CFMSClient(host, port,
                               proxy_type=self._proxy_type,
                               proxy_host=self._proxy_host,
                               proxy_port=int(self._proxy_port or "0"))
                c.connect()
                c.rpc("server_info", {})
                c.login(user, pwd)
                self.client = c
                self._save_settings()

                self.top.after(0, lambda: self.scan_status.config(text=tr("正在扫描...")))
                files = scan_server(c)
                self.files = files

                def done():
                    self._populate_tree()
                    self.scan_status.config(text=tr("共找到 {n} 个文件").format(n=len(files)))
                    self.status_bar.config(
                        text=tr("扫描结束，共找到 {n} 个文件。蓝色-新文件，紫色-隐藏文件，红色-已修改文件").format(n=len(files))
                    )
                    if not auto:
                        self.connect_btn.config(state="normal")
                    self.scanning = False
                    self._notify_new_files()

                self.top.after(0, done)
            except Exception as exc:
                err_msg = str(exc)

                def fail():
                    if auto:
                        self.scan_status.config(text=tr("自动刷新失败"))
                        self.status_bar.config(text=tr("自动刷新错误：") + err_msg)
                        try:
                            self.toolbox._notify(
                                tr("自动刷新错误："), err_msg)
                        except Exception:
                            pass
                    else:
                        mb.showerror(tr("扫描错误"), err_msg)
                        self.scan_status.config(text=tr("失败"))
                        self.status_bar.config(text=tr("错误") + f"：{err_msg}")
                    if not auto:
                        self.connect_btn.config(state="normal")
                    self.scanning = False

                self.top.after(0, fail)

        threading.Thread(target=task, daemon=True).start()

    def _notify_new_files(self):
        new_count = 0
        changed_count = 0
        for f in self.files:
            status, tag = self._file_status(f)
            if tag == "new":
                new_count += 1
            elif tag == "changed":
                changed_count += 1
        if new_count or changed_count:
            self.scan_status.config(
                text=tr("发现 {n} 个新文件 / {m} 个已修改").format(
                    n=new_count, m=changed_count)
            )
            try:
                self.toolbox._notify(
                    tr("扫描发现"),
                    tr("新增 {n} 个文件，{m} 个已修改。").format(
                        n=new_count, m=changed_count))
            except Exception:
                pass

    def _do_download(self):
        if self.downloading:
            return
        sel = self.tree.selection()
        if not sel:
            mb.showinfo(tr("提示"), tr("请先选择要下载的文件"))
            return

        indices = [self.tree.index(s) for s in sel]
        if not indices:
            return
        to_dl = [self.files[i] for i in indices if i < len(self.files)]
        if not to_dl:
            return

        out = self.output_var.get().strip()
        if not out:
            mb.showinfo(tr("提示"), tr("请先设置输出文件夹（点击「自定义文件夹」选择保存位置）。"))
            return
        self.output_dir = Path(out)
        self._save_settings()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._load_manifest()

        self.downloading = True
        self.cancel_download = False
        total_files = len(to_dl)
        self.progress["maximum"] = total_files
        self.progress["value"] = 0

        def task():
            downloaded = 0
            failed = 0
            for i, f in enumerate(to_dl):
                if self.cancel_download:
                    break

                sp = f["path"]
                local_rel = sanitize_path(sp)
                local_path = self.output_dir / local_rel
                if sp in self.manifest:
                    if f["sha"] and self.manifest[sp] != f["sha"]:
                        kind = "changed"
                    elif not local_path.exists():
                        kind = "changed"
                    else:
                        kind = "new"
                else:
                    kind = "new"

                self.top.after(0, lambda i=i, sp=sp, total=total_files: (
                self.status_bar.config(text=tr("正在下载 [{i}/{n}] {sp} ...").format(
                    i=i + 1, n=total, sp=sp)),
                    self.progress.configure(value=i + 1)
                ))

                try:
                    data = self.client.download(f["id"])
                    local_sha = hashlib.sha256(data).hexdigest()
                    if f["sha"] and local_sha != f["sha"]:
                        raise RuntimeError(
                            f"SHA校验不匹配: 服务器={f['sha'][:16]}... 本地={local_sha[:16]}..."
                        )

                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    local_path.write_bytes(data)
                    self.manifest[sp] = local_sha
                    self.session_downloaded_kinds[sp] = kind
                    downloaded += 1

                except Exception as e:
                    failed += 1
                    self.top.after(0, lambda sp=sp, e=e: (
                    mb.showwarning(tr("下载出错"), f"{sp}\n{str(e)}")
                    ))

            self._save_manifest()

            def done():
                self.downloading = False
                self.progress["value"] = total_files
                self._populate_tree()
                self.status_bar.config(
                    text=tr("下载完成：{d} 个文件成功，{f} 个失败，跳过 {s} 个").format(
                        d=downloaded, f=failed,
                        s=total_files - downloaded - failed)
                )

            self.top.after(0, done)

        threading.Thread(target=task, daemon=True).start()

    def _cancel(self):
        if self.downloading:
            self.cancel_download = True
            self.status_bar.config(text=tr("正在取消..."))

    def shutdown(self):
        try:
            if self._refresh_timer_id:
                self.top.after_cancel(self._refresh_timer_id)
                self._refresh_timer_id = None
        except Exception:
            pass
        try:
            if self.client:
                self.client.close()
        except Exception:
            pass


URL_PAT = re.compile(r"https?://[^\s)]+")

BUBBLE_COLORS = [
    "#ffffff",
    "#b8e4ff",
    "#c8f7c5",
    "#fff5b8",
    "#ffe0ec",
    "#e8d5ff",
    "#ffddc4",
    "#b8f0f0",
]

STRIP_COLORS = [
    "#e0e0e0",
    "#6cc4f5",
    "#5cd65c",
    "#f0d800",
    "#f580a8",
    "#b070f0",
    "#f09050",
    "#40c8c8",
]

REPLY_PAT = re.compile(r"\s*//\s*(\w{7})\s*->\s*(.*)$", re.DOTALL)


def _open_file(path: str) -> None:
    try:
        os.startfile(path)
    except Exception:
        subprocess.Popen(["start", "", path], shell=True)


def _build_webui_data(panel) -> dict:
    rooms = []
    for rid, room in panel.rooms.items():
        msgs = [{
            "user": m["user"],
            "name": panel.user_names.get(m["user"], m["user"][:8] + "…"),
            "time": m["time"],
            "content": m["content"],
        } for m in room["msgs"]]
        atts = []
        for p in room["attachments"]:
            ext = p.suffix.lower()
            if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"):
                kind = "image"
            elif ext in (".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac"):
                kind = "audio"
            else:
                kind = "other"
            atts.append({
                "name": p.name,
                "url": f"/file/{urllib.parse.quote(rid)}/{urllib.parse.quote(p.name)}",
                "kind": kind,
            })
        nf = [{"file": b["file"], "lines": b["lines"]}
              for b in (room.get("nonformat") or [])]
        last_time = msgs[-1]["time"] if msgs else ""
        rooms.append({
            "id": rid,
            "name": panel.room_names.get(rid, rid[:8] + "…"),
            "msgs": msgs,
            "attachments": atts,
            "nonformat": nf,
            "last_time": last_time,
        })
    rooms.sort(key=lambda r: r["last_time"], reverse=True)
    return {"rooms": rooms}


_WEBUI_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CFMS Toolbox</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100%;height:100%;overflow:hidden;background:#141413;color:#fff;font-family:'HarmonyOS Sans SC','MiSans','PingFang SC','Microsoft YaHei',sans-serif}
#stage{position:absolute;left:50%;top:50%;margin-left:-960px;margin-top:-540px;width:1920px;height:1080px;transform:scale(var(--k));transform-origin:center}
#tricolor{position:absolute;left:0;top:0;width:100%;height:4px;display:flex;z-index:5}
#tricolor i{flex:1}
#tricolor .m{background:#e202e2}
#tricolor .y{background:#f3f100}
#tricolor .c{background:#01f1f1}
#header{position:absolute;left:43px;top:26px;font-size:27px;letter-spacing:-0.5px;color:#fff;z-index:5;font-weight:500;user-select:text}
#cards{position:absolute;left:0;top:84px;width:560px;bottom:0;overflow-y:auto;padding:12px}
.card{background:#2b2927;border:1px solid transparent;border-radius:6px;margin-bottom:12px;cursor:pointer}
.card:hover{background:#3e3f3d;border-color:#575657}
.card-main{display:flex;align-items:center;padding:16px 18px}
.card-avatar{width:68px;height:68px;border-radius:50%;border:1px solid #575657;display:flex;align-items:center;justify-content:center;font-size:26px;font-weight:600;flex-shrink:0}
.card-info{margin-left:16px;min-width:0}
.card-name{font-size:26px;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card-meta{color:#8f8d8b;font-size:16px;margin-top:6px}
.card-sub{display:none;border-top:1px solid #1c1c1c;padding:10px}
.card.open .card-sub{display:block}
.sub-btn{display:flex;justify-content:space-between;align-items:center;width:100%;text-align:left;background:#3e3f3d;color:#e3e1e1;border:none;padding:12px 15px;margin:5px 0;border-radius:5px;cursor:pointer;font-size:18px}
.sub-btn:hover{background:#4a4a48;color:#fff}
.sub-btn .cnt{color:#8f8d8b}
#chat{position:absolute;left:560px;top:0;right:0;bottom:0;display:flex;flex-direction:column}
#strip{height:92px;background:#171716;border-bottom:1px solid #2b2a28;display:flex;align-items:center;padding:0 30px}
#strip .name{font-size:29px;color:#fff;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#frame{flex:1;margin:18px 28px 28px;border:1.5px solid #cac9c9;border-radius:8px;display:flex;flex-direction:column;overflow:hidden;background:rgba(255,255,255,0.02)}
#frame-bar{display:flex;height:5px}
#frame-bar i{flex:1}
#frame-bar .m{background:#e202e2}
#frame-bar .y{background:#f3f100}
#frame-bar .c{background:#01f1f1}
#msgs{flex:1;overflow-y:auto;padding:24px 30px}
.msg{display:flex;margin:14px 0;align-items:flex-start}
.msg.self{flex-direction:row-reverse}
.avatar{width:54px;height:54px;border-radius:50%;border:1px solid #575657;display:flex;align-items:center;justify-content:center;font-size:21px;font-weight:600;flex-shrink:0}
.msg-body{margin:0 14px;max-width:62%}
.msg.self .msg-body{text-align:right}
.msg-name{color:#b8b6b4;font-size:16px;margin-bottom:6px}
.msg.self .msg-name{text-align:right}
.bubble{position:relative;display:inline-block;background:#464444;color:#fff;border-radius:15px;padding:12px 18px;font-size:19px;line-height:1.55;white-space:pre-wrap;word-break:break-word;text-align:left}
.msg.self .bubble{background:#f0eeee;color:#000}
.bubble::before{content:"";position:absolute;top:14px;width:0;height:0;border:7px solid transparent}
.msg:not(.self) .bubble::before{left:-12px;border-right-color:#464444}
.msg.self .bubble::before{right:-12px;border-left-color:#f0eeee}
.msg-time{color:#6f6d6b;font-size:14px;margin-top:5px}
.msg.self .msg-time{text-align:right}
.list{padding:10px}
.file-item{background:#2b2927;padding:14px 16px;margin-bottom:10px;border-radius:6px;color:#e3e1e1;cursor:pointer;font-size:18px}
.file-item:hover{background:#3e3f3d}
.file-img{max-width:300px;max-height:220px;display:block;border-radius:6px;margin-bottom:8px;object-fit:contain}
.file-name{color:#e3e1e1}
audio{width:100%;max-width:460px;display:block;margin-bottom:8px}
#lightbox{position:absolute;left:0;top:0;width:1920px;height:1080px;background:rgba(0,0,0,0.88);display:none;align-items:center;justify-content:center;z-index:99;cursor:zoom-out}
#lightbox.show{display:flex}
#lightbox img{max-width:90%;max-height:90%;border:1px solid #575657;border-radius:4px}
.nf-block{background:#2b2927;padding:14px 16px;margin-bottom:14px;border-radius:6px}
.nf-file{color:#cac9c9;font-size:13px;margin-bottom:8px;border-bottom:1px solid #1c1c1c;padding-bottom:6px}
.nf-line{color:#e3e1e1;white-space:pre-wrap;line-height:1.7;font-size:16px}
.empty{color:#6f6d6b;text-align:center;padding:80px 0;font-size:18px}
#msgs::-webkit-scrollbar,#cards::-webkit-scrollbar{width:8px}
#msgs::-webkit-scrollbar-thumb,#cards::-webkit-scrollbar-thumb{background:#3e3f3d;border-radius:4px}
</style>
</head>
<body>
<div id="stage">
  <div id="tricolor"><i class="m"></i><i class="y"></i><i class="c"></i></div>
  <div id="header">%%TITLE%%</div>
  <div id="cards"></div>
  <div id="chat">
    <div id="strip"><div class="name" id="roomName">%%SELECT%%</div></div>
    <div id="frame">
      <div id="frame-bar"><i class="m"></i><i class="y"></i><i class="c"></i></div>
      <div id="msgs"><div class="empty">%%SELECT%%</div></div>
    </div>
  </div>
  <div id="lightbox"><img id="lightboxImg" alt=""></div>
</div>
<script>
const L={chat:"%%CHAT%%",attach:"%%ATTACH%%",nf:"%%NF%%",msgs:"%%MSGS%%",last:"%%LAST%%"};
const PALETTE=["#576b95","#07c160","#e6a23c","#409eff","#f56c6c","#909399","#9b59b6","#1abc9c"];
function hashStr(s){let h=0;for(const c of s){h=(h*31+c.charCodeAt(0))>>>0}return h}
function avatarOf(uid,label){return {c:PALETTE[hashStr(uid)%PALETTE.length],ch:(label||uid||"?").charAt(0).toUpperCase()}}
function esc(s){const d=document.createElement("div");d.textContent=s;return d.innerHTML}
const lb=document.getElementById("lightbox");const lbImg=document.getElementById("lightboxImg");
function showImg(u){lbImg.src=u;lb.classList.add("show")}
lb.addEventListener("click",()=>{lb.classList.remove("show");lbImg.src=""});
function fit(){
  const k=Math.min(innerWidth/1920,innerHeight/1080);
  document.getElementById("stage").style.setProperty("--k",String(k));
}
async function init(){
  fit();addEventListener("resize",fit);
  const r=await fetch("/data.json");const DATA=await r.json();
  const cards=document.getElementById("cards");
  for(const room of DATA.rooms){
    const selfId=room.msgs.length?room.msgs[0].user:null;
    const nfCount=room.nonformat.reduce((a,b)=>a+b.lines.length,0);
    const {c,ch}=avatarOf(room.id,room.name);
    const card=document.createElement("div");card.className="card";
    card.innerHTML='<div class="card-main">'+
      '<div class="card-avatar" style="background:'+c+'">'+ch+'</div>'+
      '<div class="card-info"><div class="card-name">'+esc(room.name)+'</div>'+
      '<div class="card-meta">'+room.msgs.length+' '+L.msgs+' · '+L.last+esc(room.last_time)+'</div></div></div>'+
      '<div class="card-sub">'+
      '<button class="sub-btn" data-a="chat">'+L.chat+'<span class="cnt">'+room.msgs.length+'</span></button>'+
      '<button class="sub-btn" data-a="att">'+L.attach+'<span class="cnt">'+room.attachments.length+'</span></button>'+
      '<button class="sub-btn" data-a="nf">'+L.nf+'<span class="cnt">'+nfCount+'</span></button>'+
      '</div>';
    card.addEventListener("click",()=>card.classList.toggle("open"));
    card.querySelectorAll(".sub-btn").forEach(b=>b.addEventListener("click",e=>{
      e.stopPropagation();showRoom(room,b.dataset.a,selfId);
    }));
    cards.appendChild(card);
  }
}
function showRoom(room,action,selfId){
  document.getElementById("roomName").textContent=room.name;
  const c=document.getElementById("msgs");c.innerHTML="";
  if(action==="att"){
    if(!room.attachments.length){c.innerHTML='<div class="empty">-</div>';return}
    const list=document.createElement("div");list.className="list";
    for(const f of room.attachments){
      const d=document.createElement("div");d.className="file-item";d.textContent=f.name;
      if(f.kind==="image"){
        d.innerHTML='<img class="file-img" src="'+f.url+'" alt="">'+
          '<div class="file-name">'+esc(f.name)+'</div>';
        d.addEventListener("click",()=>showImg(f.url));
      } else if(f.kind==="audio"){
        d.innerHTML='<audio controls preload="none" src="'+f.url+'"></audio>'+
          '<div class="file-name">'+esc(f.name)+'</div>';
      } else {
        d.textContent=f.name;
        d.addEventListener("click",()=>window.open(f.url,"_blank"));
      }
      list.appendChild(d);
    }
    c.appendChild(list);return;
  }
  if(action==="nf"){
    if(!room.nonformat.length){c.innerHTML='<div class="empty">-</div>';return}
    for(const blk of room.nonformat){
      const d=document.createElement("div");d.className="nf-block";
      d.innerHTML='<div class="nf-file">'+esc(blk.file)+'</div>'+
        blk.lines.map(l=>'<div class="nf-line">'+esc(l)+'</div>').join("");
      c.appendChild(d);
    }
    return;
  }
  if(!room.msgs.length){c.innerHTML='<div class="empty">-</div>';return}
  for(const m of room.msgs){
    const isSelf=m.user===selfId;
    const {c:ac,ch}=avatarOf(m.user,m.name);
    const row=document.createElement("div");row.className="msg"+(isSelf?" self":"");
    const av=document.createElement("div");av.className="avatar";av.style.background=ac;av.textContent=ch;
    const body=document.createElement("div");body.className="msg-body";
    const nm=document.createElement("div");nm.className="msg-name";nm.textContent=m.name;
    const bub=document.createElement("div");bub.className="bubble";bub.textContent=m.content;
    const tm=document.createElement("div");tm.className="msg-time";tm.textContent=m.time;
    body.append(nm,bub,tm);
    row.append(av,body);
    c.appendChild(row);
  }
  c.scrollTop=c.scrollHeight;
}
init();
</script>
</body>
</html>"""


_FILE_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".svg": "image/svg+xml",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".m4a": "audio/mp4",
    ".flac": "audio/flac",
    ".aac": "audio/aac",
}


class BetterUI:
    def __init__(self):
        self.server = None
        self.thread = None
        self.port = 0

    def _make_handler(self, chatbox_root):
        def _serve_file(h, path):
            try:
                parts = path.split("/")[2:]
                if len(parts) != 2:
                    h.send_error(400)
                    return
                room_id = urllib.parse.unquote(parts[0])
                name = urllib.parse.unquote(parts[1])
                if "/" in name or "\\" in name or ".." in name:
                    h.send_error(400)
                    return
                base = (Path(chatbox_root) / room_id).resolve()
                fp = (base / name).resolve()
                if not str(fp).startswith(str(base)) or not fp.is_file():
                    h.send_error(404)
                    return
                body = fp.read_bytes()
                ext = fp.suffix.lower()
                ctype = _FILE_TYPES.get(ext)
                if ctype is None:
                    ctype = ("text/plain; charset=utf-8"
                             if ext in (".txt", ".json", ".log", ".md")
                             else "application/octet-stream")
                h.send_response(200)
                h.send_header("Content-Type", ctype)
                h.send_header("Content-Length", str(len(body)))
                h.end_headers()
                h.wfile.write(body)
            except Exception:
                h.send_error(400)

        class _Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                if parsed.path in ("/", "/index.html"):
                    html = (_WEBUI_HTML
                            .replace("%%CHAT%%", tr("聊天记录"))
                            .replace("%%ATTACH%%", tr("附件"))
                            .replace("%%NF%%", tr("非格式文本"))
                            .replace("%%SELECT%%", tr("选择一个房间"))
                            .replace("%%TITLE%%", tr("CFMS聊天记录"))
                            .replace("%%MSGS%%", tr("条消息"))
                            .replace("%%LAST%%", tr("最后：")))
                    body = html.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                elif parsed.path == "/data.json":
                    body = json.dumps(self.server.data, ensure_ascii=False).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                elif parsed.path.startswith("/file/"):
                    _serve_file(self, parsed.path)
                else:
                    self.send_error(404)

            def log_message(self, *args):
                pass

        return _Handler

    def start(self, data: dict, chatbox_root) -> str:
        self.stop()
        handler = self._make_handler(chatbox_root)
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.server.data = data
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return f"http://127.0.0.1:{self.port}/"

    def stop(self) -> None:
        if self.server is not None:
            try:
                self.server.shutdown()
                self.server.server_close()
            except Exception:
                pass
            self.server = None
            self.thread = None


class QuickViewPanel:
    

    def __init__(self, parent, toolbox):
        self.toolbox = toolbox
        self.cfg = toolbox.cfg
        self.frame = ttk.Frame(parent)
        self.top = self.frame.winfo_toplevel()

        self.chatbox_path: str = ""
        self.rooms: dict[str, dict] = {}
        self.room_names: dict[str, str] = {}
        self.user_names: dict[str, str] = {}
        self._cur_room: str | None = None

        self._room_canvas: tk.Canvas | None = None
        self._room_inner: tk.Frame | None = None
        self._room_cards: dict[str, tk.Frame] = {}
        self._chat_canvas: tk.Canvas | None = None
        self._msg_frame: tk.Frame | None = None
        self._attach_frame: tk.Frame | None = None
        self._canvas_win_id: int = 0
        self._status_lbl: ttk.Label | None = None

        self._load_cfg()
        self._build_ui()
        self._scan()

    
    def _load_cfg(self) -> None:
        self.chatbox_path = str(self.cfg.get("chatbox_path", ""))
        self.room_names = dict(self.cfg.get("room_names", {}))
        self.user_names = dict(self.cfg.get("user_names", {}))

    def _save_cfg(self) -> None:
        self.cfg["chatbox_path"] = self.chatbox_path
        self.cfg["room_names"] = self.room_names
        self.cfg["user_names"] = self.user_names
        self.toolbox.save_config()

    
    def _pick_folder(self) -> None:
        d = filedialog.askdirectory(title="选择 .runtime/chatbox 文件夹")
        if d:
            self.chatbox_path = d
            self._save_cfg()
            self._scan()

    def _open_better_ui(self) -> None:
        if not self.chatbox_path or not os.path.isdir(self.chatbox_path):
            mb.showinfo(tr("提示"), tr("请选择 chatbox 文件夹"))
            return
        try:
            self._scan()
            if not getattr(self, "better_ui", None):
                self.better_ui = BetterUI()
            data = _build_webui_data(self)
            url = self.better_ui.start(data, Path(self.chatbox_path))
            os.startfile(url)
        except Exception as e:
            mb.showerror(tr("错误"), tr("打开网页查看失败：{e}").format(e=e))

    def _show_help(self) -> None:
        dlg = tk.Toplevel(self.top)
        dlg.title(tr("帮助"))
        dlg.geometry("420x300")
        dlg.resizable(False, False)
        dlg.transient(self.top)
        dlg.grab_set()
        self._center_window(dlg, 420, 300)

        tk.Label(dlg, text=f"{APP_TITLE} - {tr('聊天记录')}",
                 font=("Microsoft YaHei", 12, "bold")).pack(pady=(16, 10))
        tk.Label(dlg, text=(
            "读取已下载的 .runtime/chatbox 下的聊天记录，\n"
            "以聊天气泡风格按时间顺序展示各房间的对话。"),
                 font=("Microsoft YaHei", 9), fg="#555", justify="center").pack()

        tk.Label(dlg, text=(
            "工具栏：选择文件夹 / 刷新 / 设置 / 帮助\n"
            "左侧列表：单击选房间，双击改房间名\n"
            "右侧对话：单击用户名可改名，文字可选中复制\n"
            "网址链接：点击气泡内链接可在弹窗中选择打开或复制"),
                 font=("Microsoft YaHei", 9), justify="left",
                 wraplength=370).pack(pady=(12, 0))

        tk.Button(dlg, text=tr("确定"), command=dlg.destroy,
                  font=("Microsoft YaHei", 10), padx=20).pack(pady=(4, 12))

    def _show_settings(self) -> None:
        dlg = tk.Toplevel(self.top)
        dlg.title(tr("设置"))
        dlg.geometry("600x460")
        dlg.resizable(False, False)
        dlg.transient(self.top)
        dlg.grab_set()
        self._center_window(dlg, 600, 460)

        nb = ttk.Notebook(dlg)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        tab1 = ttk.Frame(nb)
        nb.add(tab1, text=tr("文件夹"))

        ttk.Label(tab1, text=tr("chatbox 文件夹路径:"),
                  font=("Microsoft YaHei", 10)).pack(anchor="w", padx=16, pady=(16, 6))
        path_var = tk.StringVar(value=self.chatbox_path)
        path_entry = ttk.Entry(tab1, textvariable=path_var, width=70)
        path_entry.pack(padx=16, pady=2, fill="x")
        ttk.Button(tab1, text=tr("浏览…"), command=lambda: self._browse_settings(path_var)).pack(
            anchor="w", padx=16, pady=(4, 12))

        tab2 = ttk.Frame(nb)
        nb.add(tab2, text=tr("房间名"))

        room_frame = tk.Frame(tab2, bg="#f0f0f0")
        room_frame.pack(fill="both", expand=True, padx=8, pady=8)

        room_lb = tk.Listbox(room_frame, font=("Consolas", 9), bg="white",
                              selectbackground="#cce5ff", activestyle="none",
                              borderwidth=1, highlightthickness=0)
        room_scroll = tk.Scrollbar(room_frame, orient="vertical", command=room_lb.yview)
        room_lb.configure(yscrollcommand=room_scroll.set)
        room_lb.pack(side="left", fill="both", expand=True)
        room_scroll.pack(side="right", fill="y")

        room_items: list[tuple[str, str]] = []
        for rid in self.rooms:
            cname = self.room_names.get(rid, "")
            room_items.append((rid, cname))
        room_items.sort(key=lambda x: x[1] or x[0])

        for rid, cname in room_items:
            disp = f"{cname if cname else '(默认)'}   → {rid}"
            room_lb.insert("end", disp)

        ttk.Label(tab2, text=tr("双击列表项可编辑房间名"),
                  font=("Microsoft YaHei", 8), foreground="#888").pack(anchor="w", padx=12, pady=(0, 6))

        def room_dblclick(e):
            sel = room_lb.curselection()
            if not sel:
                return
            idx = sel[0]
            rid, _ = room_items[idx]
            old = self.room_names.get(rid, "")
            new = simpledialog.askstring(tr("重命名房间"),
                tr("房间 {r}…\n输入自定义名称(留空恢复默认):").format(r=rid[:16]),
                initialvalue=old, parent=dlg)
            if new is not None:
                if new.strip():
                    self.room_names[rid] = new.strip()
                else:
                    self.room_names.pop(rid, None)
                self._save_cfg()
                self._render_room_list()
                dlg.destroy()
                self._show_settings()

        room_lb.bind("<Double-Button-1>", room_dblclick)
        room_lb.bind("<MouseWheel>", lambda e: room_lb.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        tab3 = ttk.Frame(nb)
        nb.add(tab3, text=tr("用户名"))

        user_frame = tk.Frame(tab3, bg="#f0f0f0")
        user_frame.pack(fill="both", expand=True, padx=8, pady=8)

        user_lb = tk.Listbox(user_frame, font=("Consolas", 9), bg="white",
                              selectbackground="#cce5ff", activestyle="none",
                              borderwidth=1, highlightthickness=0)
        user_scroll = tk.Scrollbar(user_frame, orient="vertical", command=user_lb.yview)
        user_lb.configure(yscrollcommand=user_scroll.set)
        user_lb.pack(side="left", fill="both", expand=True)
        user_scroll.pack(side="right", fill="y")

        all_uids: set[str] = set()
        for rid in self.rooms:
            for m in self.rooms[rid]["msgs"]:
                all_uids.add(m["user"])

        user_items = sorted(all_uids)
        for uid in user_items:
            cname = self.user_names.get(uid, "")
            disp = f"{cname if cname else '(默认)'}   → {uid}"
            user_lb.insert("end", disp)

        ttk.Label(tab3, text=tr("双击列表项可编辑用户名"),
                  font=("Microsoft YaHei", 8), foreground="#888").pack(anchor="w", padx=12, pady=(0, 6))

        def user_dblclick(e):
            sel = user_lb.curselection()
            if not sel:
                return
            idx = sel[0]
            uid = user_items[idx]
            old = self.user_names.get(uid, "")
            new = simpledialog.askstring(tr("重命名用户"),
                tr("用户 {u}…\n输入自定义名称(留空恢复默认):").format(u=uid[:16]),
                initialvalue=old, parent=dlg)
            if new is not None:
                if new.strip():
                    self.user_names[uid] = new.strip()
                else:
                    self.user_names.pop(uid, None)
                self._save_cfg()
                self._render_chat()
                dlg.destroy()
                self._show_settings()

        user_lb.bind("<Double-Button-1>", user_dblclick)
        user_lb.bind("<MouseWheel>", lambda e: user_lb.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        def save_path():
            new_path = path_var.get().strip()
            if new_path and new_path != self.chatbox_path:
                self.chatbox_path = new_path
                self._save_cfg()
                self._scan()
            dlg.destroy()

        btn_frame = ttk.Frame(dlg)
        btn_frame.pack(fill="x", padx=8, pady=(0, 10))
        ttk.Button(btn_frame, text=tr("确定"), command=save_path).pack(side="right", padx=4)
        ttk.Button(btn_frame, text=tr("取消"), command=dlg.destroy).pack(side="right", padx=4)

    def _browse_settings(self, path_var):
        d = filedialog.askdirectory(title="选择 .runtime/chatbox 文件夹")
        if d:
            path_var.set(d)

    
    def _build_ui(self) -> None:
        tbar = ttk.Frame(self.frame, padding=(8, 6))
        tbar.pack(fill="x")

        ttk.Button(tbar, text=tr("选择文件夹"), command=self._pick_folder).pack(side="left")
        ttk.Button(tbar, text=tr("刷新"), command=self._scan).pack(side="left", padx=(6, 0))
        ttk.Button(tbar, text=tr("网页查看"), command=self._open_better_ui).pack(side="left", padx=(6, 0))
        ttk.Button(tbar, text=tr("设置"), command=self._show_settings).pack(side="left", padx=(6, 0))
        ttk.Button(tbar, text=tr("帮助"), command=self._show_help).pack(side="left", padx=(6, 0))

        self._path_lbl = ttk.Label(tbar, text="", foreground="#888")
        self._path_lbl.pack(side="left", padx=(12, 0))

        pw = ttk.PanedWindow(self.frame, orient="horizontal")
        pw.pack(fill="both", expand=True, padx=(8, 8), pady=(2, 4))

        left_frame = ttk.Frame(pw, width=340)
        pw.add(left_frame, weight=0)

        ttk.Label(left_frame, text="聊天室", font=("Microsoft YaHei", 10, "bold"),
                  padding=(4, 4)).pack(fill="x")

        list_frame = tk.Frame(left_frame, bg="#e8e8e8")
        list_frame.pack(fill="both", expand=True)

        self._room_canvas = tk.Canvas(list_frame, bg="#f5f5f5",
                                       highlightthickness=0, bd=0)
        room_scrollbar = tk.Scrollbar(list_frame, orient="vertical",
                                       command=self._room_canvas.yview)
        self._room_canvas.configure(yscrollcommand=room_scrollbar.set)

        self._room_inner = tk.Frame(self._room_canvas, bg="#f5f5f5")
        self._room_win_id = self._room_canvas.create_window(
            (0, 0), window=self._room_inner, anchor="nw")

        self._room_inner.bind("<Configure>",
            lambda e: self._room_canvas.configure(
                scrollregion=self._room_canvas.bbox("all")))

        self._room_canvas.bind("<Configure>",
            lambda e: self._room_canvas.itemconfig(self._room_win_id, width=e.width))

        self._room_canvas.grid(row=0, column=0, sticky="nsew")
        room_scrollbar.grid(row=0, column=1, sticky="ns")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self._room_canvas.bind("<MouseWheel>", self._on_room_wheel)
        self._room_canvas.bind("<Button-4>", lambda e: self._room_canvas.yview_scroll(-1, "units"))
        self._room_canvas.bind("<Button-5>", lambda e: self._room_canvas.yview_scroll(1, "units"))

        right_frame = ttk.Frame(pw)
        pw.add(right_frame, weight=1)

        self._chat_canvas = tk.Canvas(right_frame, bg="#f0f0f0",
                                       highlightthickness=0, bd=0)
        vsb = ttk.Scrollbar(right_frame, orient="vertical",
                            command=self._chat_canvas.yview)
        self._chat_canvas.configure(yscrollcommand=vsb.set)

        self._msg_frame = tk.Frame(self._chat_canvas, bg="#f0f0f0")
        self._canvas_win_id = self._chat_canvas.create_window(
            (0, 0), window=self._msg_frame, anchor="nw")

        self._msg_frame.bind("<Configure>",
            lambda e: self._chat_canvas.configure(
                scrollregion=self._chat_canvas.bbox("all")))
        self._chat_canvas.bind("<Configure>", self._on_canvas_resize)
        for w in (self._chat_canvas, self._msg_frame, right_frame):
            w.bind("<MouseWheel>", self._on_mousewheel)
            w.bind("<Button-4>", self._on_mousewheel_up)
            w.bind("<Button-5>", self._on_mousewheel_down)

        self._chat_canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        self._attach_frame = tk.Frame(right_frame, bg="#e0e0e0", height=36)
        self._attach_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        self._attach_frame.grid_propagate(False)

        self._status_lbl = ttk.Label(self.frame, text=tr("就绪"), anchor="w",
                                      padding=(8, 2))
        self._status_lbl.pack(fill="x")

    
    def _on_canvas_resize(self, event: tk.Event) -> None:
        self._chat_canvas.itemconfig(self._canvas_win_id, width=event.width)

    def _on_mousewheel(self, event):
        self._chat_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_up(self, event):
        self._chat_canvas.yview_scroll(-1, "units")

    def _on_mousewheel_down(self, event):
        self._chat_canvas.yview_scroll(1, "units")

    def _on_room_wheel(self, event: tk.Event) -> None:
        self._room_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_scroll_recursive(self, parent):
        for child in parent.winfo_children():
            child.bind("<MouseWheel>", self._on_mousewheel)
            child.bind("<Button-4>", self._on_mousewheel_up)
            child.bind("<Button-5>", self._on_mousewheel_down)
            if child.winfo_children():
                self._bind_scroll_recursive(child)

    def _bind_room_scroll(self):
        self._room_inner.bind("<MouseWheel>", self._on_room_wheel)
        self._room_inner.bind("<Button-4>", lambda e: self._room_canvas.yview_scroll(-1, "units"))
        self._room_inner.bind("<Button-5>", lambda e: self._room_canvas.yview_scroll(1, "units"))
        for child in self._room_inner.winfo_children():
            child.bind("<MouseWheel>", self._on_room_wheel)
            child.bind("<Button-4>", lambda e: self._room_canvas.yview_scroll(-1, "units"))
            child.bind("<Button-5>", lambda e: self._room_canvas.yview_scroll(1, "units"))
            for sub in child.winfo_children():
                sub.bind("<MouseWheel>", self._on_room_wheel)
                sub.bind("<Button-4>", lambda e: self._room_canvas.yview_scroll(-1, "units"))
                sub.bind("<Button-5>", lambda e: self._room_canvas.yview_scroll(1, "units"))

    
    def _scan(self) -> None:
        if not self.chatbox_path:
            if self.cfg.get("chatbox_path"):
                self._load_cfg()
        if not self.chatbox_path or not os.path.isdir(self.chatbox_path):
            self._path_lbl.config(text=tr("请选择 chatbox 文件夹"))
            self._status_lbl.config(text=tr("未选择文件夹"))
            return

        self._path_lbl.config(text=self.chatbox_path)
        self.rooms.clear()
        root = Path(self.chatbox_path)

        raw_rooms: list[tuple[str, Path, list[dict], list[Path]]] = []
        for d in root.iterdir():
            if not d.is_dir():
                continue
            if d.name == "00000000-0000-0000-000000000000":
                continue
            room_id = d.name
            msgs, atts, nf = self._parse_room(d)
            raw_rooms.append((room_id, d, msgs, atts, nf))

        raw_rooms.sort(
            key=lambda r: r[2][-1]["time"] if r[2] else "0000-00-00 00:00:00",
            reverse=True,
        )

        for room_id, d, msgs, atts, nf in raw_rooms:
            name = self.room_names.get(room_id, room_id[:8] + "…")
            self.rooms[room_id] = {
                "name": name, "path": d, "msgs": msgs,
                "attachments": atts, "full_id": room_id,
                "nonformat": nf,
            }

        self._render_room_list()
        self._status_lbl.config(text=tr("共 {n} 个聊天室").format(n=len(self.rooms)))
        if self.rooms:
            if self._cur_room not in self.rooms:
                self._cur_room = next(iter(self.rooms))
            self._select_room(self._cur_room)

    def _parse_room(self, room_dir: Path) -> tuple[list[dict], list[Path], list[dict]]:
        msgs: list[dict] = []
        attachments: list[Path] = []
        nonformat: list[dict] = []

        for f in sorted(room_dir.iterdir()):
            if f.name.startswith("."):
                continue
            if f.suffix.lower() == ".txt":
                user_id = f.stem
                try:
                    lines = f.read_text("utf-8", errors="replace").splitlines()
                except Exception:
                    continue
                file_msgs = 0
                nf_lines: list[str] = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    if line == "# time | msg":
                        continue
                    if line.startswith("#") or " | " not in line:
                        nf_lines.append(line)
                        continue
                    ts, content = line.split(" | ", 1)
                    reply_ref: tuple[str, str] | None = None
                    m = REPLY_PAT.search(content)
                    if m:
                        reply_ref = (m.group(1), m.group(2).strip())
                        content = content[:m.start()]
                    msgs.append({
                        "user": user_id,
                        "time": ts,
                        "content": content,
                        "reply_ref": reply_ref,
                    })
                    file_msgs += 1
                if nf_lines and file_msgs:
                    nonformat.append({"file": f.name, "lines": nf_lines})
            else:
                attachments.append(f)

        msgs.sort(key=lambda m: m["time"])
        return msgs, attachments, nonformat

    def _render_room_list(self) -> None:
        for w in self._room_inner.winfo_children():
            w.destroy()
        self._room_cards.clear()

        for rid in self.rooms:
            room = self.rooms[rid]
            name = self.room_names.get(rid, rid[:16] + "…")
            cnt = len(room["msgs"])
            last_ts = ""
            if room["msgs"]:
                last_ts = room["msgs"][-1]["time"]

            card = tk.Frame(self._room_inner, bg="#ffffff", bd=0,
                            highlightthickness=1, highlightbackground="#e0e0e0",
                            cursor="hand2")
            card.pack(fill="x", padx=4, pady=(2, 2))

            name_lbl = tk.Label(card, text=name,
                                font=("Microsoft YaHei", 12, "bold"),
                                fg="#191919", bg="#ffffff", anchor="w",
                                justify="left", cursor="hand2")
            name_lbl.pack(fill="x", padx=(10, 10), pady=(8, 0))

            info_text = f"{cnt} 条信息"
            if last_ts:
                info_text += f"  ·  最后: {last_ts}"
            info_lbl = tk.Label(card, text=info_text,
                                font=("Microsoft YaHei", 8),
                                fg="#888", bg="#ffffff", anchor="w",
                                justify="left", cursor="hand2")
            info_lbl.pack(fill="x", padx=(10, 10), pady=(2, 8))

            self._room_cards[rid] = card

            for w in (card, name_lbl, info_lbl):
                w.bind("<Button-1>", lambda e, r=rid: self._select_room(r))
                w.bind("<Double-Button-1>", lambda e, r=rid: self._rename_room(r))

        self._bind_room_scroll()

    def _select_room(self, rid: str) -> None:
        for r, card in self._room_cards.items():
            if r == rid:
                card.configure(bg="#cce5ff", highlightbackground="#a0d0f0")
                for child in card.winfo_children():
                    child.configure(bg="#cce5ff")
            else:
                card.configure(bg="#ffffff", highlightbackground="#e0e0e0")
                for child in card.winfo_children():
                    child.configure(bg="#ffffff")
        self._cur_room = rid
        self._render_chat()

    def _rename_room(self, rid: str = "") -> None:
        if not rid:
            return
        old = self.room_names.get(rid, "")
        new = simpledialog.askstring(
            tr("重命名房间"), tr("输入自定义房间名:"),
            initialvalue=old, parent=self.top)
        if new and new.strip():
            self.room_names[rid] = new.strip()
        elif new is not None and not new.strip() and old:
            self.room_names.pop(rid, None)
        else:
            return
        self._save_cfg()
        self._render_room_list()
        self._select_room(rid)

    def _render_chat(self) -> None:
        for w in self._msg_frame.winfo_children():
            w.destroy()
        for w in self._attach_frame.winfo_children():
            w.destroy()

        if not self._cur_room or self._cur_room not in self.rooms:
            return

        room = self.rooms[self._cur_room]
        msgs = room["msgs"]
        atts = room["attachments"]

        if not msgs:
            tk.Label(self._msg_frame, text=tr("暂无消息"), bg="#f0f0f0",
                     fg="#999", font=("Microsoft YaHei", 12)).pack(pady=60)
        else:
            user_order: list[str] = []
            seen: set[str] = set()
            for m in msgs:
                u = m["user"]
                if u not in seen:
                    seen.add(u)
                    user_order.append(u)
            user_color: dict[str, tuple[str, str]] = {}
            for i, u in enumerate(user_order):
                user_color[u] = (
                    BUBBLE_COLORS[i % len(BUBBLE_COLORS)],
                    STRIP_COLORS[i % len(STRIP_COLORS)],
                )

            for m in msgs:
                u = m["user"]
                bg, strip = user_color[u]
                disp_name = self.user_names.get(u, u[:8] + "…")
                ts = m["time"]
                reply_ref = m.get("reply_ref")

                outer = tk.Frame(self._msg_frame, bg="#f0f0f0")
                outer.pack(fill="x", padx=12, pady=(4, 0))

                header = tk.Frame(outer, bg="#f0f0f0")
                header.pack(fill="x")

                name_lbl = tk.Label(
                    header, text=disp_name,
                    font=("Microsoft YaHei", 9, "bold"),
                    fg="#333", bg="#f0f0f0", cursor="hand2",
                )
                name_lbl.pack(side="left")
                name_lbl.bind("<Button-1>", lambda e, uid=u: self._rename_user(uid))

                time_lbl = tk.Label(
                    header, text=ts,
                    font=("Microsoft YaHei", 7), fg="#aaa", bg="#f0f0f0",
                )
                time_lbl.pack(side="left", padx=(6, 0))

                bubble = tk.Frame(
                    outer, bg=bg,
                    highlightbackground=strip,
                    highlightcolor=strip,
                    highlightthickness=2,
                    bd=0,
                )
                bubble.pack(anchor="w", padx=(0, 80), pady=(2, 0), fill="x")

                if reply_ref:
                    ref_uid, ref_text = reply_ref
                    ref_name = self.user_names.get(ref_uid, ref_uid[:7])
                    reply_frame = tk.Frame(bubble, bg=bg)
                    reply_frame.pack(fill="x", padx=10, pady=(6, 2))

                    tk.Label(
                        reply_frame, text="↩ ",
                        font=("Microsoft YaHei", 8),
                        fg="#6cc4f5", bg=bg,
                    ).pack(side="left")
                    tk.Label(
                        reply_frame, text=ref_name,
                        font=("Microsoft YaHei", 8, "bold"),
                        fg="#409eff", bg=bg,
                    ).pack(side="left")
                    tk.Label(
                        reply_frame, text=f"：{ref_text[:60]}{'…' if len(ref_text) > 60 else ''}",
                        font=("Microsoft YaHei", 8),
                        fg="#888", bg=bg,
                    ).pack(side="left")

                    sep = tk.Frame(bubble, bg="#e0e0e0", height=1)
                    sep.pack(fill="x", padx=10, pady=(3, 0))

                txt_content = m["content"]
                
                est = 0
                for line in (txt_content or "").split("\n"):
                    w = sum(13 if ord(c) > 127 else 7 for c in line)
                    est += max(1, -(-w // 550))
                dlines = max(1, est)
                txt = tk.Text(
                    bubble, font=("Microsoft YaHei", 10),
                    fg="#191919", bg=bg,
                    bd=0, highlightthickness=0,
                    wrap="char", relief="flat",
                    height=dlines,
                    cursor="xterm", state="normal",
                )
                txt.pack(fill="x", anchor="w",
                         padx=10, pady=(2 if reply_ref else 6, 8))
                txt.insert("1.0", txt_content)

                txt.tag_configure("url", foreground="#2980b9", underline=True)

                def _url_enter(e, widget=txt):
                    widget.configure(cursor="hand2")

                def _url_leave(e, widget=txt):
                    widget.configure(cursor="xterm")

                txt.tag_bind("url", "<Enter>", _url_enter)
                txt.tag_bind("url", "<Leave>", _url_leave)

                for match in URL_PAT.finditer(txt_content):
                    url = match.group()
                    s = f"1.0 + {match.start()} chars"
                    e = f"1.0 + {match.end()} chars"
                    txt.tag_add("url", s, e)
                    txt.tag_bind("url", "<Button-1>",
                                 self._make_url_handler(url))

                txt.configure(state="disabled")

        if atts:
            tk.Label(self._attach_frame, text=tr("附件:"),
                     font=("Microsoft YaHei", 8, "bold"),
                     fg="#666", bg="#e0e0e0").pack(side="left", padx=(10, 6))
            for i, fp in enumerate(atts, 1):
                btn = tk.Button(
                    self._attach_frame, text=f"附件{i}: {fp.name}",
                    font=("Microsoft YaHei", 8),
                    bg="#f5f5f5", fg="#333", relief="groove", bd=1,
                    cursor="hand2",
                    command=lambda p=str(fp): _open_file(p),
                )
                btn.pack(side="left", padx=4, pady=4)
        else:
            tk.Label(self._attach_frame, text=tr("无附件"),
                     font=("Microsoft YaHei", 8),
                     fg="#bbb", bg="#e0e0e0").pack(side="left", padx=10)

        nf = room.get("nonformat") or []
        if nf:
            nf_count = sum(len(item["lines"]) for item in nf)
            tk.Button(
                self._attach_frame,
                text=tr("非格式文本 ({n})").format(n=nf_count),
                font=("Microsoft YaHei", 8),
                bg="#fff3e0", fg="#a0522d", relief="groove", bd=1,
                cursor="hand2",
                command=self._show_nonformat,
            ).pack(side="right", padx=4, pady=4)

        self._chat_canvas.yview_moveto(0.0)
        self._bind_scroll_recursive(self._msg_frame)

    
    def _show_nonformat(self) -> None:
        room = self.rooms.get(self._cur_room)
        if not room:
            return
        nf = room.get("nonformat") or []
        if not nf:
            mb.showinfo(tr("非格式文本"), tr("当前聊天室没有检测到非格式文本。"))
            return
        dlg = tk.Toplevel(self.top)
        dlg.title(tr("非格式文本") + f" - {room['name']}")
        dlg.transient(self.top)
        W, H = 560, 420
        dlg.geometry(f"{W}x{H}")
        dlg.update_idletasks()
        x = self.top.winfo_rootx() + max(0, (self.top.winfo_width() - W) // 2)
        y = self.top.winfo_rooty() + max(0, (self.top.winfo_height() - H) // 2)
        dlg.geometry(f"+{x}+{y}")
        txt = tk.Text(dlg, wrap="word", font=("Microsoft YaHei", 10))
        txt.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(dlg, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        for item in nf:
            txt.insert("end", f"===== {item['file']} =====\n")
            for ln in item["lines"]:
                txt.insert("end", ln + "\n")
            txt.insert("end", "\n")
        txt.configure(state="disabled")

    
    def _make_url_handler(self, url: str):
        return lambda e: self._handle_url(url)

    def _handle_url(self, url: str) -> None:
        dlg = tk.Toplevel(self.top)
        dlg.title(tr("链接"))
        dlg.geometry("420x140")
        dlg.resizable(False, False)
        dlg.transient(self.top)
        dlg.grab_set()
        self._center_window(dlg, 420, 140)

        tk.Label(dlg, text=url[:80], font=("Microsoft YaHei", 9),
                 fg="#2980b9", wraplength=380).pack(pady=(16, 12))

        btn_frame = tk.Frame(dlg)
        btn_frame.pack()

        def do_open():
            dlg.destroy()
            try:
                os.startfile(url)
            except Exception:
                subprocess.Popen(["start", "", url], shell=True)

        def do_copy():
            self.top.clipboard_clear()
            self.top.clipboard_append(url)
            dlg.destroy()

        tk.Button(btn_frame, text=tr("打开链接"), command=do_open,
                  font=("Microsoft YaHei", 10), padx=16).pack(side="left", padx=6)
        tk.Button(btn_frame, text=tr("复制链接"), command=do_copy,
                  font=("Microsoft YaHei", 10), padx=16).pack(side="left", padx=6)

    def _center_window(self, win, w, h):
        win.update_idletasks()
        pw = self.top.winfo_width()
        ph = self.top.winfo_height()
        rx = self.top.winfo_rootx()
        ry = self.top.winfo_rooty()
        x = rx + (pw - w) // 2
        y = ry + (ph - h) // 2
        win.geometry(f"+{x}+{y}")

    def _rename_user(self, uid: str) -> None:
        old = self.user_names.get(uid, "")
        new = simpledialog.askstring(
            tr("重命名用户"), tr("为 {uid}… 输入自定义名称:").format(uid=uid[:10]),
            initialvalue=old, parent=self.top)
        if new and new.strip():
            self.user_names[uid] = new.strip()
        elif new is not None and not new.strip() and old:
            self.user_names.pop(uid, None)
        else:
            return
        self._save_cfg()
        self._render_chat()


MORSE_MAP = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".",
    "F": "..-.", "G": "--.", "H": "....", "I": "..", "J": ".---",
    "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---",
    "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-",
    "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--",
    "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
    ".": ".-.-.-", ",": "--..--", "?": "..--..", "'": ".----.",
    "!": "-.-.--", "/": "-..-.", "(": "-.--.", ")": "-.--.-",
    "&": ".-...", ":": "---...", ";": "-.-.-.", "=": "-...-",
    "+": ".-.-.", "-": "-....-", "_": "..--.-", '"': ".-..-.",
    "$": "...-..-", "@": ".--.-.",
}
MORSE_REV = {v: k for k, v in MORSE_MAP.items()}


def _caesar_shift(text: str, shift: int) -> str:
    out = []
    for ch in text:
        if "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 + shift) % 26 + 65))
        elif "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 + shift) % 26 + 97))
        else:
            out.append(ch)
    return "".join(out)


def _caesar_enc(text: str, keys: list[str]) -> str:
    try:
        shift = int(keys[0].strip() or "0") % 26
    except ValueError:
        raise ValueError(tr("位移必须是整数"))
    return _caesar_shift(text, shift)


def _caesar_dec(text: str, keys: list[str]) -> str:
    try:
        shift = int(keys[0].strip() or "0") % 26
    except ValueError:
        raise ValueError(tr("位移必须是整数"))
    return _caesar_shift(text, -shift)


def _vigenere_ks(key: str) -> list[int]:
    if key.isdigit():
        return [int(c) for c in key]
    return [ord(c) - 65 for c in key.upper() if "A" <= c <= "Z"]


def _vigenere_enc(text: str, keys: list[str]) -> str:
    key = keys[0]
    ks = _vigenere_ks(key)
    if not ks:
        raise ValueError(tr("密钥必须包含字母或数字"))
    out = []
    ki = 0
    for ch in text:
        if "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 + ks[ki % len(ks)]) % 26 + 65))
            ki += 1
        elif "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 + ks[ki % len(ks)]) % 26 + 97))
            ki += 1
        else:
            out.append(ch)
    return "".join(out)


def _vigenere_dec(text: str, keys: list[str]) -> str:
    key = keys[0]
    ks = _vigenere_ks(key)
    if not ks:
        raise ValueError(tr("密钥必须包含字母或数字"))
    out = []
    ki = 0
    for ch in text:
        if "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 - ks[ki % len(ks)]) % 26 + 65))
            ki += 1
        elif "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 - ks[ki % len(ks)]) % 26 + 97))
            ki += 1
        else:
            out.append(ch)
    return "".join(out)


def _atbash(text: str, keys: list[str]) -> str:
    out = []
    for ch in text:
        if "A" <= ch <= "Z":
            out.append(chr(ord("Z") - (ord(ch) - ord("A"))))
        elif "a" <= ch <= "z":
            out.append(chr(ord("z") - (ord(ch) - ord("a"))))
        else:
            out.append(ch)
    return "".join(out)


def _a1z26_enc(text: str, keys: list[str]) -> str:
    parts = []
    for ch in text.upper():
        if "A" <= ch <= "Z":
            parts.append(str(ord(ch) - 64))
    return "-".join(parts)


def _a1z26_dec(text: str, keys: list[str]) -> str:
    parts = [p for p in re.split(r"[\s,，、;；-]+", text.strip()) if p]
    if not parts:
        raise ValueError(tr("没有可解析的数字"))
    out = []
    for p in parts:
        try:
            n = int(p)
        except ValueError:
            raise ValueError(tr("无法解析的数字：{p}").format(p=p))
        if n < 1 or n > 26:
            raise ValueError(tr("数字必须在 1-26 之间：{n}").format(n=n))
        out.append(chr(64 + n))
    return "".join(out)


def _keyword_alphabet(key: str) -> str:
    seen: list[str] = []
    for ch in key.upper():
        if "A" <= ch <= "Z" and ch not in seen:
            seen.append(ch)
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if ch not in seen:
            seen.append(ch)
    return "".join(seen)


def _keyword_sub(text: str, keys: list[str], decode: bool) -> str:
    key = keys[0]
    if not key:
        raise ValueError(tr("请输入密钥"))
    alph = _keyword_alphabet(key)
    table: dict[str, str] = {}
    if decode:
        for i, ch in enumerate(alph):
            table[ch] = chr(65 + i)
    else:
        for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            table[ch] = alph[i]
    out = []
    for ch in text:
        u = ch.upper()
        if "A" <= u <= "Z":
            mapped = table.get(u, u)
            out.append(mapped.lower() if ch.islower() else mapped)
        else:
            out.append(ch)
    return "".join(out)


def _keyword_enc(text: str, keys: list[str]) -> str:
    return _keyword_sub(text, keys, False)


def _keyword_dec(text: str, keys: list[str]) -> str:
    return _keyword_sub(text, keys, True)


def _simple_alphabet(keys: list[str]) -> str:
    alph = "".join(ch for ch in keys[0].upper() if "A" <= ch <= "Z")
    if len(alph) != 26:
        raise ValueError(tr("替换字母表必须恰好包含 26 个不重复字母"))
    return alph


def _simple_sub(text: str, keys: list[str], decode: bool) -> str:
    alph = _simple_alphabet(keys)
    table: dict[str, str] = {}
    if decode:
        for i, ch in enumerate(alph):
            table[ch] = chr(65 + i)
    else:
        for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            table[ch] = alph[i]
    out = []
    for ch in text:
        u = ch.upper()
        if "A" <= u <= "Z":
            mapped = table.get(u, u)
            out.append(mapped.lower() if ch.islower() else mapped)
        else:
            out.append(ch)
    return "".join(out)


def _simple_enc(text: str, keys: list[str]) -> str:
    return _simple_sub(text, keys, False)


def _simple_dec(text: str, keys: list[str]) -> str:
    return _simple_sub(text, keys, True)


def _baconian_enc(text: str, keys: list[str]) -> str:
    out = []
    for ch in text.upper():
        if "A" <= ch <= "Z":
            n = ord(ch) - 65
            bits = [(n >> (4 - i)) & 1 for i in range(5)]
            out.append("".join("A" if b == 0 else "B" for b in bits))
    return " ".join(out)


def _baconian_dec(text: str, keys: list[str]) -> str:
    clean = "".join(
        ch for ch in text.upper().replace("0", "A").replace("1", "B")
        if ch in "AB")
    if not clean:
        raise ValueError(tr("没有可解析的培根码"))
    if len(clean) % 5:
        raise ValueError(tr("培根码长度必须是 5 的倍数"))
    out = []
    for i in range(0, len(clean), 5):
        g = clean[i:i + 5]
        n = 0
        for ch in g:
            n = (n << 1) | (1 if ch == "B" else 0)
        if n > 25:
            raise ValueError(tr("无效的培根码：{g}").format(g=g))
        out.append(chr(65 + n))
    return "".join(out)


_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
_BASE91_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!#$%&()*+,./:;<=>?@[]^_`{|}~\""


def _base58_encode(data: bytes) -> str:
    n = int.from_bytes(data, "big")
    out = []
    while n:
        n, r = divmod(n, 58)
        out.append(_BASE58_ALPHABET[r])
    pad = 0
    for b in data:
        if b == 0:
            pad += 1
        else:
            break
    return "1" * pad + "".join(reversed(out))


def _base58_decode(text: str) -> bytes:
    n = 0
    for ch in text:
        idx = _BASE58_ALPHABET.find(ch)
        if idx < 0:
            raise ValueError(tr("无效的 Base58 字符：{c}").format(c=ch))
        n = n * 58 + idx
    pad = 0
    for ch in text:
        if ch == "1":
            pad += 1
        else:
            break
    body = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    return b"\x00" * pad + body


def _base62_encode(data: bytes) -> str:
    n = int.from_bytes(data, "big")
    if n == 0:
        return "0" * len(data)
    out = []
    while n:
        n, r = divmod(n, 62)
        out.append(_BASE62_ALPHABET[r])
    pad = 0
    for b in data:
        if b == 0:
            pad += 1
        else:
            break
    return "0" * pad + "".join(reversed(out))


def _base62_decode(text: str) -> bytes:
    n = 0
    for ch in text:
        idx = _BASE62_ALPHABET.find(ch)
        if idx < 0:
            raise ValueError(tr("无效的 Base62 字符：{c}").format(c=ch))
        n = n * 62 + idx
    pad = 0
    for ch in text:
        if ch == "0":
            pad += 1
        else:
            break
    body = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    return b"\x00" * pad + body


def _base91_encode(data: bytes) -> str:
    b = 0
    n = 0
    out = []
    for byte in data:
        b |= byte << n
        n += 8
        if n > 13:
            v = b & 8191
            if v > 88:
                b >>= 13
                n -= 13
            else:
                v = b & 16383
                b >>= 14
                n -= 14
            out.append(_BASE91_ALPHABET[v % 91])
            out.append(_BASE91_ALPHABET[v // 91])
    if n:
        out.append(_BASE91_ALPHABET[b % 91])
        if n > 7 or b > 90:
            out.append(_BASE91_ALPHABET[b // 91])
    return "".join(out)


def _base91_decode(text: str) -> bytes:
    v = -1
    b = 0
    n = 0
    out = bytearray()
    for ch in text:
        c = _BASE91_ALPHABET.find(ch)
        if c < 0:
            raise ValueError(tr("无效的 Base91 字符：{c}").format(c=ch))
        if v < 0:
            v = c
        else:
            v += c * 91
            b |= v << n
            n += 13 if (v & 8191) > 88 else 14
            while n > 7:
                out.append(b & 255)
                b >>= 8
                n -= 8
            v = -1
    if v != -1:
        out.append((b | v << n) & 255)
    return bytes(out)


def _base_encode(text: str, keys: list[str]) -> str:
    name = keys[0].upper()
    data = text.encode("utf-8")
    if name == "BASE64":
        return base64.b64encode(data).decode("ascii")
    if name == "BASE58":
        return _base58_encode(data)
    if name == "BASE62":
        return _base62_encode(data)
    if name == "BASE85":
        return base64.a85encode(data, adobe=False).decode("ascii")
    if name == "BASE91":
        return _base91_encode(data)
    raise ValueError(tr("不支持的编码：{e}").format(e=name))


def _base_decode(text: str, keys: list[str]) -> str:
    name = keys[0].upper()
    try:
        if name == "BASE64":
            raw = base64.b64decode(text.encode("ascii"), validate=False)
        elif name == "BASE58":
            raw = _base58_decode(text.strip())
        elif name == "BASE62":
            raw = _base62_decode(text.strip())
        elif name == "BASE85":
            t = text.strip()
            if t.startswith("<~") and t.endswith("~>"):
                t = t[2:-2]
            raw = base64.a85decode(t.encode("ascii"), adobe=False)
        elif name == "BASE91":
            raw = _base91_decode(text.strip())
        else:
            raise ValueError(tr("不支持的编码：{e}").format(e=name))
        return raw.decode("utf-8")
    except ValueError:
        raise
    except Exception:
        raise ValueError(tr("解码失败，请检查输入内容和编码类型"))


def _morse_enc(text: str, keys: list[str]) -> str:
    words = []
    for w in text.upper().split():
        codes = [MORSE_MAP[c] for c in w if c in MORSE_MAP]
        if codes:
            words.append(" ".join(codes))
    return " / ".join(words)


def _morse_dec(text: str, keys: list[str]) -> str:
    words = []
    for w in text.replace("／", "/").split("/"):
        chars = [MORSE_REV[c] for c in w.split() if c in MORSE_REV]
        if chars:
            words.append("".join(chars))
    return " ".join(words)


def _sha256(text: str, keys: list[str]) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _ascii_enc(text: str, keys: list[str]) -> str:
    return " ".join(str(ord(c)) for c in text)


def _ascii_dec(text: str, keys: list[str]) -> str:
    parts = [p for p in re.split(r"[\s,，、;；]+", text.strip()) if p]
    if not parts:
        raise ValueError(tr("没有可解析的数字"))
    out = []
    for p in parts:
        try:
            n = int(p, 0)
        except ValueError:
            raise ValueError(tr("无法解析的数字：{p}").format(p=p))
        if n < 0 or n > 0x10FFFF:
            raise ValueError(tr("超出 Unicode 范围：{n}").format(n=n))
        out.append(chr(n))
    return "".join(out)


_RADIX_DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _radix_convert(text: str, src: int, dst: int) -> str:
    text = text.strip()
    if not text:
        raise ValueError(tr("请输入数字"))
    try:
        n = int(text, src)
    except ValueError:
        raise ValueError(tr("无法按 {n} 进制解析输入").format(n=src))
    neg = n < 0
    n = abs(n)
    if n == 0:
        return "0"
    out = []
    while n:
        out.append(_RADIX_DIGITS[n % dst])
        n //= dst
    s = "".join(reversed(out))
    return ("-" if neg else "") + s


def _radix_enc(text: str, keys: list[str]) -> str:
    try:
        src = int(keys[0] or "10")
        dst = int(keys[1] or "16")
    except ValueError:
        raise ValueError(tr("进制必须是整数"))
    if not (2 <= src <= 36) or not (2 <= dst <= 36):
        raise ValueError(tr("进制必须在 2-36 之间"))
    return _radix_convert(text, src, dst)


def _radix_dec(text: str, keys: list[str]) -> str:
    try:
        src = int(keys[0] or "10")
        dst = int(keys[1] or "16")
    except ValueError:
        raise ValueError(tr("进制必须是整数"))
    if not (2 <= src <= 36) or not (2 <= dst <= 36):
        raise ValueError(tr("进制必须在 2-36 之间"))
    return _radix_convert(text, dst, src)


def _enc_convert(text: str, src_enc: str, dst_enc: str) -> str:
    try:
        raw = text.encode(src_enc)
        return raw.decode(dst_enc)
    except Exception as e:
        raise ValueError(tr("转换失败：{e}").format(e=e))


def _enc_convert_enc(text: str, keys: list[str]) -> str:
    return _enc_convert(text, keys[0], keys[1])


def _enc_convert_dec(text: str, keys: list[str]) -> str:
    return _enc_convert(text, keys[1], keys[0])


_ADFGVX_ALPH = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
_ADFGVX_SYMS = "ADFGVX"


def _adfgvx_grid(key: str) -> tuple[list[str], dict[str, tuple[int, int]]]:
    seen: list[str] = []
    for c in key.upper() + _ADFGVX_ALPH:
        if c in _ADFGVX_ALPH and c not in seen:
            seen.append(c)
    grid = [seen[i * 6:(i + 1) * 6] for i in range(6)]
    pos = {ch: (r, c) for r, row in enumerate(grid) for c, ch in enumerate(row)}
    return grid, pos


def _adfgvx_enc(text: str, keys: list[str]) -> str:
    key = keys[0].upper()
    sq = keys[1].upper()
    if not key:
        raise ValueError(tr("请输入密钥"))
    if not sq:
        raise ValueError(tr("请输入转置密钥"))
    grid, pos = _adfgvx_grid(key)
    n = len(sq)
    plain = "".join(ch for ch in text.upper() if ch in pos)
    if not plain:
        raise ValueError(tr("输入中没有任何可加密的字母或数字"))
    while (2 * len(plain)) % n:
        plain += "A"
    syms = "".join(_ADFGVX_SYMS[pos[c][0]] + _ADFGVX_SYMS[pos[c][1]] for c in plain)
    rows = [syms[i:i + n] for i in range(0, len(syms), n)]
    order = sorted(range(n), key=lambda i: sq[i])
    return "".join(rows[r][c] for c in order for r in range(len(rows)))


def _adfgvx_dec(text: str, keys: list[str]) -> str:
    key = keys[0].upper()
    sq = keys[1].upper()
    if not key:
        raise ValueError(tr("请输入密钥"))
    if not sq:
        raise ValueError(tr("请输入转置密钥"))
    grid, pos = _adfgvx_grid(key)
    rev = {_ADFGVX_SYMS[r] + _ADFGVX_SYMS[c]: grid[r][c]
           for r in range(6) for c in range(6)}
    n = len(sq)
    ct = "".join(ch for ch in text.upper() if ch in _ADFGVX_SYMS)
    if not ct or len(ct) % n:
        raise ValueError(tr("密文长度不是 KeySquare 长度的整数倍（请检查 KeySquare）"))
    rows_n = len(ct) // n
    order = sorted(range(n), key=lambda i: sq[i])
    cols: dict[int, str] = {}
    idx = 0
    for c in order:
        cols[c] = ct[idx:idx + rows_n]
        idx += rows_n
    syms = "".join(cols[c][r] for r in range(rows_n) for c in range(n))
    out = []
    for i in range(0, len(syms), 2):
        p = syms[i:i + 2]
        if len(p) < 2:
            break
        out.append(rev.get(p, "?"))
    return "".join(out).rstrip("A")


class CryptoPanel:
    def __init__(self, parent, toolbox):
        self.toolbox = toolbox
        self.cfg = toolbox.cfg
        self.frame = ttk.Frame(parent)
        self.top = self.frame.winfo_toplevel()
        self._build_ui()

    def _build_ui(self) -> None:
        nb = ttk.Notebook(self.frame)
        nb.pack(fill="both", expand=True, padx=6, pady=6)
        self.nb = nb
        self.matrix_panel = MatrixPanel(nb, self.toolbox)
        nb.add(self.matrix_panel.frame, text=tr("矩阵生成"))
        self._add_tab(nb, tr("ASCII"), tr("ASCII：字符与数字编码互相转换（支持 Unicode）。"),
                      None, _ascii_enc, _ascii_dec)
        self._add_tab(nb, tr("A1Z26"), tr("A1Z26：字母与数字互转（A=1 … Z=26）。"),
                      None, _a1z26_enc, _a1z26_dec)
        self._add_tab(nb, tr("进制转换"), tr("进制转换：2-36 进制互转（加密=源进制→目标进制，解密=反向）。"),
                      [(tr("源进制："), "10"), (tr("目标进制："), "16")], _radix_enc, _radix_dec)
        self._add_tab(nb, tr("BASE"), tr("BASE：支持 BASE64 / BASE58 / BASE62 / BASE85 / BASE91 互转。"),
                      [(tr("编码："), "BASE64", ["BASE64", "BASE58", "BASE62", "BASE85", "BASE91"])],
                      _base_encode, _base_decode)
        self._add_tab(nb, tr("摩斯电码"), tr("摩斯电码：字母/数字/常用符号与摩斯码互相转换，单词间用 / 分隔。"),
                      None, _morse_enc, _morse_dec)
        self._add_tab(nb, tr("培根密码"), tr("培根密码：字母转 5 位 A/B 编码（也接受 0/1）。"),
                      None, _baconian_enc, _baconian_dec)
        self._add_tab(nb, tr("凯撒密码"), tr("凯撒密码：把字母按位移量循环平移（0-25）。"),
                      [(tr("位移："), "3")], _caesar_enc, _caesar_dec)
        self._add_tab(nb, tr("埃特巴什码"), tr("埃特巴什码：字母表反转（A↔Z）。"),
                      None, _atbash, _atbash)
        self._add_tab(nb, tr("维吉尼亚密码"), tr("维吉尼亚密码：字母或数字密钥逐字符位移，纯数字密钥即为 Gronsfeld 密码。"),
                      [(tr("密钥："), "")], _vigenere_enc, _vigenere_dec)
        self._add_tab(nb, tr("关键字密码"), tr("关键字密码：关键字生成替换字母表。"),
                      [(tr("密钥："), "")], _keyword_enc, _keyword_dec)
        self._add_tab(nb, tr("简单换位"), tr("简单换位：输入 26 个不重复字母作为替换字母表。"),
                      [(tr("替换字母表："), "")], _simple_enc, _simple_dec)
        self._add_tab(nb, tr("ADFGVX密码"), tr("ADFGVX 密码：密钥生成 6×6 方阵，KeySquare 做列置换，解密自动去除填充。"),
                      [(tr("密钥："), ""), ("KeySquare：", "")], _adfgvx_enc, _adfgvx_dec)
        enc_opts = ["UTF-8", "GBK", "GB2312", "Big5", "Shift_JIS", "EUC-JP", "ISO-8859-1", "ASCII"]
        self._add_tab(nb, tr("编码转换"), tr("编码转换：按源编码取字节、再按目标编码显示（常用于乱码修复）。"),
                      [(tr("源编码："), "UTF-8", enc_opts), (tr("目标编码："), "GBK", enc_opts)],
                      _enc_convert_enc, _enc_convert_dec)
        self._add_tab(nb, tr("SHA-256"), tr("SHA-256：对输入文本计算 SHA-256 哈希（十六进制），不可逆。"),
                      None, _sha256, None)

    def _add_tab(self, nb, text, hint, key_specs, enc_fn, dec_fn):
        f = ttk.Frame(nb, padding=12)
        ttk.Label(f, text=hint, foreground="#666", wraplength=760,
                  justify="left").pack(anchor="w")
        key_vars: list[tk.StringVar] = []
        if key_specs:
            for spec in key_specs:
                row = ttk.Frame(f)
                row.pack(fill="x", pady=(6, 0))
                ttk.Label(row, text=tr(spec[0])).pack(side="left")
                var = tk.StringVar(value=spec[1])
                if len(spec) > 2 and spec[2]:
                    ttk.Combobox(row, textvariable=var, values=spec[2],
                                 state="readonly", width=34).pack(side="left", padx=6)
                else:
                    ttk.Entry(row, textvariable=var, width=48).pack(side="left", padx=6)
                key_vars.append(var)

        ttk.Label(f, text="输入：").pack(anchor="w", pady=(8, 0))
        inp = tk.Text(f, height=6, wrap="word", font=("Consolas", 10), undo=True)
        inp.pack(fill="both", expand=True)

        btns = ttk.Frame(f)
        btns.pack(fill="x", pady=6)
        if dec_fn is None:
            ttk.Button(btns, text=tr("计算"), width=8,
                       command=lambda: self._run(inp, out, key_vars, enc_fn)).pack(side="left")
        else:
            ttk.Button(btns, text=tr("加密"), width=8,
                       command=lambda: self._run(inp, out, key_vars, enc_fn)).pack(side="left")
            ttk.Button(btns, text=tr("解密"), width=8,
                       command=lambda: self._run(inp, out, key_vars, dec_fn)).pack(side="left", padx=6)
        ttk.Button(btns, text=tr("复制结果"), width=10,
                   command=lambda: self._copy_out(out)).pack(side="left")
        ttk.Button(btns, text=tr("清空"), width=8,
                   command=lambda: (inp.delete("1.0", "end"), out.delete("1.0", "end"))).pack(side="left", padx=6)

        ttk.Label(f, text="输出：").pack(anchor="w")
        out = tk.Text(f, height=6, wrap="word", font=("Consolas", 10))
        out.pack(fill="both", expand=True)

        nb.add(f, text=text)
        return inp, out, key_vars

    def _run(self, inp, out, key_vars, fn) -> None:
        text = inp.get("1.0", "end-1c")
        keys = [v.get() for v in key_vars]
        try:
            result = fn(text, keys)
        except ValueError as e:
            mb.showerror(tr("错误"), str(e))
            return
        except Exception as e:
            mb.showerror(tr("错误"), tr("操作失败：{e}").format(e=e))
            return
        out.delete("1.0", "end")
        out.insert("1.0", result)

    def _copy_out(self, out) -> None:
        s = out.get("1.0", "end-1c")
        if not s:
            return
        self.top.clipboard_clear()
        self.top.clipboard_append(s)


_MATRIX_WEIGHTS = (1, 3, 7, 9)


def _matrix_layer_path(
    maps: int,
    size: int,
    kernel: int,
    count: int,
    *,
    partial: bool = False,
) -> list[int]:
    start = (maps - 1) % 7
    direction = 1 if size % 2 == 0 else -1
    cycle = [(start + direction * index * kernel) % 7 for index in range(7)]
    if partial:
        return [cycle[index] for index in (0, 2, 4)]
    return cycle[:count]


_MATRIX_PATHS = (
    _matrix_layer_path(6, 28, 5, 3),
    _matrix_layer_path(6, 14, 2, 3),
    _matrix_layer_path(16, 10, 5, 3, partial=True),
    _matrix_layer_path(16, 5, 2, 3),
    _matrix_layer_path(120, 1, 5, 5),
)


def _matrix_checksum(payload: str) -> int:
    total = sum(
        int(digit) * _MATRIX_WEIGHTS[index % len(_MATRIX_WEIGHTS)]
        for index, digit in enumerate(payload)
    )
    return (-total) % 10


def _matrix_hamming74(value: int) -> list[int]:
    if not 0 <= value <= 9:
        raise ValueError("RBF class must be between 0 and 9")
    d1 = (value >> 3) & 1
    d2 = (value >> 2) & 1
    d3 = (value >> 1) & 1
    d4 = value & 1
    p1 = d1 ^ d2 ^ d4
    p2 = d1 ^ d3 ^ d4
    p3 = d2 ^ d3 ^ d4
    return [p1, p2, d1, p3, d2, d3, d4]


_MATRIX_RBF_CODES = tuple(_matrix_hamming74(value) for value in range(10))


def _matrix_encode(
    ip: str,
    port: int,
    *,
    revision: int = 1,
    decoy_key: str = "726791",
) -> list[list[int]]:
    octets = list(IPv4Address(ip).packed)
    if not 0 <= port <= 65_535:
        raise ValueError("Port must fit in five decimal digits")
    fields = [
        *(f"{octet:03d}" for octet in octets),
        f"{port:05d}",
    ]
    payload = "".join(fields)
    random = Random(f"{decoy_key}|{revision}|{ip}|{port}")
    matrix = [[random.randrange(10) for _ in range(7)] for _ in range(7)]
    for row, (columns, field) in enumerate(zip(_MATRIX_PATHS, fields)):
        for column, digit in zip(columns, field):
            matrix[row][column] = int(digit)
    check = _matrix_checksum(payload)
    matrix[5] = _matrix_hamming74(check)
    matrix[6][(10 - 1) % 7] = check
    return matrix


def _matrix_decode(matrix: Sequence[Sequence[int]]) -> dict[str, object]:
    if len(matrix) != 7 or any(len(row) != 7 for row in matrix):
        raise ValueError("Matrix must be exactly 7×7")
    fields = [
        "".join(str(matrix[row][column]) for column in columns)
        for row, columns in enumerate(_MATRIX_PATHS)
    ]
    octets = [int(field) for field in fields[:4]]
    port = int(fields[4])
    payload = "".join(fields)
    expected_check = _matrix_checksum(payload)
    f6 = list(matrix[5])
    if any(bit not in (0, 1) for bit in f6):
        raise ValueError("F6 row must contain only zeroes and ones")
    distances = [
        sum(actual != target for actual, target in zip(f6, code))
        for code in _MATRIX_RBF_CODES
    ]
    nearest_distance = min(distances)
    nearest_classes = [
        value
        for value, distance in enumerate(distances)
        if distance == nearest_distance
    ]
    rbf_class = nearest_classes[0] if len(nearest_classes) == 1 else None
    stored_class = matrix[6][(10 - 1) % 7]
    ranges_valid = all(0 <= octet <= 255 for octet in octets) and 0 <= port <= 65_535
    checksum_valid = rbf_class == expected_check and stored_class == expected_check
    return {
        "endpoint": f"{'.'.join(map(str, octets))}:{port}",
        "octets": octets,
        "port": port,
        "checksum": expected_check,
        "rbf_class": rbf_class,
        "rbf_distance": nearest_distance,
        "valid": ranges_valid and checksum_valid,
    }


def _matrix_transpose(matrix: list[list[int]]) -> list[list[int]]:
    if not matrix or any(len(row) != len(matrix) for row in matrix):
        raise ValueError("Matrix must be non-empty and square")
    return [list(column) for column in zip(*matrix)]


class MatrixPanel:
    def __init__(self, parent, toolbox):
        self.toolbox = toolbox
        self.cfg = toolbox.cfg
        self.frame = ttk.Frame(parent)
        self.top = self.frame.winfo_toplevel()
        self._build_ui()

    def _build_ui(self) -> None:
        pad = ttk.Frame(self.frame, padding=12)
        pad.pack(fill="both", expand=True)

        ttk.Label(pad, text=tr("把 IP 与端口编码为 7×7 谜题矩阵（含干扰数据），也可解码还原与转置。"),
                  foreground="#666").pack(anchor="w")

        row1 = ttk.Frame(pad)
        row1.pack(fill="x", pady=(8, 6))
        ttk.Label(row1, text=tr("IP 地址：")).pack(side="left")
        self.ip_var = tk.StringVar(value="")
        ttk.Entry(row1, textvariable=self.ip_var, width=16).pack(side="left", padx=2)
        ttk.Label(row1, text=tr("端口：")).pack(side="left", padx=(8, 0))
        self.port_var = tk.StringVar(value="7573")
        ttk.Entry(row1, textvariable=self.port_var, width=7).pack(side="left", padx=2)
        ttk.Label(row1, text=tr("修订：")).pack(side="left", padx=(8, 0))
        self.rev_var = tk.StringVar(value="1")
        ttk.Entry(row1, textvariable=self.rev_var, width=5).pack(side="left", padx=2)
        ttk.Label(row1, text=tr("干扰密钥：")).pack(side="left", padx=(8, 0))
        self.key_var = tk.StringVar(value="726791")
        ttk.Entry(row1, textvariable=self.key_var, width=14).pack(side="left", padx=2)

        row2 = ttk.Frame(pad)
        row2.pack(fill="x", pady=(0, 8))
        ttk.Button(row2, text=tr("生成矩阵"), command=self._generate).pack(side="left")
        ttk.Button(row2, text=tr("解码"), command=self._decode).pack(side="left", padx=6)
        ttk.Button(row2, text=tr("转置"), command=self._transpose).pack(side="left")
        ttk.Button(row2, text=tr("清空"), command=self._clear).pack(side="left", padx=6)

        grid_frame = ttk.Frame(pad)
        grid_frame.pack(fill="both", expand=True)
        self.cells: list[list[tk.StringVar]] = []
        for r in range(7):
            row_vars: list[tk.StringVar] = []
            for c in range(7):
                var = tk.StringVar(value="")
                ttk.Entry(
                    grid_frame, textvariable=var, width=3, justify="center",
                    font=("Consolas", 12),
                ).grid(row=r, column=c, padx=1, pady=1)
                row_vars.append(var)
            self.cells.append(row_vars)

        self.result_lbl = ttk.Label(pad, text="", foreground="#333", wraplength=760)
        self.result_lbl.pack(anchor="w", pady=(8, 0))

    def _read_matrix(self) -> list[list[int]]:
        matrix: list[list[int]] = []
        for row in self.cells:
            r: list[int] = []
            for var in row:
                v = var.get().strip()
                if not (v.isdigit() and len(v) == 1):
                    raise ValueError(tr("矩阵每个格子必须填 0-9 的一位数字"))
                r.append(int(v))
            matrix.append(r)
        return matrix

    def _write_matrix(self, matrix: list[list[int]]) -> None:
        for r in range(7):
            for c in range(7):
                self.cells[r][c].set(str(matrix[r][c]))

    def _generate(self) -> None:
        try:
            ip = self.ip_var.get().strip()
            port = int(self.port_var.get().strip())
            revision = int(self.rev_var.get().strip() or "1")
            decoy_key = self.key_var.get().strip() or "726791"
            matrix = _matrix_encode(ip, port, revision=revision, decoy_key=decoy_key)
        except Exception as e:
            mb.showerror(tr("错误"), str(e))
            return
        self._write_matrix(matrix)
        self.result_lbl.config(text=tr("已生成 7×7 矩阵。"), foreground="#333")

    def _decode(self) -> None:
        try:
            info = _matrix_decode(self._read_matrix())
        except Exception as e:
            mb.showerror(tr("错误"), str(e))
            return
        ok = bool(info["valid"])
        rbf = (str(info["rbf_class"]) if info["rbf_class"] is not None
               else tr("不确定"))
        txt = (
            tr("端点：") + str(info["endpoint"]) + "\n"
            + tr("校验和：") + str(info["checksum"])
            + f"  |  {tr('RBF：')}{rbf} ({tr('距离')} {info['rbf_distance']})\n"
            + (tr("校验结果：有效") if ok else tr("校验结果：无效"))
        )
        self.result_lbl.config(
            text=txt, foreground=("#1a7f37" if ok else "#c42b1c"))

    def _transpose(self) -> None:
        try:
            matrix = _matrix_transpose(self._read_matrix())
        except Exception as e:
            mb.showerror(tr("错误"), str(e))
            return
        self._write_matrix(matrix)

    def _clear(self) -> None:
        for row in self.cells:
            for var in row:
                var.set("")
        self.result_lbl.config(text="")


class SettingsPanel:
    def __init__(self, parent, toolbox):
        self.toolbox = toolbox
        self.cfg = toolbox.cfg
        self.frame = ttk.Frame(parent)
        self.top = self.frame.winfo_toplevel()
        self._build_ui()

    def _build_ui(self) -> None:
        pad = ttk.Frame(self.frame, padding=24)
        pad.pack(fill="both", expand=True)

        dev_lbl = ttk.Label(
            pad, text=tr("开发者：") + "Rosmontis220",
            foreground="#2980b9", cursor="hand2")
        dev_lbl.pack(side="bottom", pady=(0, 12))
        dev_lbl.bind(
            "<Button-1>",
            lambda e: _open_file("https://github.com/Rosmontis220/cfms-toolbox"))

        ttk.Label(pad, text="语言 / Language / 言語：",
                  font=("Microsoft YaHei", 11, "bold")).pack(anchor="w")
        lang_row = ttk.Frame(pad)
        lang_row.pack(fill="x", pady=(6, 0))
        self.lang_var = tk.StringVar(value=LANG_NAMES.get(LANG, "中文"))
        ttk.Combobox(
            lang_row, textvariable=self.lang_var, state="readonly", width=16,
            values=list(LANG_DISPLAY.keys()),
        ).pack(side="left")
        ttk.Button(lang_row, text=tr("应用"), width=8,
                   command=self._apply_language).pack(side="left", padx=8)

        ttk.Label(pad, text=tr("切换语言后界面将自动重建，当前页签会保留。"),
                  foreground="#888").pack(anchor="w", pady=(4, 0))

        ttk.Label(pad, text=tr("参考仓库："),
                  font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", pady=(16, 0))
        repo_row1 = ttk.Frame(pad)
        repo_row1.pack(fill="x", pady=(6, 0))
        ttk.Label(repo_row1, text=tr("服务端："), foreground="#555").pack(side="left")
        srv_lbl = ttk.Label(repo_row1, text="https://github.com/Creeper19472/cfms_2",
                            foreground="#2980b9", cursor="hand2")
        srv_lbl.pack(side="left")
        srv_lbl.bind(
            "<Button-1>",
            lambda e: _open_file("https://github.com/Creeper19472/cfms_2"))
        repo_row2 = ttk.Frame(pad)
        repo_row2.pack(fill="x", pady=(4, 0))
        ttk.Label(repo_row2, text=tr("客户端："), foreground="#555").pack(side="left")
        cli_lbl = ttk.Label(repo_row2, text="https://github.com/Creeper19472/cfms_client_next",
                            foreground="#2980b9", cursor="hand2")
        cli_lbl.pack(side="left")
        cli_lbl.bind(
            "<Button-1>",
            lambda e: _open_file("https://github.com/Creeper19472/cfms_client_next"))
    def _apply_language(self) -> None:
        code = LANG_DISPLAY.get(self.lang_var.get(), "zh")
        self.toolbox.set_language(code)


class ToolboxApp:
    def __init__(self):
        self.root = tk.Tk()
        self.cfg = load_config()
        self.root.geometry("1280x760")
        self.root.minsize(960, 600)
        if SPECIAL:
            
            self._migrate_legacy_config()
        self.tray_icon = None
        self.tray_thread = None
        self._closing = False
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._set_window_icon()
        self._create_tray_icon()

    def _build_ui(self) -> None:
        for w in self.root.winfo_children():
            w.destroy()
        self.root.title(
            tr("CFMS工具箱") + f" v{APP_VERSION}"
            + (f" {VARIANT_NAME}" if VARIANT_NAME else ""))

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=6, pady=6)
        self.nb = nb

        self.download_panel = DownloadPanel(nb, self)
        self.view_panel = QuickViewPanel(nb, self)
        self.crypto_panel = CryptoPanel(nb, self)
        self.settings_panel = SettingsPanel(nb, self)

        if not self.view_panel.chatbox_path:
            cand = Path(str(self.cfg.get("output") or "")) / ".runtime" / "chatbox"
            if cand.is_dir():
                self.cfg["chatbox_path"] = str(cand)
                self.view_panel._load_cfg()
                self.view_panel._scan()

        nb.add(self.download_panel.frame, text=tr("下载文件"))
        nb.add(self.view_panel.frame, text=tr("聊天记录"))
        nb.add(self.crypto_panel.frame, text=tr("小工具"))
        nb.add(self.settings_panel.frame, text="⚙️" + tr("设置"))
        nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def set_language(self, code: str) -> None:
        if code == LANG:
            return
        set_lang(code)
        self.cfg["language"] = code
        self.save_config()
        cur = self.nb.index("current") if getattr(self, "nb", None) is not None else 0
        self._build_ui()
        try:
            self.nb.select(cur)
        except Exception:
            pass

    def save_config(self) -> None:
        save_config(self.cfg)

    def _migrate_legacy_config(self) -> None:
        
        fresh = not CONFIG_PATH.exists()
        legacy_dir = APP_DIR.parent / "cfms_downloader"
        try:
            if fresh:
                dl = legacy_dir / "cfms_downloader_settings.json"
                if dl.exists():
                    d = json.loads(dl.read_text("utf-8"))
                    for k in ("host", "port", "username", "password", "auto_refresh",
                              "interval", "proxy_type", "proxy_host", "proxy_port", "output"):
                        if d.get(k) not in (None, ""):
                            self.cfg[k] = d[k]
                vw = legacy_dir / "chatbox_viewer_config.json"
                if vw.exists():
                    v = json.loads(vw.read_text("utf-8"))
                    if v.get("chatbox_path"):
                        self.cfg["chatbox_path"] = v["chatbox_path"]
        except Exception:
            pass

        changed = False
        
        viewer_sources = [
            legacy_dir / "chatbox_viewer_config.json",
            legacy_dir / "dist" / "chatbox_viewer_config.json",
        ]
        override = not self.cfg.get("_legacy_viewer_migrated")
        try:
            for vw in viewer_sources:
                if not vw.exists():
                    continue
                v = json.loads(vw.read_text("utf-8"))
                if not isinstance(v, dict):
                    continue
                
                for rid, name in (v.get("room_names") or {}).items():
                    if name and (override or rid not in self.cfg["room_names"]):
                        self.cfg["room_names"][rid] = name
                        changed = True
                
                for uid, name in (v.get("user_names") or {}).items():
                    if name and (override or uid not in self.cfg["user_names"]):
                        self.cfg["user_names"][uid] = name
                        changed = True
                    
                    if name and uid not in self.cfg["decoded_ids"]:
                        self.cfg["decoded_ids"][uid] = name
                        changed = True
                if v.get("chatbox_path") and not self.cfg.get("chatbox_path"):
                    self.cfg["chatbox_path"] = v["chatbox_path"]
                    changed = True
        except Exception:
            pass
        if override:
            self.cfg["_legacy_viewer_migrated"] = 1
            changed = True

        
        try:
            for src, key in (
                (APP_DIR / "users.json", "user_names"),
                (APP_DIR / "rooms.json", "room_names"),
                (APP_DIR / "dates.json", "date_labels"),
            ):
                if not src.exists():
                    continue
                d = json.loads(src.read_text("utf-8"))
                if not isinstance(d, dict):
                    continue
                if key == "user_names":
                    for uid, info in d.items():
                        if not isinstance(info, dict):
                            continue
                        if info.get("name") and uid not in self.cfg["user_names"]:
                            self.cfg["user_names"][uid] = info["name"]
                            changed = True
                        if info.get("id") and uid not in self.cfg["decoded_ids"]:
                            self.cfg["decoded_ids"][uid] = info["id"]
                            changed = True
                elif key == "room_names":
                    for rid, name in d.items():
                        if name and rid not in self.cfg["room_names"]:
                            self.cfg["room_names"][rid] = name
                            changed = True
                elif key == "date_labels":
                    for date_str, label in d.items():
                        if label and date_str not in self.cfg["date_labels"]:
                            self.cfg["date_labels"][date_str] = label
                            changed = True
        except Exception:
            pass

        if changed:
            save_config(self.cfg)

    def _on_tab_changed(self, event=None) -> None:
        try:
            nb = event.widget
            sel = nb.nametowidget(nb.select())
            if sel is self.view_panel.frame:
                self.view_panel._scan()
        except Exception:
            pass

    
    def _set_window_icon(self) -> None:
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".ico", delete=False)
            tmp.write(_icon_bytes())
            tmp.close()
            self.root.iconbitmap(tmp.name)
            os.unlink(tmp.name)
        except Exception:
            pass

    def _create_tray_icon(self) -> None:
        if not TRAY_AVAILABLE:
            return
        try:
            image = Image.open(io.BytesIO(_icon_bytes())).resize((64, 64))
            menu = pystray.Menu(
                pystray.MenuItem(tr("显示窗口"), self._show_window, default=True),
                pystray.MenuItem(tr("退出"), self._quit_app),
            )
            tray_id = "cfms_toolbox" + ("_special" if SPECIAL else "_regular")
            self.tray_icon = pystray.Icon(tray_id, image, APP_TITLE, menu)
            self.tray_thread = threading.Thread(
                target=self.tray_icon.run, daemon=True)
            self.tray_thread.start()
        except Exception:
            self.tray_icon = None

    def _show_window(self) -> None:
        try:
            self.root.after(0, self._restore_window)
        except Exception:
            pass

    def _restore_window(self) -> None:
        self.root.deiconify()
        self.root.state("normal")
        self.root.lift()
        self.root.focus_force()

    def _quit_app(self) -> None:
        self._closing = True
        try:
            if self.tray_icon:
                self.tray_icon.stop()
        except Exception:
            pass
        try:
            self.root.after(0, self._force_close)
        except Exception:
            pass

    def _force_close(self) -> None:
        try:
            self.download_panel.shutdown()
        except Exception:
            pass
        try:
            self.view_panel._save_cfg()
        except Exception:
            pass
        save_config(self.cfg)
        self.root.destroy()

    def _on_close(self) -> None:
        if self._closing:
            return
        if TRAY_AVAILABLE and self.tray_icon is not None:
            
            self.root.withdraw()
            try:
                self.tray_icon.notify(
                    tr("程序已最小化到托盘，自动刷新仍在运行。"),
                    APP_TITLE)
            except Exception:
                pass
        else:
            self._quit_app()

    def _notify(self, title: str, message: str) -> None:
        try:
            if TRAY_AVAILABLE and self.tray_icon is not None:
                self.tray_icon.notify(f"{title}\n{message}", APP_TITLE)
        except Exception:
            pass


def main() -> None:
    app = ToolboxApp()
    app.root.mainloop()


if __name__ == "__main__":
    main()
