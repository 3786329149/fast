from sqlalchemy.ext.asyncio import AsyncSession


class NotifyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
