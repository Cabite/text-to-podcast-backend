"""python -m app.bootstrap：迁移数据库并初始化固定测试身份、模型及角色。"""
from alembic import command
from alembic.config import Config

from app.core.config import ROOT, Settings
from app.db.database import Database
from app.db.seed import seed


def initialize(settings=None):
    settings = settings or Settings.from_env()
    database = Database(settings.database_url)
    try:
        cfg = Config(str(ROOT / "alembic.ini"))
        with database.engine.begin() as connection:
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "head")
        seed(database, settings)
    finally:
        database.engine.dispose()


if __name__ == "__main__":
    initialize()
    print("数据库迁移和测试数据初始化完成。分别启动 API 与 Worker。")
