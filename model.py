#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time

from orm import Model, StringField, IntegerField, TextField, FloatField


class BaseModel(Model):
    create_at = FloatField(default=time.time)


class User(Model):
    name = StringField(ddl='varchar(50)')
    password = StringField(ddl='varchar(50)')
    type = IntegerField()
    email = StringField(ddl='varchar(50)')
    image = StringField(ddl='varchar(500)')


class Blog(Model):
    user_id = IntegerField()
    name = StringField(ddl='varchar(50)')
    summary = StringField(ddl='varchar(200)')
    content = TextField()


class Comment(Model):
    blog_id = IntegerField()
    user_id = IntegerField()
    content = TextField()

