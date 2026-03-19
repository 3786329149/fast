from sqlalchemy.ext.asyncio import AsyncSession


class SystemRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
