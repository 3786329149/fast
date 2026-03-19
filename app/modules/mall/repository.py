from sqlalchemy.ext.asyncio import AsyncSession


class MallRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
