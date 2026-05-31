from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
import os
from datetime import datetime, timedelta
from flask_migrate import Migrate

app = Flask(__name__)

# --- GÜVENLİK VE VERİTABANI AYARLARI ---
app.config['SECRET_KEY'] = 'suzgec-cok-gizli-anahtar-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///suzgec.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- KÜTÜPHANELERİ ÇALIŞTIRMA ---
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- VERİTABANI TABLOLARI (MODELS) ---

class User(db.Model, UserMixin):
    __table_args__ = {'extend_existing': True} 
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    records = db.relationship('DailyRecord', backref='author', lazy=True)
    goals = db.relationship('Goal', backref='user', uselist=False)

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

class Goal(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sleep_goal = db.Column(db.Float, default=8.0)
    water_goal = db.Column(db.Integer, default=8)
    screen_goal = db.Column(db.Float, default=4.0)

# --- TÜM SAYFALAR İÇİN OTOMATİK DEĞİŞKENLER ---

# app.py içine ekleyin
@app.after_request
def add_header(response):
    """Tarayıcının sayfaları önbelleğe almasını engeller."""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.context_processor
def inject_now():
    aylar = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
             "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    bugun = datetime.now()
    tarih_metni = f"{bugun.day} {aylar[bugun.month]} {bugun.year}"
    saat_metni = bugun.strftime("%H:%M") 
    return {'bugunun_tarihi': tarih_metni, 'bugunun_saati': saat_metni}

# --- ROTALAR (SAYFALAR) ---

@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    bugun_str = datetime.now().strftime("%Y-%m-%d")
    gunluk_veri = DailyRecord.query.filter_by(user_id=current_user.id, date_str=bugun_str).first()

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
            yeni_kayit = DailyRecord(
                date_str=bugun_str,
                sleep_start=uyku_baslangic,
                sleep_end=uyku_bitis,
                screen_time=float(ekran_suresi) if ekran_suresi else 0.0,
                water=int(su_miktari) if su_miktari else 0,
                mood=ruh_hali,
                author=current_user
            )
            db.session.add(yeni_kayit)
        
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('index.html', veri=gunluk_veri)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form_email = request.form.get('email')
        form_password = request.form.get('password')

        user = User.query.filter_by(email=form_email).first()

        if user and bcrypt.check_password_hash(user.password, form_password):
            login_user(user)
            print(f"GİRİŞ BAŞARILI: {user.fullname} sisteme girdi!")
            return redirect(url_for('home'))
        else:
            print("Hata: E-posta veya şifre yanlış!")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form_fullname = request.form.get('fullname')
        form_email = request.form.get('email')
        form_password = request.form.get('password')
        form_password_confirm = request.form.get('passwordConfirm')

        if form_password != form_password_confirm:
            print("Hata: Şifreler eşleşmiyor!")
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(email=form_email).first()
        if existing_user:
            print("Hata: Bu e-posta zaten sistemde var!")
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(form_password).decode('utf-8')

        yeni_kullanici = User(fullname=form_fullname, email=form_email, password=hashed_password)
        db.session.add(yeni_kullanici)
        db.session.commit()

        print(f"BAŞARILI: {form_fullname} sisteme kaydedildi!")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/grafikler')
@login_required
def grafikler():
    son_kayitlar = DailyRecord.query.filter_by(user_id=current_user.id)\
                                    .order_by(DailyRecord.date_str.desc())\
                                    .limit(7).all()
    
    son_kayitlar.reverse()

    tarihler = []
    su_verileri = []
    ekran_verileri = []

    for kayit in son_kayitlar:
        tarihler.append(kayit.date_str[-5:]) 
        su_verileri.append(kayit.water)
        ekran_verileri.append(kayit.screen_time)

    return render_template('grafikler.html', 
                           tarihler=tarihler, 
                           su_verileri=su_verileri, 
                           ekran_verileri=ekran_verileri)

@app.route('/api/grafikler')
@login_required
def api_grafikler():
    periyot = request.args.get('periyot', 'haftalik')
    
    bugun = datetime.now()
    if periyot == 'haftalik':
        baslangic_tarihi = bugun - timedelta(days=7)
    elif periyot == 'aylik':
        baslangic_tarihi = bugun - timedelta(days=30)
    elif periyot == '3aylik':
        baslangic_tarihi = bugun - timedelta(days=90)
    elif periyot == '6aylik':
        baslangic_tarihi = bugun - timedelta(days=180)
    elif periyot == 'yillik':
        baslangic_tarihi = bugun - timedelta(days=365)
    else:
        baslangic_tarihi = bugun - timedelta(days=7)

    baslangic_str = baslangic_tarihi.strftime("%Y-%m-%d")

    kayitlar = DailyRecord.query.filter(
        DailyRecord.user_id == current_user.id,
        DailyRecord.date_str >= baslangic_str
    ).order_by(DailyRecord.date_str.asc()).all()

    veri_paketi = {
        'tarihler': [],
        'su': [],
        'ekran': [],
        'uyku': []
    }

    for kayit in kayitlar:
        veri_paketi['tarihler'].append(kayit.date_str[-5:])
        veri_paketi['su'].append(kayit.water)
        veri_paketi['ekran'].append(kayit.screen_time)
        
        try:
            start = datetime.strptime(kayit.sleep_start, "%H:%M")
            end = datetime.strptime(kayit.sleep_end, "%H:%M")
            if end < start:
                end += timedelta(days=1)
            uyku_saat = round((end - start).total_seconds() / 3600, 1)
            veri_paketi['uyku'].append(uyku_saat)
        except:
            veri_paketi['uyku'].append(0)

    return jsonify(veri_paketi)

@app.route('/hedefler', methods=['GET', 'POST'])
@login_required
def hedefler():
    goal = Goal.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        sleep = float(request.form.get('sleep_goal', 8.0))
        water = int(request.form.get('water_goal', 8))
        screen = float(request.form.get('screen_goal', 4.0))
        
        if goal:
            goal.sleep_goal = sleep
            goal.water_goal = water
            goal.screen_goal = screen
        else:
            goal = Goal(user_id=current_user.id, sleep_goal=sleep, water_goal=water, screen_goal=screen)
            db.session.add(goal)
            
        db.session.commit()
        return redirect(url_for('hedefler'))
        
    return render_template('hedefler.html', goal=goal)

@app.route('/yardim')
@login_required
def yardim():
    return render_template('yardim.html')

@app.route('/ayarlar')
@login_required
def ayarlar():
    return render_template('ayarlar.html')

@app.route('/sifre', methods=['GET', 'POST'])
@login_required
def sifre():
    if request.method == 'POST':
        current_pw = request.form.get('current_password')
        new_pw = request.form.get('new_password')
        new_pw_confirm = request.form.get('new_password_confirm')

        # 1. Mevcut şifre doğrulaması
        if not bcrypt.check_password_hash(current_user.password, current_pw):
            print("Hata: Mevcut şifre yanlış!")
            return redirect(url_for('sifre'))

        # 2. Yeni şifre eşleşme kontrolü
        if new_pw != new_pw_confirm:
            print("Hata: Yeni şifreler eşleşmiyor!")
            return redirect(url_for('sifre'))

        # 3. Şifreyi güncelle
        hashed_pw = bcrypt.generate_password_hash(new_pw).decode('utf-8')
        current_user.password = hashed_pw
        db.session.commit()
        
        print("BAŞARILI: Şifre güncellendi.")
        return redirect(url_for('ayarlar'))

    return render_template('sifre.html')

@app.route('/logout')
@login_required
def logout():
    logout_user() 
    return redirect(url_for('login'))

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)

    # Hata sayfaları modülünü içeri aktar ve uygulamaya kaydet
from errors import bp as errors_bp
app.register_blueprint(errors_bp)