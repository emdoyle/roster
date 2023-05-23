from environs import Env

env = Env()
env.read_env()

DEBUG = env.bool("ROSTER_API_DEBUG", False)

PORT = env.int("ROSTER_API_PORT", 7888)

ETCD_HOST = env.str("ROSTER_API_ETCD_HOST", "localhost")
ETCD_PORT = env.int("ROSTER_API_ETCD_PORT", 2379)
