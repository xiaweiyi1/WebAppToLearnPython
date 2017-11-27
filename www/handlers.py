from webcore import get
from webcore import post
from models import User, Blog, next_id
from apis import APIValueError, APIPermissionError
from aiohttp import web
import json
import re
import asyncio
import time
import hashlib
import config
import logging


COOKIE_NAME = 'awesession'
_COOKIE_KEY = config.configs.get('session').get('secret')


def user2cookie(user, max_age):
    '''
    Generate cookie str by user.
    '''
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)


@asyncio.coroutine
def cookie2user(cookie_str):
    '''
    Parse cookie and load user if cookie is valid.
    '''
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = yield from User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None


@get('/')
def index(request):
    summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    blogs = [
        Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
        Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200)
    ]
    return {
        '__template__': 'blogs.html',
        'blogs': blogs,
        'user': request.__user__
    }


@get('/users')
async def api_get_users():
    users = await User.findAll(orderBy='created_at desc')
    for u in users:
        u.passwd='******'
    return dict(users=users)


_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')


@get('/register')
async def regist():
    return {
        '__template__': 'regist.html'

    }


@get('/signin')
async def signin():
    return {
        '__template__': 'signin.html'
    }


@post('/api/users')
async def api_register(*, email, name, passwd):
    if not name :
        raise APIValueError
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError
    users = await User.findAll('email=?', [email])
    if len(users)>0:
        raise APIValueError('regist fail:email', 'email is already used.')
    uid = next_id()
    shal_paswd = '%s:%s' % (uid, passwd)
    user = User(id=uid, name=name, email=email, passwd=hashlib.sha1(shal_paswd.encode('utf-8')).hexdigest(),image='about:blank')
    await user.save()
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


@post('/api/loggin')
async def loggin(*, email, passwd):
    if not email:
        raise APIValueError('email', "Email can't be empty")
    if not passwd:
        raise APIValueError('passwd',"Password can't be empty")
    users = await User.findAll('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'User not exist or password is error ')
    user=users[0]
    shal = hashlib.sha1()
    shal.update(user.id.encode('utf-8'))
    shal.update(b':')
    shal.update(passwd.encode('utf-8'))
    if user.passwd != shal.hexdigest():
        raise APIValueError('passwd', 'User not exist or password is error')
    r = web.Response()
    r.set_cookie(COOKIE_NAME,user2cookie(user,86400), max_age=86400, httponly=True)
    user.passwd='******'
    r.content_type='application/json'
    r.body=json.dumps(user,ensure_ascii=False).encode('utf-8')
    return r


@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r


def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()


@post('/api/blogs')
async def api_create_blog(request, *, name, summary, content):
    check_admin(request)
    if not name or not name.strip():
        raise APIValueError()
    if not summary or not summary.strip():
        raise  APIValueError()
    if not content or not content.strip():
        raise APIValueError()
    blog=Blog(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__.image,  name=name.strip(), summary=summary.strip(), content=content.strip())
    await blog.save()
    return blog


@get('/blog_edite')
async def blog_edite(request):
    return {
        '__template__': 'blog_edite.html',
        'user': request.__user__

    }
