mods = ['fastapi', 'uvicorn', 'sqlalchemy', 'pydantic_settings', 'jwt', 'alembic', 'asyncpg', 'redis', 'passlib', 'bcrypt', 'python-jose', 'psycopg']
for m in mods:
    try:
        mod = __import__(m)
        print('OK', m, getattr(mod, '__version__', ''))
    except Exception as e:
        print('MISSING', m, e)
