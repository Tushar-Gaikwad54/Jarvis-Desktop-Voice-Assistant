"""
Configuration Manager for J.A.R.V.I.S.
Handles loading, saving, and defaults for offline/local LLMs, tools, permissions, and voice.
"""

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict


@dataclass
class LLMConfig:
    provider: str = "fallback"  # 'ollama', 'openai_compatible', 'fallback'
    model: str = "llama3.2"
    ollama_url: str = "http://localhost:11434"
    openai_compat_url: str = "http://localhost:1234/v1"
    openai_compat_api_key: str = "not-needed"
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout_seconds: int = 60


@dataclass
class SecurityConfig:
    require_confirmation_for_high_risk: bool = True
    auto_approve_low_risk: bool = True
    auto_approve_medium_risk: bool = False
    allowed_workspace_only: bool = False
    command_timeout_seconds: int = 30


@dataclass
class VoiceConfig:
    enabled: bool = False
    tts_engine: str = "pyttsx3"  # Offline SAPI5 on Windows
    tts_rate: int = 175
    tts_volume: float = 1.0
    voice_index: int = 1
    voice_gender: str = "male"  # 'male' (J.A.R.V.I.S.) or 'female' (F.R.I.D.A.Y.)
    input_mode: str = "text"  # 'text' or 'voice'


@dataclass
class JarvisConfig:
    name: str = "J.A.R.V.I.S."
    user_name: str = "Sir"
    workspace_dir: str = str(Path.cwd())
    llm: LLMConfig = field(default_factory=LLMConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    log_level: str = "INFO"

    @classmethod
    def load(cls, config_path: str = "config.json") -> "JarvisConfig":
        path = Path(config_path)
        if not path.is_file():
            config = cls()
            config.save(config_path)
            return config

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            llm_data = data.get("llm", {})
            security_data = data.get("security", {})
            voice_data = data.get("voice", {})

            return cls(
                name=data.get("name", "J.A.R.V.I.S."),
                user_name=data.get("user_name", "Sir"),
                workspace_dir=data.get("workspace_dir", str(Path.cwd())),
                llm=LLMConfig(**llm_data),
                security=SecurityConfig(**security_data),
                voice=VoiceConfig(**voice_data),
                log_level=data.get("log_level", "INFO"),
            )
        except Exception as e:
            print(f"[Warning] Failed to parse {config_path}: {e}. Using default config.")
            return cls()

    def save(self, config_path: str = "config.json") -> None:
        path = Path(config_path)
        data = asdict(self)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


# Global instance
_current_config: JarvisConfig = None


def get_config(config_path: str = "config.json") -> JarvisConfig:
    global _current_config
    if _current_config is None:
        _current_config = JarvisConfig.load(config_path)
    return _current_config


def reload_config(config_path: str = "config.json") -> JarvisConfig:
    global _current_config
    _current_config = JarvisConfig.load(config_path)
    return _current_config
