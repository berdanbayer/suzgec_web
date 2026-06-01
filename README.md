# 🎯 Süzgeç - Kişisel Verimlilik ve Ruh Hali Takip Uygulaması

Gazi Üniversitesi Sistem Analizi ve Tasarımı dersi kapsamında, Vibe Coding ve yapay zeka asistanı desteğiyle geliştirilmiş, Flask tabanlı bir kişisel takip uygulamasıdır.

---

## 📺 Proje Demo Videosu
Uygulamanın çalışan tüm özelliklerini ve kod yapısını anlattığım demo videosuna aşağıdaki linkten ulaşabilirsiniz:

👉 **[Süzgeç Proje Demo Videosu (https://youtube.com/shorts/wdIHHIG_zcU?feature=share)]

---

## 🚀 Öne Çıkan Özellikler
* **Modern Mimari:** Application Factory Pattern (`create_app()`) ve Blueprint yapısı.
* **Tam Güvenlik:** Tüm formlarda Flask-WTF ile CSRF koruması, Bcrypt şifreleme ve güvenli şifre sıfırlama sistemi.
* **Gelişmiş Filtreleme:** Geçmiş ruh hali kayıtlarında arama ve SQLAlchemy ile Sayfalama (Pagination).
* **Çoklu Dil:** Sayfa yenilenmeden tek tıkla Türkçe ve İngilizce dil desteği.
* **Dinamik Grafikler:** Su, uyku ve ekran süresi verilerinin Dashboard üzerinde anlık görselleştirilmesi.

---

## 🐳 Docker ile Çalıştırma
Sisteminizde Docker ve Docker Compose kuruluysa, projeyi hiçbir kütüphane kurmadan tek komutla ayağa kaldırabilirsiniz:

```bash
docker-compose up --build
