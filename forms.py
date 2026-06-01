from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class RegistrationForm(FlaskForm):
    fullname = StringField('Ad Soyad', validators=[DataRequired(message="Bu alan zorunludur."), Length(min=2, max=100)])
    email = StringField('E-posta', validators=[DataRequired(message="Bu alan zorunludur."), Email(message="Geçerli bir e-posta adresi giriniz.")])
    password = PasswordField('Şifre', validators=[DataRequired(message="Bu alan zorunludur."), Length(min=6, message="Şifre en az 6 karakter olmalıdır.")])
    confirm_password = PasswordField('Şifre (Tekrar)', validators=[DataRequired(message="Bu alan zorunludur."), EqualTo('password', message='Şifreler eşleşmiyor.')])
    submit = SubmitField('Kayıt Ol')

class LoginForm(FlaskForm):
    email = StringField('E-posta', validators=[DataRequired(message="Bu alan zorunludur."), Email(message="Geçerli bir e-posta adresi giriniz.")])
    password = PasswordField('Şifre', validators=[DataRequired(message="Bu alan zorunludur.")])
    submit = SubmitField('Giriş Yap')
