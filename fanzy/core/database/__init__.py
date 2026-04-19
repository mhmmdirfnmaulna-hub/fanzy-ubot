from motor.motor_asyncio import AsyncIOMotorClient

from fanzy.config import MONGO_URL

mongo_client = AsyncIOMotorClient(MONGO_URL)
mongodb = mongo_client.userbotxx

from fanzy.core.database.expired import *
from fanzy.core.database.userbot import *
from fanzy.core.database.two_factor import *
from fanzy.core.database.pref import *
from fanzy.core.database.variabel import *
from fanzy.core.database.antigcast import *