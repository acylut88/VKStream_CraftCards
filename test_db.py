import asyncio
from database import DatabaseManager
import aiosqlite

async def test():
    db = DatabaseManager()
    await db.init_db()
    print('✅ Database initialized successfully')
    
    # Check tables
    async with aiosqlite.connect('stream_game.db') as conn:
        async with conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name") as cursor:
            tables = await cursor.fetchall()
            print('\n📋 Tables created:')
            for t in tables:
                print(f'   ✓ {t[0]}')

asyncio.run(test())
