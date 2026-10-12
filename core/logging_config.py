import logging.config


from pathlib import Path


def setup_logger(level: str = "INFO") -> None:
    Path("logs").mkdir(exist_ok=True)
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s | %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "default",
                    "filename": "logs/app.log",
                    "maxBytes": 5 * 1024 * 1024,  # 5 МБ
                    "backupCount": 3,
                    "encoding": "utf-8",
                },
            },
            "root": {
                "level": level,
                "handlers": ["console", "file"],
            },
            "loggers": {
                "sqlalchemy.engine": {"level": "WARNING"},
                "uvicorn.access": {"level": "WARNING"},
            },
        }
    )
