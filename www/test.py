import orm
from models import User, Blog, Comment
from orm import create_pool
import asyncio


async def test(lp):
    await create_pool(lp)
    u = User(name='Test', email='test@example.com', passwd='123456', image='about:blank')
    await u.save()


loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()
