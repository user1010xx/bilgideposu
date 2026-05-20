import os
import sys
import tempfile

_tmp = tempfile.mkdtemp(prefix="bilgibotu_test_")
os.environ["BOT_TOKEN"] = "000000000:TEST"
os.environ["ADMIN_IDS"] = "1"
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"

for name in list(sys.modules.keys()):
    if name == "bot" or name.startswith("bot."):
        del sys.modules[name]
