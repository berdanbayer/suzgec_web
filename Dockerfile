# 1. Adım: Temel işletim sistemi olarak hafif bir Python sürümü seç
FROM python:3.11-slim

# 2. Adım: Sanal bilgisayarın içinde /app adında bir klasör oluştur ve oraya geç
WORKDIR /app

# 3. Adım: Önce kütüphane listeni kopyala (Hız için bu adım önemlidir)
COPY requirements.txt .

# 4. Adım: Listendeki tüm kütüphaneleri sanal bilgisayara kur
RUN pip install --no-cache-dir -r requirements.txt

# 5. Adım: Projenin geri kalan tüm dosyalarını (app.py, templates vb.) kopyala
COPY . .

# 6. Adım: Flask'ın dışarıya yayın yapacağı kapıyı (Port) belirle
EXPOSE 5000

# 7. Adım: Uygulamayı başlat
CMD ["python", "app.py"]