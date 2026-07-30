import asyncio
import os
from pathlib import Path
import asyncpg
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')


async def main():
    database_url = os.environ['DATABASE_URL']
    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    sql = (ROOT_DIR / 'migrations' / 'schema.sql').read_text()
    await conn.execute(sql)
    await conn.close()
    print('MIGRATION_OK')


if __name__ == '__main__':
    asyncio.run(main())
