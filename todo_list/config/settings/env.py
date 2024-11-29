from pathlib import Path
import os
import environ

env = environ.Env()

BASE_DIR = Path(__file__).resolve()

if os.getenv('READ_ENV_LOCAL'):
    if os.path.exists(os.path.join(BASE_DIR, '.env.local')):
        environ.Env.read_env(os.path.join(BASE_DIR, '.env.local'))
    else:
        environ.Env.read_env(os.path.join(BASE_DIR.parent, '.env.local'))
else:
    if os.path.exists(os.path.join(BASE_DIR, '.env')):
        environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
    else:
        environ.Env.read_env(os.path.join(BASE_DIR.parent, '.env'))
