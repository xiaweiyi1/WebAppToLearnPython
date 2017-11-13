#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Xiaweiyi'
__date__ = "2017/11/09 "

import orm, asyncio
from models import User, Blog, Comment


async def test(loop):
    await orm.create_pool(loop=loop, user='root', password='woaini1314', db='awesome')
    u = User(name='Test', email='test@example.com', passwd='1234567890', image='about:blank')
    await u.save()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()