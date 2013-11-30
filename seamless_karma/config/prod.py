# production configuration

import os

DEBUG = False
SECRET_KEY = os.environ.get("SECRET_KEY", '\x1c\x19\x90\xaf\x1c\x03(\xbc\n\xf03\x9e\x08,\xafgO\xf0\xb7\xaar\x8b\xc5\x9d')
CACHE_TYPE = "redis"
CACHE_REDIS_URL = os.environ.get("REDISCLOUD_URL")
