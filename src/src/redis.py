import redis
import os

REDIS = redis.StrictRedis(
    host=os.environ.get("REDIS_HOST"),
    port=os.environ.get("REDIS_PORT"),
    password=os.environ.get("REDIS_PASS"),
)
