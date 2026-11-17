import os
os.environ["SECRET_KEY"] = "dev-secret-key-do-not-use-in-production"

import uvicorn
uvicorn.run("olenevod.interfaces.http.app:app", host="127.0.0.1", port=8001)
