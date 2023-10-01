import logging

from environs import Env

env = Env()
env.read_env()

DEBUG = env.bool("DEBUG", False)
SERVER_LOG = env.str("SERVER_LOG", "app.log")
SERVER_LOG_LEVEL = getattr(
    logging, env.str("SERVER_LOG_LEVEL", "DEBUG"), "DEBUG"
)

WORKSPACE_DIR = env.str("WORKSPACE_DIR", "/tmp/roster-workspace")

PORT = env.int("PORT", 7888)

ETCD_HOST = env.str("ETCD_HOST", "localhost")
ETCD_PORT = env.int("ETCD_PORT", 2379)

POSTGRES_HOST = env.str("POSTGRES_HOST", "localhost")
POSTGRES_PORT = env.int("POSTGRES_PORT", 5432)
POSTGRES_USER = env.str("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = env.str("POSTGRES_PASSWORD", "")
POSTGRES_DB = env.str("POSTGRES_DB", "rosterdb")

RABBITMQ_USER = env.str("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = env.str("RABBITMQ_PASSWORD", "guest")
RABBITMQ_HOST = env.str("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = env.int("RABBITMQ_PORT", 5672)
RABBITMQ_VHOST = env.str("RABBITMQ_VHOST", "/")

GITHUB_APP_PRIVATE_KEY = env.str("GITHUB_APP_PRIVATE_KEY", "private_key.pem")
GITHUB_APP_ID = env.int("GITHUB_APP_ID", 123456)
GITHUB_APP_WEBHOOK_SECRET = env.str("GITHUB_APP_WEBHOOK_SECRET", "turquoise")
GITHUB_APP_NAME = env.str("GITHUB_APP_NAME", "roster-ai")
