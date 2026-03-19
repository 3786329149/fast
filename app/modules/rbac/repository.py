from sqlalchemy.ext.asyncio import AsyncSession


class RBACRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
