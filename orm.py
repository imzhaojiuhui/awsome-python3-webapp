from typing import Any

import aiomysql, logging; logging.basicConfig(level=logging.INFO)

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


async def select(sql, args, size):
    global __pool
    async with __pool.get() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            logging.info('execute sql %s'%sql)
            logging.info('args:%s'%args)
            await cur.execute(sql.replace('?', '%s'), args or ())
            if size:
                rs = await cur.fetchmany(size)
            else:
                rs = await cur.fetchall()
            logging.info('result set:%s'%rs)
            return rs


async def execute(sql, args=None):
    global __pool
    async with __pool.get() as conn:
        async with conn.cursor() as cur:
            logging.info('execute sql: %s'%sql)
            logging.info('args:%s'%args)
            await cur.execute(sql.replace('?', '%s'), args or ())
            affected = cur.rowcount
            return affected


def gen_args_string(num):
    args = []
    for i in range(num):
        args.append('?')

    return ', '.join(args)



class Field(object):
    def __init__(self, column_type, default, name=None, primary_key=False):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self) -> str:
        return '<%s, %s, %s>'%(self.__class__.__name__, self.name, self.column_type)


class StringField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
        super().__init__(ddl, default, name=name, primary_key=primary_key)


class IntegerField(Field):

    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__('bigint', default, name, primary_key)


class PrimaryKey(Field):

    def __init__(self, name=None):
        super().__init__('INT UNSIGNED AUTO_INCREMENT', 0, name, primary_key=True)


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
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)'%(table_name, escaped_fields, primary_key, gen_args_string(len(fields)+1))
        attrs['__create_table__'] = '''
        CREATE TABLE IF NOT EXISTS `%s`(
           `%s` %s,
           %s,
           PRIMARY KEY ( `%s` )
        );
        ''' % (table_name, primary_key, mappings.get(primary_key).column_type, ','.join(map(lambda f:'`%s` %s'%(f, mappings[f].column_type), fields)) ,primary_key)
        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):

    @classmethod
    async def find(cls, pk):
        rs = await select('%s where `%s` = ?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if not rs:
            return None
        return cls(**rs[0])

    @classmethod
    async def create_table(cls):
        await execute(cls.__create_table__)

    @classmethod
    async def refresh_table_stru(cls):
        await execute('drop table if exists `%s`'%cls.__table__)
        await cls.create_table()


    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(r'object has not attribute %s'%name)

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.info('use default value %s'%value)
                setattr(self, key, value)
        return value

    async def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        logging.info('%s'%self.getValueOrDefault('name'))
        args.append(self.getValueOrDefault(self.__primary_key__))
        affected = await execute(self.__insert__, args=args)
        if affected != 1:
            logging.warning('insert failed')


class User(Model):
    id = PrimaryKey()
    name = StringField()
    password = StringField()


async def test_setup():
    await User.refresh_table_stru()


async def test():
    user1 = User(name='zhaojiuhui', password='111111')
    print(user1)
    await user1.save()
    user = await User.find(1)
    print(user)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_pool(loop, user='root', password='111111', db='awsome_python3_webapp'))
    # loop.run_until_complete(test_setup())
    tasks = [test()]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

