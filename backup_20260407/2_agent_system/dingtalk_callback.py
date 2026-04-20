#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
钉钉回调接收服务器

用于接收钉钉用户发送的消息，实现双向通信。
支持 HTTP 回调和 WebSocket 两种模式。

使用方法：
    python dingtalk_callback.py --port 8080
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import requests


# ==================== 配置 ====================

DEFAULT_PORT = 8080
CALLBACK_LOG_DIR = Path(__file__).resolve().parents[1] / "7_monitor_system" / "dingtalk_log"
CALLBACK_LOG_DIR.mkdir(parents=True, exist_ok=True)

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DingTalkCallback")


class DingTalkCallbackHandler(BaseHTTPRequestHandler):
    """钉钉回调 HTTP 请求处理器"""
    
    # 回调处理器实例（由外部设置）
    callback_server = None
    
    def do_GET(self):
        """处理 GET 请求（钉钉验证）"""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        # 钉钉验证参数
        signature = params.get('signature', [''])[0]
        timestamp = params.get('timestamp', [''])[0]
        nonce = params.get('nonce', [''])[0]
        
        if signature and timestamp and nonce:
            # 验证签名
            if self.callback_server and self.callback_server.verify_signature(
                signature, timestamp, nonce
            ):
                logger.info("钉钉验证成功")
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(timestamp.encode())
                return
        
        # 验证失败
        self.send_response(403)
        self.end_headers()
    
    def do_POST(self):
        """处理 POST 请求（接收消息）"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        # 获取签名头
        signature = self.headers.get('X-Ding-Signature', '')
        timestamp = self.headers.get('X-Ding-Timestamp', '')
        
        # 验证签名
        if self.callback_server and not self.callback_server.verify_signature(
            signature, timestamp, ''
        ):
            logger.warning("签名验证失败")
            self.send_response(403)
            self.end_headers()
            return
        
        try:
            # 解析消息
            message = json.loads(post_data.decode('utf-8'))
            logger.info(f"收到消息：{json.dumps(message, ensure_ascii=False)}")
            
            # 保存消息到文件
            self._save_message(message)
            
            # 处理消息
            if self.callback_server:
                self.callback_server.process_message(message)
            
            # 返回成功响应
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {"success": True}
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            logger.error(f"处理消息失败：{e}")
            self.send_response(500)
            self.end_headers()
    
    def _save_message(self, message: Dict[str, Any]) -> None:
        """保存消息到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = CALLBACK_LOG_DIR / f"message_{timestamp}.json"
        log_file.write_text(
            json.dumps(message, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    
    def log_message(self, format, *args):
        """重写日志方法"""
        logger.info("%s - %s" % (self.address_string(), format % args))


class DingTalkCallbackServer:
    """
    钉钉回调服务器
    
    功能：
    1. 接收钉钉回调消息
    2. 验证签名
    3. 解析并处理消息
    4. 调用指令处理器
    """
    
    def __init__(
        self,
        port: int = DEFAULT_PORT,
        app_key: str = "",
        app_secret: str = "",
        token: str = "",
        encoding_aes_key: str = "",
        instruction_handler: Optional[Callable] = None,
    ):
        self.port = port
        self.app_key = app_key
        self.app_secret = app_secret
        self.token = token  # 回调 Token
        self.encoding_aes_key = encoding_aes_key
        self.instruction_handler = instruction_handler  # 指令处理函数
        
        self._server = None
        self._thread = None
        self._running = False
        self._message_queue: List[Dict[str, Any]] = []
    
    def verify_signature(self, signature: str, timestamp: str, nonce: str) -> bool:
        """
        验证钉钉签名
        
        签名算法：
        signature = base64(hmac_sha256(token, timestamp + "\\n" + nonce))
        """
        if not self.token:
            logger.warning("未配置 Token，跳过签名验证")
            return True
        
        if not signature or not timestamp:
            return False
        
        # 计算期望的签名
        data = f"{timestamp}\n{nonce}"
        expected = base64.b64encode(
            hmac.new(
                self.token.encode(),
                data.encode(),
                hashlib.sha256
            ).digest()
        ).decode()
        
        return hmac.compare_digest(signature, expected)
    
    def decrypt_message(self, encrypted_data: str) -> Dict[str, Any]:
        """
        解密钉钉消息
        
        钉钉使用 AES/CBC/PKCS7Padding 加密
        """
        if not self.encoding_aes_key or not encrypted_data:
            return {}
        
        # TODO: 实现 AES 解密
        # 目前先处理未加密的消息
        logger.warning("消息已加密但未配置解密，返回空消息")
        return {}
    
    def process_message(self, message: Dict[str, Any]) -> None:
        """
        处理接收到的消息
        
        消息格式：
        {
            "msgtype": "text",
            "text": {
                "content": "/start"
            },
            "senderId": "123456",
            "senderNick": "张三",
            "conversationId": "789",
            "timestamp": 1234567890
        }
        """
        # 提取消息内容
        msg_type = message.get("msgtype", "text")
        
        if msg_type == "text":
            content = message.get("text", {}).get("content", "").strip()
            sender_id = message.get("senderId", "")
            sender_nick = message.get("senderNick", "未知用户")
            conversation_id = message.get("conversationId", "")
            
            logger.info(f"收到文本消息：{content} (发送者：{sender_nick})")
            
            # 检查是否是指令
            if content.startswith("/"):
                # 调用指令处理器
                if self.instruction_handler:
                    response = self.instruction_handler(content, sender_id, sender_nick)
                    
                    # 发送响应
                    if response:
                        self.send_response(response, conversation_id)
            else:
                # 普通消息，可以添加自动回复
                logger.info(f"普通消息，忽略：{content}")
        
        # 保存消息到队列
        self._message_queue.append({
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "processed": True,
        })
        
        # 限制队列大小
        if len(self._message_queue) > 100:
            self._message_queue = self._message_queue[-100:]
    
    def send_response(self, text: str, conversation_id: str = "") -> bool:
        """
        发送响应到钉钉
        
        使用钉钉 API 发送消息到指定会话
        """
        if not self.app_key or not self.app_secret:
            logger.warning("未配置 AppKey/AppSecret，无法发送响应")
            return False
        
        try:
            # 1. 获取 access_token
            token_url = "https://oapi.dingtalk.com/gettoken"
            token_params = {
                "appkey": self.app_key,
                "appsecret": self.app_secret,
            }
            token_resp = requests.get(token_url, params=token_params, timeout=10)
            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                logger.error(f"获取 access_token 失败：{token_data}")
                return False
            
            # 2. 发送消息
            send_url = f"https://oapi.dingtalk.com/robot/send?access_token={access_token}"
            payload = {
                "msgtype": "text",
                "text": {
                    "content": text
                }
            }
            
            resp = requests.post(send_url, json=payload, timeout=10)
            result = resp.json()
            
            if result.get("errcode") == 0:
                logger.info("响应发送成功")
                return True
            else:
                logger.error(f"响应发送失败：{result}")
                return False
                
        except Exception as e:
            logger.error(f"发送响应异常：{e}")
            return False
    
    def start(self) -> bool:
        """启动服务器"""
        try:
            # 创建 HTTP 服务器
            self._server = HTTPServer(('0.0.0.0', self.port), DingTalkCallbackHandler)
            DingTalkCallbackHandler.callback_server = self
            
            # 启动线程
            self._thread = threading.Thread(target=self._server.serve_forever)
            self._thread.daemon = True
            self._thread.start()
            
            self._running = True
            logger.info(f"钉钉回调服务器已启动，监听端口：{self.port}")
            logger.info(f"回调 URL 配置：http://你的服务器 IP:{self.port}/")
            
            return True
            
        except Exception as e:
            logger.error(f"启动服务器失败：{e}")
            return False
    
    def stop(self) -> None:
        """停止服务器"""
        if self._server:
            self._server.shutdown()
            self._server = None
        
        self._running = False
        logger.info("钉钉回调服务器已停止")
    
    def is_running(self) -> bool:
        """检查服务器是否运行中"""
        return self._running and self._thread is not None
    
    def get_message_queue(self) -> List[Dict[str, Any]]:
        """获取消息队列"""
        return self._message_queue.copy()


# ==================== 全局回调服务器实例 ====================

_callback_server: Optional[DingTalkCallbackServer] = None


def create_callback_server(
    port: int = DEFAULT_PORT,
    env: Optional[Dict[str, str]] = None,
    instruction_handler: Optional[Callable] = None,
) -> DingTalkCallbackServer:
    """
    创建回调服务器实例
    
    Args:
        port: 监听端口
        env: 环境变量字典
        instruction_handler: 指令处理函数
    
    Returns:
        DingTalkCallbackServer 实例
    """
    if env is None:
        env = dict(os.environ)
        # 尝试从.env 文件加载
        env_file = Path(__file__).resolve().parents[2] / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env[key.strip()] = value.strip().strip('"').strip("'")
    
    server = DingTalkCallbackServer(
        port=port,
        app_key=env.get("DINGTALK_APP_KEY", ""),
        app_secret=env.get("DINGTALK_APP_SECRET", ""),
        token=env.get("DINGTALK_TOKEN", ""),
        encoding_aes_key=env.get("DINGTALK_ENCODING_AES_KEY", ""),
        instruction_handler=instruction_handler,
    )
    
    return server


def start_callback_server(
    port: int = DEFAULT_PORT,
    env: Optional[Dict[str, str]] = None,
    instruction_handler: Optional[Callable] = None,
) -> bool:
    """
    启动回调服务器
    
    Args:
        port: 监听端口
        env: 环境变量字典
        instruction_handler: 指令处理函数
    
    Returns:
        启动是否成功
    """
    global _callback_server
    
    _callback_server = create_callback_server(port, env, instruction_handler)
    return _callback_server.start()


def stop_callback_server() -> None:
    """停止回调服务器"""
    global _callback_server
    
    if _callback_server:
        _callback_server.stop()
        _callback_server = None


def get_callback_server() -> Optional[DingTalkCallbackServer]:
    """获取回调服务器实例"""
    return _callback_server


# ==================== 命令行启动 ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="钉钉回调服务器")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="监听端口")
    args = parser.parse_args()
    
    print(f"正在启动钉钉回调服务器，监听端口：{args.port}")
    print("按 Ctrl+C 停止")
    
    # 创建并启动服务器
    server = create_callback_server(port=args.port)
    
    if server.start():
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n正在停止服务器...")
            server.stop()
    else:
        print("启动失败")