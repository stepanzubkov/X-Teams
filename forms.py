from flask_wtf import FlaskForm
from flask import request
from wtforms import StringField, SubmitField, BooleanField, TextAreaField, FileField, PasswordField, SelectField, RadioField, ValidationError
from wtforms.validators import DataRequired, Email, Length, NoneOf

from requests import get


class Github(object):
    def __init__(self, message=None):
        if not message:
            message = 'Не существует такого аккаунта'
        self.message = message

    def __call__(self, form, field):
        data = field.data
        URL = f'https://github.com/{data}'
        HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.43 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36 OPR/77.0.4054.277'}
        status = get(URL, headers=HEADERS).status_code
        if status == 404:
            raise ValidationError(self.message)
        
class Extensions(object):
    def __init__(self, message=None, ext=[]):
        if not message:
            message = 'Неправильный формат файла'
        self.message = message
        self.extensions = ext

    def __call__(self, form, field):
        if field.data:
            filename = request.files[field.name].filename
            ext = filename.split('.')[1]
            if ext not in self.extensions:
                raise ValidationError(self.message)


class RegistrationForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired('Пустое поле'), Length(min=4, max=100, message='Неверная длинна имени')])
    github_name = StringField('Имя на github', validators=[DataRequired('Пустое поле'), Length(min=4, max=100, message='Неверная длинна имени'), Github()])
    email = StringField('Email', validators=[DataRequired('Пустое поле'), Email(message='Неправильный email'), Length(min=4, max=100, message='Неверная длинна email')])
    password = PasswordField('Пароль', validators=[DataRequired(message='Пустое поле'), Length(min=4, max=100, message='Неверная длинна пароля')])
    specialization = SelectField('Специализация', choices=[
                                                            ('Backend', '-- Специализация --'),
                                                            ('Backend', 'Backend'),
                                                            ('Frontend', 'Frontend'),
                                                            ('Мобильная разработка', 'Мобильная разработка'),
                                                            ('Веб-дизайн', 'Веб-дизайн'),
                                                            ('Плагины/утилиты', 'Плагины/утилиты'),
                                                            ('Разработка игр','Разработка игр'),
                                                            ('Гейм-дизайн','Гейм-дизайн')
                                                            ])
    expirience = RadioField('Опыт', choices=[
        ('Junior', 'Junior'),
        ('Middle', 'Middle'),
        ('Senior', 'Senior')
    ])
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired('Пустое поле'), Email(message='Неправильный email'), Length(min=4, max=100, message='Неверная длинна email')])
    password = PasswordField('Пароль', validators=[DataRequired(message='Пустое поле'), Length(min=4, max=100, message='Неверная длинна пароля')])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class EditForm(FlaskForm):
    avatar = FileField('Аватар', validators=[Extensions(ext=['png'])])
    name = StringField('Имя', validators=[DataRequired('Пустое поле'), Length(min=4, max=100, message='Неверная длинна имени')])
    github = StringField('Имя на github', validators=[DataRequired('Пустое поле'), Length(min=4, max=100, message='Неверная длинна имени'), Github()])
    email = StringField('Email', validators=[DataRequired('Пустое поле'), Email(message='Неправильный email'), Length(min=4, max=100, message='Неверная длинна email')])
    password = PasswordField('Пароль', validators=[Length(min=0, max=100, message='Неверная длинна пароля')])
    specialization = SelectField('Специализация', choices=[
                                                            ('-', '-'),
                                                            ('Backend', 'Backend'),
                                                            ('Frontend', 'Frontend'),
                                                            ('Мобильная разработка', 'Мобильная разработка'),
                                                            ('Веб-дизайн', 'Веб-дизайн'),
                                                            ('Плагины/утилиты', 'Плагины/утилиты'),
                                                            ('Разработка игр','Разработка игр'),
                                                            ('Гейм-дизайн','Гейм-дизайн')
                                                            ])
    expirience = RadioField('Опыт', choices=[
        ('Junior', 'Junior'),
        ('Middle', 'Middle'),
        ('Senior', 'Senior')
    ])
    stack = StringField('Стек (разделяя запятой)', validators=[Length(min=0, max=100, message='Неправильная длинна стека')])
    submit = SubmitField('Зарегистрироваться')