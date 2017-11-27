#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Xiaweiyi'
__date__ = "2017/11/09 "

import aiomysql
import asyncio

loop = asyncio.get_event_loop()


def test_example():
    conn = aiomysql.connect(host='127.0.0.1', port=3306, user='root', password='woaini1314', db='awesome', loop=loop)
    cur = conn.cursor()
    cur.execute('select * from users')
    print(cur.description)
    r = cur.fetchall()
    print(r)
    cur.close()
    conn.close()

#loop.run_until_complete(test_example())
test_example()