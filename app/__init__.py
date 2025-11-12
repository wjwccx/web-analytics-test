import logging
import os
from pathlib import Path

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.log import LogConfig


def init_project_logger():
    """初始化项目日志器"""
    # 设置日志文件路径
    log_file_str = os.getenv("LOG_FILE")
    if log_file_str:
        log_file = Path(log_file_str)
    else:
        # 设置默认日志路径
        log_file = Path("logs/server.log")

    # 确保日志目录存在
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # 设置日志级别
    log_level_str = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    try:
        level = getattr(logging, log_level_str)
    except AttributeError:
        level = logging.INFO
        print(f"Warning: Invalid log level '{log_level_str}', using INFO")

    # 设置根日志器和主模块日志器
    for name in ["__main__", __name__]:
        LogConfig.setup_logger(
            name=name,
            level=level,
            log_file=log_file,
            console=True,
            max_bytes=10 * 1024 * 1024,  # 10MB
            backup_count=10,
        )

    # 记录初始化信息
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging initialized. Level: {logging.getLevelName(level)}, File: {log_file}"
    )


# 初始化项目日志器
init_project_logger()


def init_sentry():
    """初始化 Sentry 监控"""
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        logger = logging.getLogger(__name__)
        logger.warning(
            "SENTRY_DSN not found in environment variables, Sentry monitoring is disabled"
        )
        return

    # 配置 Sentry
    sentry_logging = LoggingIntegration(
        level=logging.WARNING,  # 捕获 WARNING 及以上级别的日志
        event_level=logging.ERROR,  # 发送 ERROR 及以上级别到 Sentry
    )

    # 性能追踪采样率，默认 10%
    traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
    # 性能分析采样率，默认 5%
    profiles_sample_rate = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.05"))

    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=traces_sample_rate,
        profiles_sample_rate=profiles_sample_rate,
        environment=os.getenv("ENVIRONMENT", "development"),
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            sentry_logging,
        ],
    )


# 初始化 Sentry
init_sentry()
