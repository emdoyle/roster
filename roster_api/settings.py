import logging

from environs import Env

env = Env()
env.read_env()

DEBUG = env.bool("ROSTER_API_DEBUG", False)
SERVER_LOG = env.str("ROSTER_API_SERVER_LOG", "app.log")
SERVER_LOG_LEVEL = getattr(
    logging, env.str("ROSTER_API_SERVER_LOG_LEVEL", "DEBUG"), "DEBUG"
)

PORT = env.int("ROSTER_API_PORT", 7888)

ETCD_HOST = env.str("ROSTER_API_ETCD_HOST", "localhost")
ETCD_PORT = env.int("ROSTER_API_ETCD_PORT", 2379)
