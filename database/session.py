from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from config import config

engine = create_async_engine(config.DB_URL, echo=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session