from typing import Any

import aiomysql, logging

import asyncio



async def create_pool(loop, **kw):
    '''create database connection pool'''

    global __pool
    __pool = await aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )

'''
CREATE TABLE IF NOT EXISTS `runoob_tbl`(
   `runoob_id` INT UNSIGNED AUTO_INCREMENT,
   `runoob_title` VARCHAR(100) NOT NULL,
   `runoob_author` VARCHAR(40) NOT NULL,
   `submission_date` DATE,
   PRIMARY KEY ( `runoob_id` )
)ENGINE=InnoDB DEFAULT CHARSET=utf8;
'''


async def select(sql, args, size):
    global __pool
    async with __pool.get() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql.replace('?', '%s'), args or ())
            if size:
                rs = cur.fetchmany(size)
            else:
                rs = cur.fetchall()
            return rs


async def execute(sql, args):
    global __pool
    with (await __pool) as conn:
        cur = conn.cursor()
        cur.execute(sql.replace('?', '%s'), args or ())
        affected = cur.rowcount
        await cur.close()
        return affected


class Field(object):
    def __init__(self, column_type, name=None, primary_key=False):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key

    def __str__(self) -> str:
        return '<%s, %s, %s>'%(self.__class__.__name__, self.name, self.column_type)


class StringField(Field):
    def __init__(self, name=None, primary_key=False, ddl='varchar(100)'):
        super().__init__(ddl, name=name, primary_key=primary_key)


class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs) -> Any:
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        table_name = attrs.get('__table__') or name.lower()
        mappings = dict()
        fields = []
        primary_key = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                if not v.name:
                    v.name = k
                mappings[k] = v
                if v.primary_key:
                    primary_key = k
                else:
                    fields.append(k)

        for k in mappings.keys():
            attrs.pop(k)

        escaped_fields = ', '.join(map(lambda f: '`%s`' % f, fields))
        attrs['__table__'] = table_name
        attrs['__mappings__'] = mappings
        attrs['__primary_key__'] = primary_key
        attrs['__fields__'] = fields
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primary_key, escaped_fields, table_name)
        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):

    @classmethod
    async def find(cls, pk):
        rc = await select('%s where `%s` = ?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if not rc:
            return None
        return cls(rc)


class User(Model):
    id = StringField(primary_key=True)
    name = StringField()
    password = StringField()


async def test():
    user = await User.find('1')
    print(user)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_pool(loop, user='root', password='111111', db='awsome_python3_webapp'))
    tasks = [test()]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

