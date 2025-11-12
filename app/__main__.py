import argparse
import logging
import os

import sentry_sdk
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)

app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器 - 最佳实践机制
    1. 统一错误处理：兜底捕获所有异常，向客户返回统一友好的错误响应格式
    2. 防止敏感信息泄露：生产环境下，向客户屏蔽具体的错误堆栈等信息
    3. 错误的监控和追踪：可以补充全面的上下文，并让 Sentry 自动捕获异常
    """
    logger.exception("Unhandled exception occurred", exc_info=exc)
    # Sentry 会自动捕获异常，这里不需要额外处理
    return HTMLResponse(content="Internal Server Error", status_code=500)


@app.get("/api/company_info/{stock_code}")
async def company_info(stock_code: str):
    logger.info(f"Fetching company info for stock code: {stock_code}")
    try:
        data = {"id":"00001"}
        if not data:
            logger.warning(f"No company info found for stock code: {stock_code}")
            return {"status": "error", "message": "未找到相关公司信息"}
        logger.debug(f"Successfully retrieved company info for {stock_code}")
        return {"status": "success", "data": data}
    except Exception as e:
        logger.error(
            f"Error fetching company info for {stock_code}: {str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ping")
async def ping():
    """测试接口"""
    return {"ping": "pong"}


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Stock Data API Server")
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host address to bind to. Examples: "
        "0.0.0.0/127.0.0.1 (IPv4), [::]/[::1] (IPv6). "
        "Default: None (dual-stack, IPv4+IPv6)",
    )
    parser.add_argument(
        "--port", type=int, default=8888, help="Port number (default: 8888)"
    )
    parser.add_argument(
        "--reload", action="store_true", help="Reload on code changes (default: False)"
    )
    args = parser.parse_args()

    logger.info(f"Starting server on {args.host}:{args.port} (reload={args.reload})")

    module_path = f"{__package__}.{__name__}:app" if __package__ else f"{__name__}:app"
    try:
        uvicorn.run(
            module_path,
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=os.getenv("LOG_LEVEL", "info").lower(),
        )
    except Exception as e:
        logger.critical(f"Failed to start server: {str(e)}", exc_info=True)
        raise
