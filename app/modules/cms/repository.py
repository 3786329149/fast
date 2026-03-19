from sqlalchemy.ext.asyncio import AsyncSession


class CMSRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
