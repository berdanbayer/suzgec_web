from app import app, db, User, DailyRecord
from datetime import datetime, timedelta

# Flask'ın veritabanına dışarıdan müdahale etmesi için app_context() kullanmalıyız
with app.app_context():
    # Verileri ekleyeceğimiz kullanıcıyı seçiyoruz (Sistemdeki ilk kullanıcı, yani senin test hesabın)
    kullanici = User.query.first()
    
    if not kullanici:
        print("Hata: Sistemde henüz hiç kullanıcı yok! Önce siteden kayıt olun.")
    else:
        bugun = datetime.now()
        eklenen_kayit_sayisi = 0
        
        print(f"Veriler {kullanici.fullname} adlı kullanıcıya ekleniyor...\n")
        
        # Son 15 gün için geriye dönük döngü başlatıyoruz
        for i in range(1, 16):
            gecmis_tarih = bugun - timedelta(days=i)
            tarih_str = gecmis_tarih.strftime("%Y-%m-%d")
            
            # O tarihte zaten bir kayıt var mı diye bakıyoruz ki çakışma olmasın
            mevcut_kayit = DailyRecord.query.filter_by(user_id=kullanici.id, date_str=tarih_str).first()
            
            if not mevcut_kayit:
                yeni_kayit = DailyRecord(
                    date_str=tarih_str,
                    sleep_start="23:30",
                    sleep_end="07:30",
                    screen_time=4.5,
                    water=6,
                    mood="Nötr",  # Senin istediğin gibi hepsini Nötr yapıyoruz
                    author=kullanici
                )
                db.session.add(yeni_kayit)
                eklenen_kayit_sayisi += 1
                print(f"✅ {tarih_str} tarihi için 'Nötr' kaydı oluşturuldu.")
            else:
                print(f"⚠️ {tarih_str} tarihinde zaten veri var, atlandı.")
                
        # Tüm verileri veritabanına topluca kaydediyoruz
        db.session.commit()
        print(f"\nİşlem Başarılı! Toplam {eklenen_kayit_sayisi} günlük sahte veri eklendi.")