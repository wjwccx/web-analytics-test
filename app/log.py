import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


class LogConfig:
    """日志配置类"""

    # 添加类变量定义默认值
    DEFAULT_FORMAT = {
        "DEBUG": "%(asctime)s | %(levelname)-5s | %(name)s | %(filename)s:%(funcName)s:%(lineno)d | %(message)s",
        "DEFAULT": "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
    }
    DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    @classmethod
    def setup_logger(
        cls,
        name: str,
        log_file: Optional[Path] = None,
        level: int = logging.INFO,
        console: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 10,
        encoding: str = "utf-8",
    ) -> logging.Logger:
        """设置日志器

        Args:
            name: 日志器名称, 通常为带包路径的模块名
            log_file: 日志文件路径
            level: 日志级别
            console: 是否输出到控制台
            max_bytes: 单个日志文件最大大小，默认10MB
            backup_count: 保留的日志文件数量，默认5个
            encoding: 日志文件编码，默认utf-8
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # 设置日志格式
        fmt = (
            cls.DEFAULT_FORMAT["DEBUG"]
            if level == logging.DEBUG
            else cls.DEFAULT_FORMAT["DEFAULT"]
        )
        formatter = logging.Formatter(fmt, datefmt=cls.DEFAULT_DATE_FORMAT)

        # 清除已有的处理器
        logger.handlers.clear()

        # 添加文件处理器（使用 RotatingFileHandler）
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding=encoding,
            )
            fh.setFormatter(formatter)
            logger.addHandler(fh)

        # 添加控制台处理器
        if console:
            ch = logging.StreamHandler(sys.stdout)
            ch.setFormatter(formatter)
            logger.addHandler(ch)

        # 防止日志向上传递
        logger.propagate = False

        logger.debug(
            f"Logger '{name}' setup completed. Level: {logging.getLevelName(level)}"
        )
        return logger
