from typing import *
from starlette.requests import Request

from src.modules import Module

import logging
import json
import os

class Helpers:
    @staticmethod
    def get_env(name: str, default: Optional[Any] = None) -> Any:
        value = os.getenv(name)
        if value is None or value.strip() == "":
            return default
        return value.strip()

    @staticmethod
    def get_env_list(name: str, default: Optional[list[str]] = None) -> list[str]:
        value = os.getenv(name)
        if value is None or value.strip() == "":
            return list(default or [])
        return [item.strip() for item in value.split(",") if item.strip()]

    @staticmethod
    def get_env_bool(name: str, default: bool = False) -> bool:
        value = os.getenv(name)
        if value is None:
            return default
        return value.strip().lower() in ["1", "true", "yes", "on"]

    @staticmethod
    def send_error(
        error_code: Union[int, str] = 500,
        error_message: str = "An unexpected error occurred.",
        raise_exception: bool = False,
    ):
        if raise_exception:
            raise ConnectionRefusedError(f"Error {error_code}: {error_message}")
        return {
            "code": error_code,
            "message": error_message,
        }

    @staticmethod
    async def parse_rest_payload(
        request: Request,
        agent_logger: logging.Logger,
        nested_keys: Optional[list[str]] = None
    ) -> dict[str, Any]:
        try:
            payload = await request.json()
            if isinstance(payload, dict):
                return payload
        except:
            pass

        form = await request.form()
        payload = dict(form)
        if nested_keys:
            for key in nested_keys:
                value = payload.get(key, None)
                if isinstance(value, str) and value.strip():
                    try:
                        payload[key] = json.loads(value)
                    except:
                        agent_logger.warning(f"Failed to parse JSON for key '{key}': {value}")

        return payload


    @staticmethod
    def sanitize_extra_kwargs(
        extra_kwargs: Optional[dict[str, Any]],
        key_prefix: str = 'params_',
        allow_test_kwargs: bool = False,
    ) -> tuple[dict[str, Any], list[str]]:
        """
        Sanitize extra keyword arguments by enforcing key prefixes and value constraints.

        Args:
            extra_kwargs (Optional[dict[str, Any]]): The extra keyword arguments to sanitize.
            key_prefix (str): The prefix that valid keys must start with.
            allow_test_kwargs (bool): Whether to allow test-specific keyword arguments.

        Returns:
            tuple[dict[str, Any], list[str]]: A tuple containing the sanitized keyword arguments and a list of warnings.
        """
        
        warnings = []
        if extra_kwargs is None:
            return {}, warnings

        if not isinstance(extra_kwargs, dict):
            warnings.append("Invalid extraKwargs type. It must be a JSON object and was ignored.")
            return {}, warnings

        sanitized = dict(extra_kwargs)
        validate_keys = [key for key in list(sanitized.keys()) if key.startswith(key_prefix)]

        # In production mode, block retrieval tuning from extra kwargs.
        if validate_keys and not allow_test_kwargs:
            for key in validate_keys:
                sanitized.pop(key, None)
            warnings.append(
                f"{key_prefix}* parameters from extraKwargs are disabled by server guardrail. "
                "Use server defaults unless test mode is enabled."
            )
            return sanitized, warnings

        def clamp_int(key: str, minimum: int, maximum: int, default: int) -> None:
            if key not in sanitized:
                return
            try:
                value = int(sanitized[key])
            except Exception:
                warnings.append(f"Invalid {key}. Using default value {default}.")
                sanitized[key] = default
                return

            clamped = min(max(value, minimum), maximum)
            if clamped != value:
                warnings.append(f"{key} was clamped to {clamped} (allowed range: {minimum}..{maximum}).")
            sanitized[key] = clamped

        def clamp_float(key: str, minimum: float, maximum: float, default: float) -> None:
            if key not in sanitized:
                return
            try:
                value = float(sanitized[key])
            except Exception:
                warnings.append(f"Invalid {key}. Using default value {default}.")
                sanitized[key] = default
                return

            clamped = min(max(value, minimum), maximum)
            if clamped != value:
                warnings.append(f"{key} was clamped to {clamped} (allowed range: {minimum}..{maximum}).")
            sanitized[key] = clamped

        def parse_bool_value(key: str, default: bool = False) -> None:
            if key not in sanitized:
                return
            value = sanitized[key]
            if isinstance(value, bool):
                sanitized[key] = value
                return
            if isinstance(value, (int, float)):
                sanitized[key] = bool(value)
                return
            if isinstance(value, str):
                lowered = value.strip().lower()
                if lowered in ["1", "true", "yes", "on"]:
                    sanitized[key] = True
                    return
                if lowered in ["0", "false", "no", "off", ""]:
                    sanitized[key] = False
                    return
            warnings.append(f"Invalid {key}. Using default value {default}.")
            sanitized[key] = default


        # Example
        # 1. str or float (variation)
        if "params_str_or_float" in sanitized:
            value = sanitized.get("params_str_or_float")
            if isinstance(value, str) and value.strip().lower() == "auto":
                sanitized["params_str_or_float"] = "auto"
            else:
                clamp_float("params_str_or_float", minimum=0.0, maximum=1.0, default=0.5)
        
        # 2. int
        clamp_int("params_int", minimum=1, maximum=10, default=3)
        # 3. float
        clamp_float("params_float", minimum=0.0, maximum=1.0, default=1.0)
        # 4. bool
        parse_bool_value("params_bool", default=False)

        return sanitized, warnings