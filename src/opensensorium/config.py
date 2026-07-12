"""配置加载：分层覆盖 config.yaml → config.local.yaml → 环境变量。

- `config.yaml`：提交进仓库的默认配置。
- `config.local.yaml`：本机私有覆盖（**已在 .gitignore**，放推理服务地址/密钥）。
- 环境变量：`OPENSENSORIUM_` 前缀，`__` 表示层级，如
  `OPENSENSORIUM_INFERENCE__BASE_URL=http://192.168.1.20:8070`。

优先级（低→高）：默认值 < config.yaml < config.local.yaml < 环境变量。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

ENV_PREFIX = "OPENSENSORIUM_"
ENV_NESTED_SEP = "__"


class InferenceConfig(BaseModel):
    """推理服务（跑在 4090 台式机，局域网可达）。"""

    base_url: str = Field(default="http://127.0.0.1:8070", description="推理服务 HTTP 基址")
    model: str = Field(default="minicpm-o", description="默认模型名（对应 Adapter 注册名）")
    request_timeout_s: float = 30.0


class StreamConfig(BaseModel):
    """采集/流基线（对齐 PRD §6.6）。"""

    audio_sample_rate: int = 16000  # 16kHz mono
    audio_chunk_s: float = 1.0
    video_fps: float = 1.0  # 基线 ~1fps，最高 10
    video_max_pixels: int = 1_800_000  # ≤~180 万像素


class Config(BaseModel):
    """全局配置根。各任务按需在此追加自己的子配置块。"""

    inference: InferenceConfig = Field(default_factory=InferenceConfig)
    stream: StreamConfig = Field(default_factory=StreamConfig)
    log_level: str = "INFO"


# --------------------------------------------------------------------------- #
# 加载
# --------------------------------------------------------------------------- #


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """递归合并 override 到 base（就地返回新 dict）。"""
    out = dict(base)
    for key, value in override.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def _coerce_scalar(value: str) -> Any:
    """把环境变量字符串尽量还原为 yaml 标量（int/float/bool/None/str）。"""
    try:
        return yaml.safe_load(value)
    except yaml.YAMLError:
        return value


def _env_overrides(environ: dict[str, str]) -> dict[str, Any]:
    """从环境变量提取覆盖树。`OPENSENSORIUM_A__B=v` → {"a": {"b": v}}。"""
    tree: dict[str, Any] = {}
    for raw_key, raw_val in environ.items():
        if not raw_key.startswith(ENV_PREFIX):
            continue
        path = raw_key[len(ENV_PREFIX) :].lower().split(ENV_NESTED_SEP)
        node = tree
        for part in path[:-1]:
            node = node.setdefault(part, {})
        node[path[-1]] = _coerce_scalar(raw_val)
    return tree


def load_config(
    config_dir: str | Path | None = None,
    environ: dict[str, str] | None = None,
) -> Config:
    """按分层顺序加载并返回 `Config`。

    `config_dir` 默认取当前工作目录；`environ` 默认取 `os.environ`（便于测试注入）。
    """
    base_dir = Path(config_dir) if config_dir is not None else Path.cwd()
    env = dict(os.environ if environ is None else environ)

    merged: dict[str, Any] = {}
    merged = _deep_merge(merged, _load_yaml(base_dir / "config.yaml"))
    merged = _deep_merge(merged, _load_yaml(base_dir / "config.local.yaml"))
    merged = _deep_merge(merged, _env_overrides(env))

    return Config.model_validate(merged)
