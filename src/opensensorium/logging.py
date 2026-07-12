"""结构化日志（loguru）。每条记录带 run id 与时间戳，满足可观测 NFR。

用法：
    from opensensorium.logging import setup_logging, get_logger
    setup_logging(level="INFO")
    log = get_logger()
    log.info("started", extra_field=123)
"""

from __future__ import annotations

import sys
import uuid

from loguru import logger

# 本进程的一次运行标识，贯穿所有日志，便于把一次会话的记录串起来。
RUN_ID: str = uuid.uuid4().hex[:12]

_CONFIGURED = False

_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
    "<level>{level: <8}</level> "
    "run=<cyan>{extra[run_id]}</cyan> "
    "<level>{message}</level> "
    "{extra}"
)


def setup_logging(level: str = "INFO", run_id: str | None = None) -> "logger.__class__":
    """初始化全局日志。可传入自定义 `run_id`（否则用本进程默认）。"""
    global RUN_ID, _CONFIGURED
    if run_id:
        RUN_ID = run_id
    logger.remove()
    logger.configure(extra={"run_id": RUN_ID})
    logger.add(sys.stderr, level=level, format=_FORMAT, enqueue=True, backtrace=False)
    _CONFIGURED = True
    return logger


def get_logger() -> "logger.__class__":
    """获取日志器；若尚未初始化则用默认配置初始化一次。"""
    if not _CONFIGURED:
        setup_logging()
    return logger
