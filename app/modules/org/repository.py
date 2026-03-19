from sqlalchemy.ext.asyncio import AsyncSession


class OrgRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
