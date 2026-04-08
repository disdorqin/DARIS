#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DARIS v3.2 OpenClaw 全局调度主文件（交互式版本）

功能：
- 交互式启动（GPU/服务器选择、关键词输入、轮次设置）
- 钉钉机器人双向对接（告警推送 + 指令监听）
- 全流程工作流调度
- 告警分级推送
- 持久化记忆同步
- 最终报表生成

启动命令：python openclaw_main.py
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import hmac
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import yaml
from urllib.parse import parse_qsl, quote_plus, urlencode, urlparse, urlunparse

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# 导入路径解析模块、钉钉回调模块和阿里云连接器
from core.utils.path_resolver import resolve_first_existing, resolve_workspace_root
from dingtalk_callback import (
    DingTalkCallbackServer,
    create_callback_server,
    start_callback_server,
    stop_callback_server,
)
from aliyun_connector import AliyunConnector, create_connector_from_env


# ==================== 路径配置 ====================
ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = resolve_workspace_root(create=True)
CONFIG_PATH = resolve_first_existing(
    WORKSPACE_ROOT / "config" / "base" / "openclaw_config.yaml",
    WORKSPACE_ROOT / "config" / "openclaw_config.yaml",
    ROOT / "1_config" / "base" / "openclaw_config.yaml",
)
DINGTALK_CONFIG_PATH = resolve_first_existing(
    WORKSPACE_ROOT / "config" / "alert" / "dingtalk_config.yaml",
    WORKSPACE_ROOT / "config" / "dingtalk_config.yaml",
    ROOT / "1_config" / "alert" / "dingtalk_config.yaml",
)
STATE_PATH = WORKSPACE_ROOT / "logs" / "openclaw_state.json"
RUNNER_PATH = ROOT / "2_agent_system" / "1_research_manager" / "run.py"
MEMORY_DIR = WORKSPACE_ROOT / "memory"
SKILLS_LIBRARY = MEMORY_DIR / "skills_library.md"
REPORT_DIR = WORKSPACE_ROOT / "report"

# ==================== 钉钉回调配置 ====================
CALLBACK_PORT = 8080  # 回调服务器监听端口
CALLBACK_SERVER: Optional[DingTalkCallbackServer] = None

# ==================== 工作流状态 ====================
WORKFLOW_LOG: List[str] = []


def log_message(message: str) -> None:
    """记录日志并推送到钉钉"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    WORKFLOW_LOG.append(log_entry)
    print(log_entry)


# ==================== 钉钉指令定义 ====================
DINGTALK_COMMANDS = {
    "/start": {
        "description": "启动一轮完整的 DARIS 科研闭环工作流",
        "action": "start_workflow",
        "response_template": "🚀 DARIS 工作流已启动，当前环节：{stage}\n进度：{progress}",
    },
    "/pause": {
        "description": "暂停当前执行的工作流",
        "action": "pause_workflow",
        "response_template": "⏸️ 工作流已暂停\n当前进度快照：{progress}",
    },
    "/resume": {
        "description": "恢复暂停的工作流",
        "action": "resume_workflow",
        "response_template": "▶️ 工作流已恢复，继续执行",
    },
    "/rollback": {
        "description": "回滚到上一稳定版本",
        "action": "rollback_version",
        "response_template": "🔄 已回滚到版本：{version}\n回滚详情：{details}",
    },
    "/status": {
        "description": "查询当前项目执行状态",
        "action": "query_status",
        "response_template": "📊 当前状态\n环节：{stage}\n进度：{progress}\n资源使用：{resources}",
    },
    "/stop": {
        "description": "终止当前执行的工作流",
        "action": "stop_workflow",
        "response_template": "⏹️ 工作流已终止\n本轮完成内容：{summary}",
    },
    "/clean": {
        "description": "触发项目冗余文件自动清理",
        "action": "cleanup_files",
        "response_template": "🧹 清理完成\n清理清单：{list}\n空间占用：{space}",
    },
    "/help": {
        "description": "显示帮助信息",
        "action": "show_help",
        "response_template": "📖 DARIS 指令帮助\n{commands}",
    },
}


class DingTalkBot:
    """钉钉机器人双向对接模块"""
    
    def __init__(self, config_path: Path, env: Dict[str, str]):
        self.config = self._load_config(config_path)
        self.env = env
        self.webhook = (
            env.get("DINGTALK_WEBHOOK", "")
            or env.get("WEBHOOK_URL", "")
            or self.config.get("webhook", "")
            or self.config.get("webhook_url", "")
        ).strip()
        self.signature_secret = (
            env.get("DINGTALK_SECRET", "")
            or env.get("WEBHOOK_SECRET", "")
            or self.config.get("secret", "")
            or self.config.get("sign_secret", "")
        ).strip()
        self._last_message_time = 0
        self._message_interval = 1.0  # 消息间隔（秒）
    
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """加载钉钉配置"""
        if not config_path.exists():
            return {}
        return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    def _build_webhook_url(self) -> str:
        """如果配置了签名密钥，就给 webhook 自动追加 timestamp/sign。"""
        if not self.webhook:
            return ""
        if not self.signature_secret:
            return self.webhook

        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{self.signature_secret}"
        digest = hmac.new(
            self.signature_secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        sign = quote_plus(base64.b64encode(digest).decode("utf-8"))

        parsed = urlparse(self.webhook)
        query_params = dict(parse_qsl(parsed.query))
        query_params.update({"timestamp": timestamp, "sign": sign})
        return urlunparse(parsed._replace(query=urlencode(query_params)))
    
    def send_message(self, level: str, stage: str, action: str, result: str, duration: float = 0.0) -> bool:
        """
        发送钉钉消息
        
        Args:
            level: 告警级别（emergency/warning/notice）
            stage: 执行阶段
            action: 动作
            result: 结果
            duration: 耗时（秒）
        
        Returns:
            发送是否成功
        """
        if not self.webhook:
            return False
        
        # 限流
        current_time = time.time()
        if current_time - self._last_message_time < self._message_interval:
            time.sleep(self._message_interval - (current_time - self._last_message_time))
        
        template = self.config.get("message_template", {})
        body_tpl = template.get(
            "body",
            "[{level}] stage={stage} agent=openclaw action={action} result={result} duration={duration}s",
        )
        
        text = body_tpl.format(
            level=level.upper(),
            stage=stage,
            agent="openclaw_main",
            action=action,
            result=result,
            duration=round(duration, 2),
        )
        
        # 根据告警级别添加标记
        if level == "emergency":
            text = f"🚨 **紧急告警** 🚨\n{text}"
        elif level == "warning":
            text = f"⚠️ **预警** ⚠️\n{text}"
        elif level == "notice":
            text = f"📢 **通知** 📢\n{text}"
        
        payload = {
            "msgtype": "text",
            "text": {"content": text},
        }
        
        webhook = self._build_webhook_url()
        if not webhook:
            return False

        try:
            resp = requests.post(webhook, json=payload, timeout=20)
            self._last_message_time = time.time()
            return resp.status_code == 200
        except Exception:
            return False
    
    def send_workflow_start(self, request: str, rounds: int) -> bool:
        """发送工作流启动通知"""
        return self.send_message(
            level="notice",
            stage="workflow",
            action="start",
            result=f"请求：{request[:50]}..., 轮次：{rounds}",
            duration=0.0,
        )
    
    def send_workflow_complete(self, status: str, duration: float, summary: Dict[str, Any]) -> bool:
        """发送工作流完成通知"""
        return self.send_message(
            level="notice" if status == "success" else "emergency",
            stage="workflow",
            action="complete",
            result=f"状态：{status}, 耗时：{duration:.1f}s",
            duration=duration,
        )
    
    def send_stage_progress(self, stage: str, progress: str, details: str = "") -> bool:
        """发送阶段进度通知"""
        return self.send_message(
            level="notice",
            stage=stage,
            action="progress",
            result=f"进度：{progress}\n{details}" if details else f"进度：{progress}",
        )
    
    def send_alert(self, alert_type: str, message: str, details: str = "") -> bool:
        """
        发送告警消息
        
        Args:
            alert_type: 告警类型（emergency/warning）
            message: 告警消息
            details: 详细信息
        """
        return self.send_message(
            level=alert_type,
            stage="alert",
            action="alert",
            result=f"{message}\n{details}" if details else message,
        )
    
    def send_command_response(self, command: str, response: str) -> bool:
        """发送指令响应"""
        return self.send_message(
            level="notice",
            stage="command",
            action=command,
            result=response,
        )


class OpenClawState:
    """OpenClaw 状态管理"""
    
    def __init__(self, state_path: Path):
        self.state_path = state_path
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """加载状态"""
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "status": "idle",
            "current_stage": None,
            "progress": 0,
            "started_at": None,
            "paused_at": None,
            "last_version": None,
        }
    
    def _save_state(self) -> None:
        """保存状态"""
        self.state_path.write_text(
            json.dumps(self._state, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    
    def update(self, **kwargs) -> None:
        """更新状态"""
        self._state.update(kwargs)
        self._save_state()
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取状态值"""
        return self._state.get(key, default)
    
    def set_running(self, request: str, rounds: int) -> None:
        """设置为运行状态"""
        self.update(
            status="running",
            started_at=datetime.now().isoformat(),
            current_stage="initializing",
            progress=0,
            request=request,
            rounds=rounds,
        )
    
    def set_stage(self, stage: str, progress: int) -> None:
        """更新阶段和进度"""
        self.update(current_stage=stage, progress=progress)
    
    def set_paused(self) -> None:
        """设置为暂停状态"""
        self.update(
            status="paused",
            paused_at=datetime.now().isoformat(),
        )
    
    def set_resumed(self) -> None:
        """设置为恢复状态"""
        self.update(
            status="running",
            paused_at=None,
        )
    
    def set_completed(self, status: str, duration: float) -> None:
        """设置为完成状态"""
        self.update(
            status="completed",
            ended_at=datetime.now().isoformat(),
            duration_seconds=duration,
            current_stage=None,
        )
    
    def set_idle(self) -> None:
        """设置为空闲状态"""
        self.update(
            status="idle",
            current_stage=None,
            progress=0,
            started_at=None,
            paused_at=None,
        )


class OpenClawScheduler:
    """OpenClaw 全局调度器"""
    
    def __init__(self, env: Dict[str, str]):
        self.env = env
        self.state = OpenClawState(STATE_PATH)
        self.dingtalk = DingTalkBot(DINGTALK_CONFIG_PATH, env)
        self._workflow_process: Optional[subprocess.Popen] = None
        self._is_paused = False
        self._current_stage = ""
        self._stage_progress = 0
        self._workflow_log: List[str] = []
    
    def load_skills_library(self) -> str:
        """加载 skills 知识库"""
        if SKILLS_LIBRARY.exists():
            return SKILLS_LIBRARY.read_text(encoding="utf-8")
        return ""
    
    def save_skills_entry(self, stage_name: str, entry: Dict[str, Any]) -> None:
        """保存 skills 条目"""
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        
        if not SKILLS_LIBRARY.exists():
            SKILLS_LIBRARY.write_text(
                "# DARIS v3 Skills Library\n\n## 环节能力沉淀\n\n## 每轮深度复盘\n",
                encoding="utf-8"
            )
        
        lines = [
            "",
            f"### [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {stage_name}",
        ]
        for key in ["core_skills", "pitfalls", "optimizations", "evidence"]:
            values = entry.get(key, [])
            if not values:
                continue
            lines.append(f"- {key}:")
            for item in values:
                lines.append(f"  - {item}")
        
        with SKILLS_LIBRARY.open("a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    
    def send_dingtalk_progress(self, stage: str, message: str) -> None:
        """发送进度到钉钉"""
        self.dingtalk.send_stage_progress(stage, message)
        log_message(f"📱 钉钉推送：{stage} - {message}")
    
    def execute_workflow(
        self,
        request: str,
        rounds: int,
        use_gpu: bool = True,
        use_server: bool = False,
        skip_git: bool = False,
        skip_benchmark: bool = False,
    ) -> int:
        """
        执行工作流
        
        Args:
            request: 请求文本（科研关键词）
            rounds: 轮次
            use_gpu: 是否使用 GPU
            use_server: 是否使用阿里云服务器
        
        Returns:
            退出码
        """
        start_time = datetime.now()
        
        # 设置运行状态
        self.state.set_running(request, rounds)
        
        # 发送启动通知
        self.send_dingtalk_progress("启动通知", f"🚀 工作流启动\n关键词：{request}\n轮次：{rounds}\n运行模式：{'GPU 加速' if use_gpu else 'CPU'}")
        
        log_message(f"开始执行工作流：{request}")
        log_message(f"轮次：{rounds}")
        log_message(f"运行模式：{'GPU 加速' if use_gpu else 'CPU'}")
        
        # 构建命令
        cmd = [
            sys.executable,
            str(RUNNER_PATH),
            "--request",
            request,
            "--rounds",
            str(rounds),
        ]
        if skip_git:
            cmd.append("--skip-git")
        if skip_benchmark:
            cmd.append("--skip-benchmark")
        
        try:
            # 执行工作流
            self._workflow_process = subprocess.Popen(
                cmd,
                cwd=str(ROOT),
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env={**os.environ, **self.env},
            )
            
            # 读取输出并发送进度通知
            output_lines = []
            for line in self._workflow_process.stdout:
                line = line.strip()
                output_lines.append(line)
                print(line, flush=True)
                
                # 解析阶段进度并推送钉钉
                self._parse_and_notify_stage_progress(line)
            
            # 等待完成
            returncode = self._workflow_process.wait()
            
            # 计算耗时
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 更新状态
            if returncode == 0:
                self.state.set_completed("success", duration)
            else:
                self.state.set_completed("failed", duration)
            
            # 发送完成通知
            self.send_dingtalk_progress("完成通知", f"✅ 工作流完成\n状态：{'成功' if returncode == 0 else '失败'}\n耗时：{duration:.1f}秒")
            
            # 保存日志
            self._save_workflow_log(output_lines, start_time)
            
            # 更新 skills 知识库
            self._update_skills_library(returncode == 0)
            
            # 生成最终报表
            self._generate_final_report(request, rounds, duration, returncode == 0)
            
            return returncode
            
        except Exception as e:
            self.state.set_completed("error", 0)
            error_msg = f"工作流执行失败：{str(e)}"
            self.send_dingtalk_progress("错误告警", f"🚨 {error_msg}")
            log_message(error_msg)
            return 1
    
    def _parse_and_notify_stage_progress(self, line: str) -> None:
        """解析日志并发送阶段进度通知"""
        if "文献" in line.lower() or "literature" in line.lower():
            if "检索" in line or "抓取" in line:
                self.send_dingtalk_progress("文献检索", f"📚 正在检索文献...\n{line[:100]}")
            elif "总结" in line or "阅读" in line:
                self.send_dingtalk_progress("文献阅读", f"📖 正在阅读文献...\n{line[:100]}")
        elif "创新" in line or "innovation" in line.lower():
            self.send_dingtalk_progress("创新点生成", f"💡 正在生成创新点...\n{line[:100]}")
        elif "评审" in line or "review" in line.lower():
            self.send_dingtalk_progress("创新点评审", f"🔍 正在评审创新点...\n{line[:100]}")
        elif "代码" in line or "code" in line.lower():
            self.send_dingtalk_progress("代码实现", f"💻 正在制作代码 Demo...\n{line[:100]}")
        elif "实验" in line or "experiment" in line.lower() or "测试" in line:
            self.send_dingtalk_progress("实验测试", f"🧪 正在进行实验测试...\n{line[:100]}")
        elif "完成" in line or "complete" in line.lower():
            self.send_dingtalk_progress("完成", f"✅ {line[:100]}")
    
    def _save_workflow_log(self, lines: List[str], start_time: datetime) -> None:
        """保存工作流日志"""
        log_dir = WORKSPACE_ROOT / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        ts = start_time.strftime("%Y%m%d_%H%M%S")
        log_path = log_dir / f"openclaw_workflow_{ts}.log"
        log_path.write_text("\n".join(lines), encoding="utf-8")
        self._workflow_log = lines
    
    def _update_skills_library(self, success: bool) -> None:
        """更新 skills 知识库"""
        if success:
            self.save_skills_entry(
                "工作流执行完成",
                {
                    "core_skills": ["全流程自动执行", "多智能体协同"],
                    "optimizations": ["强化阶段间指标门禁", "缩短无效迭代"],
                }
            )
    
    def _generate_final_report(self, request: str, rounds: int, duration: float, success: bool) -> None:
        """生成最终报表"""
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 生成报表内容
        report = {
            "timestamp": datetime.now().isoformat(),
            "request": request,
            "rounds": rounds,
            "duration_seconds": duration,
            "success": success,
            "workflow_log": self._workflow_log[-50:],  # 最近 50 条日志
        }
        
        # 保存 JSON 报表
        json_path = REPORT_DIR / f"daily_report_{ts}.json"
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        
        # 生成 Markdown 报表
        md_content = f"""# DARIS 每日科研报表

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📋 今日任务

- **科研关键词**: {request}
- **工作流轮次**: {rounds}
- **执行耗时**: {duration:.1f} 秒
- **执行状态**: {'✅ 成功' if success else '❌ 失败'}

---

## 💡 今日创新点

> 从工作流日志中提取创新点内容...

---

## 💻 程序改动

> 从工作流日志中提取代码改动内容...

---

## 📊 数据指标

> 从工作流日志中提取实验指标...

---

## 📝 复盘记录

> 从工作流日志中提取复盘内容...

---

## 📁 详细日志

查看完整日志：`7_monitor_system/system_log/openclaw_workflow_{ts}.log`
"""
        md_path = REPORT_DIR / f"daily_report_{ts}.md"
        md_path.write_text(md_content, encoding="utf-8")
        
        # 发送报表到钉钉
        self.send_dingtalk_progress("报表生成", f"📊 今日报表已生成\n创新点：待提取\n程序改动：待提取\n数据指标：待提取\n复盘记录：待提取\n\n详细报表：{md_path}")
        
        # 在终端显示报表
        print("\n" + "=" * 60)
        print("📊 今日科研报表")
        print("=" * 60)
        print(f"科研关键词：{request}")
        print(f"工作流轮次：{rounds}")
        print(f"执行耗时：{duration:.1f}秒")
        print(f"执行状态：{'✅ 成功' if success else '❌ 失败'}")
        print(f"\n详细报表：{md_path}")
        print("=" * 60)
    
    def pause_workflow(self) -> str:
        """暂停工作流"""
        if self.state.get("status") != "running":
            return "当前没有正在执行的工作流"
        
        self._is_paused = True
        self.state.set_paused()
        
        progress = self.state.get("progress", 0)
        stage = self.state.get("current_stage", "unknown")
        
        response = DINGTALK_COMMANDS["/pause"]["response_template"].format(
            progress=f"{progress}%",
        )
        
        self.dingtalk.send_command_response("/pause", response)
        return response
    
    def resume_workflow(self) -> str:
        """恢复工作流"""
        if self.state.get("status") != "paused":
            return "当前没有暂停的工作流"
        
        self._is_paused = False
        self.state.set_resumed()
        
        response = DINGTALK_COMMANDS["/resume"]["response_template"]
        self.dingtalk.send_command_response("/resume", response)
        return response
    
    def stop_workflow(self) -> str:
        """停止工作流"""
        if self._workflow_process:
            self._workflow_process.terminate()
            self._workflow_process = None
        
        self.state.set_idle()
        
        response = DINGTALK_COMMANDS["/stop"]["response_template"].format(
            summary="工作流已终止",
        )
        self.dingtalk.send_command_response("/stop", response)
        return response
    
    def query_status(self) -> str:
        """查询状态"""
        status = self.state.get("status", "idle")
        stage = self.state.get("current_stage", "N/A")
        progress = self.state.get("progress", 0)
        started_at = self.state.get("started_at", "N/A")
        
        response = f"""📊 DARIS 当前状态

运行状态：{status}
当前环节：{stage}
进度：{progress}%
启动时间：{started_at}
"""
        return response
    
    def cleanup_files(self) -> str:
        """清理冗余文件"""
        # 导入清理模块
        from importlib import import_module
        
        try:
            runner = import_module("2_agent_system.1_research_manager.run")
            
            # 执行清理
            from pathlib import Path as P
            import sys
            sys.path.append(str(P(__file__).resolve().parent))
            
            # 简单清理：删除缓存目录
            cleaned = []
            skipped = []
            
            cache_dirs = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
            for cache_name in cache_dirs:
                for cache_dir in ROOT.rglob(cache_name):
                    if cache_dir.is_dir() and ".git" not in str(cache_dir):
                        try:
                            for child in cache_dir.rglob("*"):
                                child.unlink()
                            cache_dir.rmdir()
                            cleaned.append(str(cache_dir))
                        except Exception:
                            skipped.append(str(cache_dir))
            
            response = DINGTALK_COMMANDS["/clean"]["response_template"].format(
                list=f"删除 {len(cleaned)} 项，跳过 {len(skipped)} 项",
                space="N/A",
            )
            
            self.dingtalk.send_command_response("/clean", response)
            return response
            
        except Exception as e:
            return f"清理失败：{str(e)}"
    
    def rollback_version(self) -> str:
        """回滚版本"""
        try:
            # 执行 git 回滚
            result = subprocess.run(
                ["git", "log", "--oneline", "-2"],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                check=True,
            )
            
            lines = result.stdout.strip().split("\n")
            if len(lines) >= 2:
                prev_version = lines[1]
                
                subprocess.run(
                    ["git", "reset", "--hard", prev_version.split()[0]],
                    cwd=str(ROOT),
                    check=True,
                )
                
                response = DINGTALK_COMMANDS["/rollback"]["response_template"].format(
                    version=prev_version,
                    details="已回滚到上一版本",
                )
            else:
                response = "没有可回滚的版本"
            
            self.dingtalk.send_command_response("/rollback", response)
            return response
            
        except Exception as e:
            return f"回滚失败：{str(e)}"
    
    def show_help(self) -> str:
        """显示帮助信息"""
        commands_list = []
        for cmd, info in DINGTALK_COMMANDS.items():
            commands_list.append(f"{cmd} - {info['description']}")
        
        response = DINGTALK_COMMANDS["/help"]["response_template"].format(
            commands="\n".join(commands_list),
        )
        return response
    
    def process_command(self, command: str) -> str:
        """
        处理钉钉指令
        
        Args:
            command: 指令文本
        
        Returns:
            响应文本
        """
        command = command.strip().lower()
        
        if command == "/start":
            # 启动工作流
            threading.Thread(
                target=self.execute_workflow,
                args=("严格按照 DARIS_v3.md 文档执行", 1),
                daemon=True,
            ).start()
            return "🚀 DARIS 工作流已启动"
        
        elif command == "/pause":
            return self.pause_workflow()
        
        elif command == "/resume":
            return self.resume_workflow()
        
        elif command == "/stop":
            return self.stop_workflow()
        
        elif command == "/status":
            return self.query_status()
        
        elif command == "/clean":
            return self.cleanup_files()
        
        elif command == "/rollback":
            return self.rollback_version()
        
        elif command == "/help":
            return self.show_help()
        
        else:
            return f"未知指令：{command}\n发送 /help 查看可用指令"


def _load_env() -> Dict[str, str]:
    """加载环境变量"""
    env = dict(os.environ)
    env_file = ROOT / ".env"
    if env_file.exists():
        for raw in env_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def _interactive_setup() -> Dict[str, Any]:
    """交互式设置"""
    print("\n" + "=" * 60)
    print("DARIS v3.2 交互式启动")
    print("=" * 60)
    
    # 1. 选择运行模式
    print("\n📍 请选择运行模式:")
    print("1. 本地 GPU 加速 (推荐)")
    print("2. 本地 CPU 运行")
    print("3. 阿里云服务器运行")
    
    while True:
        mode_choice = input("\n请输入选项 (1/2/3): ").strip()
        if mode_choice in ["1", "2", "3"]:
            break
        print("无效选项，请重新输入")
    
    use_gpu = mode_choice == "1"
    use_server = mode_choice == "3"
    
    if use_server:
        print("\n📡 正在检查阿里云服务器连接...")
        connector = create_connector_from_env()
        if connector.connect():
            gpu_available = connector.check_gpu()
            connector.close()
            if gpu_available:
                print("✅ 阿里云服务器 GPU 可用")
            else:
                print("⚠️ 阿里云服务器 GPU 不可用，将使用 CPU 运行")
        else:
            print("❌ 阿里云服务器连接失败，切换到本地运行")
            use_server = False
    
    # 2. 输入科研关键词
    print("\n🔬 请输入今日科研关键词:")
    print("(例如：负荷预测、碳排放预测、电力时序预测等)")
    keywords = input("关键词：").strip()
    
    if not keywords:
        keywords = "负荷预测方向"
        print(f"使用默认关键词：{keywords}")
    
    # 3. 输入工作流轮次
    print("\n🔄 请输入工作流轮次:")
    while True:
        try:
            rounds = int(input("轮次 (默认 1): ").strip() or "1")
            if rounds > 0:
                break
            print("轮次必须大于 0")
        except ValueError:
            print("请输入有效数字")
    
    # 4. 确认配置
    print("\n" + "=" * 60)
    print("配置确认")
    print("=" * 60)
    print(f"运行模式：{'阿里云服务器' if use_server else ('本地 GPU 加速' if use_gpu else '本地 CPU')}")
    print(f"科研关键词：{keywords}")
    print(f"工作流轮次：{rounds}")
    print("=" * 60)
    
    confirm = input("\n确认启动？(y/n): ").strip().lower()
    if confirm != "y":
        print("已取消启动")
        sys.exit(0)
    
    return {
        "keywords": keywords,
        "rounds": rounds,
        "use_gpu": use_gpu,
        "use_server": use_server,
    }


def _dingtalk_instruction_handler(command: str, sender_id: str, sender_nick: str) -> str:
    """
    钉钉指令处理函数（供回调服务器调用）
    
    Args:
        command: 指令内容
        sender_id: 发送者 ID
        sender_nick: 发送者昵称
    
    Returns:
        响应文本
    """
    # 创建临时调度器处理指令
    env = _load_env()
    scheduler = OpenClawScheduler(env)
    return scheduler.process_command(command)


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="DARIS v3.2 OpenClaw 全局调度")
    parser.add_argument(
        "--command",
        type=str,
        default="start",
        choices=["start", "status", "daemon", "interactive"],
        help="启动模式",
    )
    parser.add_argument(
        "--request",
        type=str,
        default="",
        help="工作流请求（科研关键词）",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=0,
        help="工作流轮次",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="以守护进程模式运行（持续监听钉钉指令）",
    )
    parser.add_argument(
        "--callback-port",
        type=int,
        default=CALLBACK_PORT,
        help=f"钉钉回调服务器监听端口 (默认：{CALLBACK_PORT})",
    )
    parser.add_argument(
        "--no-callback",
        action="store_true",
        help="不启动钉钉回调服务器",
    )
    parser.add_argument(
        "--gpu",
        action="store_true",
        help="使用 GPU 加速",
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help="使用阿里云服务器",
    )
    parser.add_argument(
        "--skip-git",
        action="store_true",
        help="跳过工作流中的所有 git 提交",
    )
    parser.add_argument(
        "--skip-benchmark",
        action="store_true",
        help="跳过 12 个标杆项目能力集成阶段",
    )
    args = parser.parse_args()
    
    # 加载环境
    env = _load_env()
    
    # 创建调度器
    scheduler = OpenClawScheduler(env)
    
    # 交互式模式或命令行参数模式
    if args.command == "interactive" or (args.command == "start" and not args.request):
        # 交互式设置
        config = _interactive_setup()
        keywords = config["keywords"]
        rounds = config["rounds"]
        use_gpu = config["use_gpu"]
        use_server = config["use_server"]
    else:
        # 命令行参数模式
        keywords = args.request or "负荷预测方向"
        rounds = args.rounds if args.rounds > 0 else 1
        use_gpu = args.gpu
        use_server = args.server
    
    print("\n" + "=" * 60)
    print("DARIS v3.2 OpenClaw 全局调度服务")
    print("=" * 60)
    
    if args.command == "status":
        # 查询状态
        print(scheduler.query_status())
        return
    
    # 启动钉钉回调服务器（双向通信）
    if not args.no_callback:
        print(f"\n📡 正在启动钉钉回调服务器，监听端口：{args.callback_port}")
        
        global CALLBACK_SERVER
        CALLBACK_SERVER = create_callback_server(
            port=args.callback_port,
            env=env,
            instruction_handler=_dingtalk_instruction_handler,
        )
        
        if CALLBACK_SERVER.start():
            print(f"✅ 钉钉回调服务器已启动")
            print(f"📡 回调 URL: http://47.100.98.160:{args.callback_port}/")
            print("")
            print("⚠️ 钉钉开发者后台配置步骤:")
            print("1. 登录钉钉开发者后台：https://open-dev.dingtalk.com/")
            print("2. 创建企业内部应用")
            print("3. 配置回调 URL: http://47.100.98.160:{args.callback_port}/")
            print("4. 配置 Token: {env.get('DINGTALK_TOKEN', '未配置')}")
            print("5. 启用事件订阅")
            print("")
        else:
            print("❌ 钉钉回调服务器启动失败")
    
    # 发送启动通知到钉钉
    scheduler.dingtalk.send_message(
        level="notice",
        stage="openclaw",
        action="start",
        result=f"DARIS v3.2 OpenClaw 服务已启动\n关键词：{keywords}\n轮次：{rounds}\n模式：{'GPU 加速' if use_gpu else 'CPU'}",
    )
    
    print("✅ OpenClaw 服务已启动")
    print("✅ 钉钉管控已接通")
    print("✅ 可发送指令操控项目")
    print("")
    print("可用指令:")
    for cmd, info in DINGTALK_COMMANDS.items():
        print(f"  {cmd} - {info['description']}")
    print("")
    
    # 执行工作流
    print(f"开始执行工作流：{keywords}")
    print(f"轮次：{rounds}")
    
    # 在后台线程中执行工作流
    workflow_thread = threading.Thread(
        target=scheduler.execute_workflow,
        args=(keywords, rounds, use_gpu, use_server, args.skip_git, args.skip_benchmark),
        daemon=True,
    )
    workflow_thread.start()
    
    # 如果是守护进程模式，持续监听钉钉指令
    if args.daemon or not args.no_callback:
        print("")
        print("进入钉钉指令监听模式...")
        print("按 Ctrl+C 退出")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n收到退出信号，正在关闭...")
            scheduler.stop_workflow()
            
            # 停止回调服务器
            if CALLBACK_SERVER:
                CALLBACK_SERVER.stop()
    else:
        # 等待工作流完成
        workflow_thread.join()


if __name__ == "__main__":
    main()