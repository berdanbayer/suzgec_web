from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
import os
from datetime import datetime, timedelta
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from flask_wtf.csrf import CSRFProtect
from forms import RegistrationForm, LoginForm
from flask_wtf import FlaskForm

# --- 1. UZANTILARI (EXTENSIONS) SADECE TANIMLIYORUZ (FABRİKA İÇİN) ---
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
migrate = Migrate()
mail = Mail()
csrf = CSRFProtect()

# --- 2. VERİTABANI MODELLERİ ---
class User(db.Model, UserMixin):
    __table_args__ = {'extend_existing': True} 
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    profile_image = db.Column(db.String(120), default='default.jpg')
    records = db.relationship('DailyRecord', back_populates='author', lazy=True)
    goals = db.relationship('Goal', back_populates='user', uselist=False)

    def get_reset_token(self):
        # NOT: Burada current_app kullanmak daha doğrudur ama import etmemek için app config'i factory içinde okuyacağız.
        from flask import current_app
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}, salt='password-reset-salt')

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        from flask import current_app
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, salt='password-reset-salt', max_age=expires_sec)['user_id']
        except:
            return None
        return User.query.get(user_id)

class DailyRecord(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    date_str = db.Column(db.String(20), nullable=False)
    mood = db.Column(db.String(20))
    sleep_start = db.Column(db.String(10))
    sleep_end = db.Column(db.String(10))
    screen_time = db.Column(db.Float)
    water = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', back_populates='records')

class Goal(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sleep_goal = db.Column(db.Float, default=8.0)
    water_goal = db.Column(db.Integer, default=8)
    screen_goal = db.Column(db.Float, default=4.0)
    user = db.relationship('User', back_populates='goals')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- DİL (ÇEVİRİ) SÖZLÜĞÜ ---
DIL_SOZLUGU = {
    'tr': {
        'menu_ana_sayfa': 'Ana Sayfa', 'menu_grafikler': 'Grafikler', 'menu_arama': 'Kayıtlarda Ara',
        'menu_hedefler': 'Hedefler', 'menu_yardim': 'Yardım', 'menu_ayarlar': 'Ayarlar', 'menu_cikis': 'Çıkış Yap',
        'ayarlar_baslik': 'Ayarlar ve Profil', 'durum': 'Durum:', 'aktif': 'Aktif Kullanıcı',
        'gorunum': 'Görünüm Ayarları', 'acik_tema': 'Açık Tema', 'koyu_tema': 'Koyu Tema',
        'guvenlik': 'Hesap Güvenliği', 'sifre_guncelle': 'Şifre Güncelle', 'dil_ayarlari': 'Dil Ayarları'
    },
    'en': {
        'menu_ana_sayfa': 'Dashboard', 'menu_grafikler': 'Charts', 'menu_arama': 'Search Records',
        'menu_hedefler': 'Goals', 'menu_yardim': 'Help', 'menu_ayarlar': 'Settings', 'menu_cikis': 'Logout',
        'ayarlar_baslik': 'Settings and Profile', 'durum': 'Status:', 'aktif': 'Active User',
        'gorunum': 'Appearance Settings', 'acik_tema': 'Light Theme', 'koyu_tema': 'Dark Theme',
        'guvenlik': 'Account Security', 'sifre_guncelle': 'Update Password', 'dil_ayarlari': 'Language Settings'
    }
}

# --- 3. APPLICATION FACTORY (UYGULAMA FABRİKASI) ---
def create_app():
    app = Flask(__name__)

    # --- AYARLAR ---
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/profile_pics')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) 
    app.config['SECRET_KEY'] = 'suzgec-cok-gizli-anahtar-123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///suzgec.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'bayerberdan@gmail.com'
    app.config['MAIL_PASSWORD'] = 'egce uecs cseg yhiy' 
    app.config['MAIL_DEFAULT_SENDER'] = 'bayerberdan@gmail.com'

    # --- UZANTILARI APP'E BAĞLAMA ---
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    csrf.init_app(app)

    # --- BLUEPRINT KAYDI ---
    from errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    # --- GLOBAL FONKSİYONLAR ---
    @app.before_request
    def varsayilan_dil_belirle():
        if 'dil' not in session: session['dil'] = 'tr'

    @app.context_processor
    def dil_verilerini_gonder():
        secili_dil = session.get('dil', 'tr')
        return dict(t=DIL_SOZLUGU[secili_dil], mevcut_dil=secili_dil)

    @app.after_request
    def add_header(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    @app.context_processor
    def inject_now():
        aylar = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        bugun = datetime.now()
        return {'bugunun_tarihi': f"{bugun.day} {aylar[bugun.month]} {bugun.year}", 'bugunun_saati': bugun.strftime("%H:%M")}

    # --- ROTALAR ---
    @app.route('/', methods=['GET', 'POST'])
    @login_required
    def home():
        bugun_str = datetime.now().strftime("%Y-%m-%d")
        gunluk_veri = DailyRecord.query.filter_by(user_id=current_user.id, date_str=bugun_str).first()
        guvenlik_formu = FlaskForm()

        if request.method == 'POST':
            uyku_baslangic = request.form.get('sleep_start')
            uyku_bitis = request.form.get('sleep_end')
            ekran_suresi = request.form.get('screen_time')
            su_miktari = request.form.get('water_count')
            ruh_hali = request.form.get('mood_status')
            
            if gunluk_veri:
                gunluk_veri.sleep_start = uyku_baslangic
                gunluk_veri.sleep_end = uyku_bitis
                gunluk_veri.screen_time = float(ekran_suresi) if ekran_suresi else 0.0
                gunluk_veri.water = int(su_miktari) if su_miktari else 0
                gunluk_veri.mood = ruh_hali
            else:
                yeni_kayit = DailyRecord(date_str=bugun_str, sleep_start=uyku_baslangic, sleep_end=uyku_bitis, screen_time=float(ekran_suresi) if ekran_suresi else 0.0, water=int(su_miktari) if su_miktari else 0, mood=ruh_hali, author=current_user)
                db.session.add(yeni_kayit)
            db.session.commit()
            return redirect(url_for('home'))
        return render_template('index.html', veri=gunluk_veri, form=guvenlik_formu)

    @app.route('/arama')
    @login_required
    def arama():
        arama_kelimesi = request.args.get('q', '')
        page = request.args.get('page', 1, type=int) 
        sonuclar = None
        if arama_kelimesi:
            sonuclar = DailyRecord.query.filter(
                DailyRecord.user_id == current_user.id, DailyRecord.mood.ilike(f'%{arama_kelimesi}%')
            ).order_by(DailyRecord.date_str.desc()).paginate(page=page, per_page=6, error_out=False)
        return render_template('arama.html', sonuclar=sonuclar, arama_kelimesi=arama_kelimesi)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated: return redirect(url_for('home'))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('home'))
        return render_template('login.html', form=form)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated: return redirect(url_for('home'))
        form = RegistrationForm()
        if form.validate_on_submit():
            if not User.query.filter_by(email=form.email.data).first():
                hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                yeni_kullanici = User(fullname=form.fullname.data, email=form.email.data, password=hashed_password)
                db.session.add(yeni_kullanici)
                db.session.commit()
                return redirect(url_for('login'))
        return render_template('register.html', form=form)

    @app.route('/dili_degistir/<yeni_dil>')
    def dili_degistir(yeni_dil):
        if yeni_dil in ['tr', 'en']: session['dil'] = yeni_dil
        return redirect(request.referrer or url_for('home'))

    @app.route('/grafikler')
    @login_required
    def grafikler():
        son_kayitlar = DailyRecord.query.filter_by(user_id=current_user.id).order_by(DailyRecord.date_str.desc()).limit(7).all()
        son_kayitlar.reverse()
        return render_template('grafikler.html', tarihler=[k.date_str[-5:] for k in son_kayitlar], su_verileri=[k.water for k in son_kayitlar], ekran_verileri=[k.screen_time for k in son_kayitlar])

    @app.route('/api/grafikler')
    @login_required
    def api_grafikler():
        periyot = request.args.get('periyot', 'haftalik')
        bugun = datetime.now()
        gun_farki = {'haftalik': 7, 'aylik': 30, '3aylik': 90, '6aylik': 180, 'yillik': 365}.get(periyot, 7)
        baslangic_str = (bugun - timedelta(days=gun_farki)).strftime("%Y-%m-%d")
        
        kayitlar = DailyRecord.query.filter(DailyRecord.user_id == current_user.id, DailyRecord.date_str >= baslangic_str).order_by(DailyRecord.date_str.asc()).all()
        
        veri_paketi = {'tarihler': [], 'su': [], 'ekran': [], 'uyku': []}
        for k in kayitlar:
            veri_paketi['tarihler'].append(k.date_str[-5:])
            veri_paketi['su'].append(k.water)
            veri_paketi['ekran'].append(k.screen_time)
            try:
                start = datetime.strptime(k.sleep_start, "%H:%M")
                end = datetime.strptime(k.sleep_end, "%H:%M")
                if end < start: end += timedelta(days=1)
                veri_paketi['uyku'].append(round((end - start).total_seconds() / 3600, 1))
            except: veri_paketi['uyku'].append(0)
        return jsonify(veri_paketi)

    @app.route('/hedefler', methods=['GET', 'POST'])
    @login_required
    def hedefler():
        goal = Goal.query.filter_by(user_id=current_user.id).first()
        guvenlik_formu = FlaskForm()
        if request.method == 'POST':
            if goal:
                goal.sleep_goal = float(request.form.get('sleep_goal', 8.0))
                goal.water_goal = int(request.form.get('water_goal', 8))
                goal.screen_goal = float(request.form.get('screen_goal', 4.0))
            else:
                goal = Goal(user_id=current_user.id, sleep_goal=float(request.form.get('sleep_goal', 8.0)), water_goal=int(request.form.get('water_goal', 8)), screen_goal=float(request.form.get('screen_goal', 4.0)))
                db.session.add(goal)
            db.session.commit()
            return redirect(url_for('hedefler'))
        return render_template('hedefler.html', goal=goal, form=guvenlik_formu)

    @app.route('/ayarlar', methods=['GET', 'POST'])
    @login_required
    def ayarlar():
        guvenlik_formu = FlaskForm()
        if request.method == 'POST' and 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                pic_name = f"user_{current_user.id}_{filename}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], pic_name))
                current_user.profile_image = pic_name
                db.session.commit()
            return redirect(url_for('ayarlar'))
        return render_template('ayarlar.html', form=guvenlik_formu)

    @app.route('/sifre', methods=['GET', 'POST'])
    @login_required
    def sifre():
        guvenlik_formu = FlaskForm()
        if request.method == 'POST':
            if bcrypt.check_password_hash(current_user.password, request.form.get('current_password')) and request.form.get('new_password') == request.form.get('new_password_confirm'):
                current_user.password = bcrypt.generate_password_hash(request.form.get('new_password')).decode('utf-8')
                db.session.commit()
            return redirect(url_for('ayarlar'))
        return render_template('sifre.html', form=guvenlik_formu)

    @app.route('/yardim')
    @login_required
    def yardim(): return render_template('yardim.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user() 
        return redirect(url_for('login'))

    def send_reset_email(user):
        token = user.get_reset_token()
        msg = Message('Süzgeç - Şifre Sıfırlama Talebi', recipients=[user.email])
        msg.body = f"Şifrenizi sıfırlamak için aşağıdaki bağlantıya tıklayın:\n{url_for('reset_token', token=token, _external=True)}\nEğer bu talebi siz yapmadıysanız, bu e-postayı görmezden gelebilirsiniz."
        mail.send(msg)

    @app.route("/reset_password", methods=['GET', 'POST'])
    def reset_request():
        if current_user.is_authenticated: return redirect(url_for('home'))
        guvenlik_formu = FlaskForm()
        if request.method == 'POST':
            user = User.query.filter_by(email=request.form.get('email')).first()
            if user: send_reset_email(user)
            return redirect(url_for('login'))
        return render_template('reset_request.html', form=guvenlik_formu)

    @app.route("/reset_password/<token>", methods=['GET', 'POST'])
    def reset_token(token):
        if current_user.is_authenticated: return redirect(url_for('home'))
        user = User.verify_reset_token(token)
        if user is None: return redirect(url_for('reset_request'))
        guvenlik_formu = FlaskForm()
        if request.method == 'POST':
            if request.form.get('password') == request.form.get('password_confirm'):
                user.password = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
                db.session.commit()
                return redirect(url_for('login'))
        return render_template('reset_token.html', form=guvenlik_formu)

    with app.app_context():
        db.create_all()

    return app

# --- 4. UYGULAMAYI ÇALIŞTIRMA ---
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)