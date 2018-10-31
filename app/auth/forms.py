#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : forms.py
# Author: jixin
# Date  : 18-10-17
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length
from .models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=16)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=16)])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField(label=u'Login')

    def validate_username(self, field):
        if not self.get_user():
            raise ValidationError('Invalid username!')

    def validate_password(self, field):
        if not self.get_user():
            return
        if not self.get_user().check_password(field.data):
            raise ValidationError('Incorrect password!')

    def get_user(self):
        return User.query.filter_by(username=self.username.data).first()


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(4, 16)])
    password = PasswordField('Password', validators=[DataRequired(), Length(6, 16)])
    password_confirm = PasswordField('ConfirmPassword', validators=[DataRequired(), Length(6, 16)])
    submit = SubmitField(label=u'Submit')
