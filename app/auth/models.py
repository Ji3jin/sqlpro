#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : models.py
# Author: jixin
# Date  : 18-10-19
from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from .. import db, login_manager
from ..core.basemodel import Serializable


class User(UserMixin, db.Model, Serializable):
    __tablename__ = 't_user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64),
                         nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(128))
    create_time = db.Column(db.DateTime, default=datetime.now)

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
