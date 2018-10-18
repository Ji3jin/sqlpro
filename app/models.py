#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : forms.py
# Author: jixin
# Date  : 18-10-17
from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import request, current_app
from flask_login import UserMixin
from . import db, login_manager


class Serializable(object):
    class FieldNotFound(Exception):
        pass

    def serialize(self, fields=[]):
        if not fields:
            fields = [f.name for f in self._meta.get_fields()
                      if not (f.auto_created or
                              f.many_to_many or
                              f.many_to_one)]
        allowed = set(fields) - set(getattr(self, '_api_hidden_fields', []))
        grouped = {}
        for field in allowed:
            if '.' not in field:
                grouped[field] = False
                continue
            k, v = field.split('.', 1)
            grouped.setdefault(k, []).append(v)

        d = {}
        for field, keys in grouped.items():
            d[field] = self.get_value(field, keys)
        return d

    def get_value(self, name, keypath):
        if keypath:
            field = self._meta.get_field(name)
            if field.many_to_one:
                return getattr(self, field.name).serialize(keypath)
            if field.many_to_many:
                return [val.serialize(keypath) for val in
                        getattr(self, field.name).all()]
            raise Serializable.FieldNotFound(
                "%s is not a relation field." % name)
        else:
            field = self._meta.get_field(name)
            return getattr(self, field.name)


class User(UserMixin, db.Model, Serializable):
    __tablename__ = 't_user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64),
                         nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_api_token(self, expiration=300):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'user': self.id}).decode('utf-8')

    @staticmethod
    def validate_api_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        id = data.get('user')
        if id:
            return User.query.get(id)
        return None


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
