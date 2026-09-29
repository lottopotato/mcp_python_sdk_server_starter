from rich.console import Console, RenderableType
from rich.logging import RichHandler
from rich.abc import RichRenderable
from rich.table import Table
from rich.text import Text

from dataclasses import dataclass
from typing import Optional
from io import StringIO
from logging.handlers import TimedRotatingFileHandler

import logging
import os
import gzip
import shutil

from .__init__ import Module, ModuleConfig

class LoggerLevel:
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    @staticmethod
    def to_int(level_str: str) -> int:
        level_str = level_str.upper()
        if level_str == "DEBUG":
            return LoggerLevel.DEBUG
        elif level_str == "INFO":
            return LoggerLevel.INFO
        elif level_str == "WARNING":
            return LoggerLevel.WARNING
        elif level_str == "ERROR":
            return LoggerLevel.ERROR
        elif level_str == "CRITICAL":
            return LoggerLevel.CRITICAL
        else:
            return LoggerLevel.INFO  # Default to INFO if unrecognized
    
    @staticmethod
    def to_str(level_int: int) -> str:
        if level_int == LoggerLevel.DEBUG:
            return "DEBUG"
        elif level_int == LoggerLevel.INFO:
            return "INFO"
        elif level_int == LoggerLevel.WARNING:
            return "WARNING"
        elif level_int == LoggerLevel.ERROR:
            return "ERROR"
        elif level_int == LoggerLevel.CRITICAL:
            return "CRITICAL"
        else:
            return "INFO"  # Default to INFO if unrecognized

class RenderableHandler(RichHandler):
    def render_message(self, record, message):
        if isinstance(message, RichRenderable):
            return message
        else:
            return super().render_message(record, message)

class RenderableFormatter(logging.Formatter):
    def format(self, record):
        if isinstance(record.msg, RichRenderable):
            return record.msg
        else:
            return super().format(record)

class RichFileFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%', validate=True, **kwargs):
        super().__init__(fmt, datefmt, style, validate)
        # Initialize a rich Console for rendering to a string buffer.
        # - file=StringIO() redirects output to an in-memory string.
        # - force_terminal=False and no_color=True ensure plain text output without ANSI codes.
        # - width can be adjusted to control how wide tables/panels are rendered in the log file.
        self._console = Console(file=StringIO(), force_terminal=False, no_color=True, width=120)

    def format(self, record):
        # Store the original message to restore it later, preventing side effects
        original_msg = record.msg
        try:
            # If the message is a rich renderable object
            if isinstance(original_msg, RenderableType):
                # Capture the rich object's rendered string
                with self._console.capture() as capture:
                    # Print the rich object to our internal console, soft_wrap helps with long lines
                    self._console.print(original_msg, soft_wrap=True)
                rendered_string = capture.get()
                # Replace the record's message with the rendered string, removing trailing newlines
                record.msg = rendered_string.strip()

            # Now, let the standard formatter handle the (potentially modified) record
            return super().format(record)
        finally:
            # Always restore the original message
            record.msg = original_msg

@dataclass
class LoggingModuleConfig(ModuleConfig):
    log_level: int = logging.INFO

class LoggingModule(Module):
    def __init__(
        self,
        config: LoggingModuleConfig
    ):
        super().__init__(config)

    @staticmethod
    def create_rich_table(
        title: str, 
        columns: list[str], 
        rows: list[list[str]], 
        table_config: Optional[dict] = None,
    ) -> Table:
        """Create a Rich table with given title, columns, and rows
        """
        table_kwargs = table_config.get('body', {}) if table_config else {}
        table = Table(title=title, **table_kwargs)
        for i, col in enumerate(columns):
            column_kwargs = table_config.get('columns', {}).get(i, {}) if table_config else {}
            table.add_column(col, **column_kwargs)
        for i, row in enumerate(rows):
            row_kwargs = table_config.get('rows', {}).get(i, {}) if table_config else {}
            table.add_row(*row, **row_kwargs)
        return table
    
    @staticmethod
    def show_loggers():
        print("Current loggers in the logging system:")
        for name in logging.Logger.manager.loggerDict.keys():
            # The root logger is represented by an empty string or 'root' in some contexts,
            # but its entry in loggerDict is usually the Logger object itself, not a string key.
            # We can explicitly check for the root logger.
            if name == 'root': # Sometimes the root logger is explicitly named 'root' here
                print(f"  - {name} (Root Logger)")
            elif isinstance(logging.Logger.manager.loggerDict[name], logging.PlaceHolder):
                # PlaceHolders are created for child loggers whose parents haven't been
                # explicitly instantiated yet. They still represent a logger name.
                print(f"  - {name} (PlaceHolder Logger)")
            else:
                print(f"  - {name}")

    def log_table(self, title: str, columns: list[str], rows: list[list[str]]):
        return self.create_rich_table(title, columns, rows)

    @staticmethod
    def _str_to_bool(value: str, default: bool = False) -> bool:
        if value is None:
            return default
        value = value.strip().lower()
        return value in ["1", "true", "yes", "y", "on"]

    def create_rich_logger(
        self,
        name: Optional[str] = None, 
        level: Optional[int] = logging.INFO,
        log_file_name: str = "app_log",
        logger_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        retention_days: Optional[int] = None,
        compress_rotated_logs: Optional[bool] = None,
    ) -> logging.Logger:
        """Get a logger that can handle Rich renderables in both console and file outputs.

        Rotation policy (centralized):
        - rotate daily at midnight
        - keep logs for N days (default: 10)
        - optionally compress rotated logs (default: true)

        Env override:
        - LOG_RETENTION_DAYS
        - LOG_COMPRESS_ROTATED
        """
        logger = logging.getLogger(name)
        logger.propagate = False

        # Re-initialization safety: avoid duplicated handlers when modules are reloaded.
        for existing_handler in list(logger.handlers):
            logger.removeHandler(existing_handler)
            try:
                existing_handler.close()
            except Exception:
                pass
        
        rich_file_formatter = RichFileFormatter(logger_format)
        renderable_formatter = RenderableFormatter(logger_format)

        log_dir = os.path.dirname(log_file_name)
        os.makedirs(log_dir, exist_ok=True)

        if retention_days is None:
            retention_days = int(os.getenv("LOG_RETENTION_DAYS", "10"))
        retention_days = max(1, retention_days)

        if compress_rotated_logs is None:
            compress_rotated_logs = self._str_to_bool(
                os.getenv("LOG_COMPRESS_ROTATED", "true"),
                default=True,
            )

        file_handler = TimedRotatingFileHandler(
            filename=log_file_name,
            when="midnight",
            interval=1,
            backupCount=retention_days,
            encoding="utf-8",
        )

        if compress_rotated_logs:
            def _namer(default_name: str) -> str:
                return default_name + ".gz"

            def _rotator(source: str, dest: str) -> None:
                with open(source, "rb") as source_file, gzip.open(dest, "wb") as dest_file:
                    shutil.copyfileobj(source_file, dest_file)
                os.remove(source)

            file_handler.namer = _namer
            file_handler.rotator = _rotator

        file_handler.setFormatter(rich_file_formatter)
        logger.addHandler(file_handler)

        handler = RenderableHandler(show_path=False)
        handler.setFormatter(renderable_formatter)
        logger.addHandler(handler)

        logger.setLevel(level or self.config.log_level)

        return logger
    
    def create_basic_logger(
        self,
        name: Optional[str] = None, 
        level: Optional[int] = logging.INFO,
        log_file_name: str = "app_log",
        logger_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        retention_days: Optional[int] = None,
        compress_rotated_logs: Optional[bool] = None,
    ) -> logging.Logger:
        """Get a basic logger without Rich renderable support, for simpler log messages.
        Useful for logging from modules that may not have access to the rich library or for very high-frequency logs where performance is a concern.
        """
        logger = logging.getLogger(name)
        logger.propagate = False

        # Re-initialization safety: avoid duplicated handlers when modules are reloaded.
        for existing_handler in list(logger.handlers):
            logger.removeHandler(existing_handler)
            try:
                existing_handler.close()
            except Exception:
                pass

        formatter = logging.Formatter(logger_format)

        log_dir = os.path.dirname(log_file_name)
        os.makedirs(log_dir, exist_ok=True)

        if retention_days is None:
            retention_days = int(os.getenv("LOG_RETENTION_DAYS", "10"))
        retention_days = max(1, retention_days)

        if compress_rotated_logs is None:
            compress_rotated_logs = self._str_to_bool(
                os.getenv("LOG_COMPRESS_ROTATED", "true"),
                default=True,
            )

        file_handler = TimedRotatingFileHandler(
            filename=log_file_name,
            when="midnight",
            interval=1,
            backupCount=retention_days,
            encoding="utf-8",
        )

        if compress_rotated_logs:
            def _namer(default_name: str) -> str:
                return default_name + ".gz"

            def _rotator(source: str, dest: str) -> None:
                with open(source, "rb") as source_file, gzip.open(dest, "wb") as dest_file:
                    shutil.copyfileobj(source_file, dest_file)
                os.remove(source)

            file_handler.namer = _namer
            file_handler.rotator = _rotator

        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.setLevel(level or self.config.log_level)
        return logger