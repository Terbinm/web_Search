from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

class LoginForm(FlaskForm):
    """使用者登入表單"""
    email = StringField('電子郵件', validators=[
        DataRequired(message='請輸入電子郵件'),
        Email(message='請輸入有效的電子郵件地址')
    ])
    password = PasswordField('密碼', validators=[
        DataRequired(message='請輸入密碼')
    ])
    remember = BooleanField('記住我')
    submit = SubmitField('登入')


class RegistrationForm(FlaskForm):
    """使用者註冊表單"""
    username = StringField('使用者名稱', validators=[
        DataRequired(message='請輸入使用者名稱'),
        Length(min=3, max=64, message='使用者名稱長度必須在3到64個字元之間')
    ])
    email = StringField('電子郵件', validators=[
        DataRequired(message='請輸入電子郵件'),
        Email(message='請輸入有效的電子郵件地址'),
        Length(max=120, message='電子郵件長度不能超過120個字元')
    ])
    password = PasswordField('密碼', validators=[
        DataRequired(message='請輸入密碼'),
        Length(min=8, message='密碼長度至少需要8個字元')
    ])
    confirm_password = PasswordField('確認密碼', validators=[
        DataRequired(message='請確認密碼'),
        EqualTo('password', message='兩次輸入的密碼不一致')
    ])
    accept_terms = BooleanField('我同意服務條款和隱私政策', validators=[
        DataRequired(message='您必須同意服務條款和隱私政策才能註冊')
    ])
    submit = SubmitField('註冊')