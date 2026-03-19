from sqlalchemy.ext.asyncio import AsyncSession


class FileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
