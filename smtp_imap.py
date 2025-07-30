# Gerekli Kütüphaneler & Örnek Kod Parçası

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from groq import Groq
from email.header import decode_header
import traceback
from email.mime.multipart import MIMEMultipart
import sqlconnect
from email.utils import parseaddr
from sqlalchemy import text

# Gmail'in IMAP ve SMTP sunucularını kullandım, bu nedenle ayarları buna göre yapılandırıyoruz.

IMAP_SERVER = 'imap.gmail.com'  
SMTP_SERVER = 'smtp.gmail.com'  
EMAIL_USER = '#Gmail adres'
EMAIL_PASS = '#Gmail uygulama şifresi'
IMAP_PORT = 993  
SMTP_PORT = 587

# Soruları göndereceğimiz Groq API anahtarını tanımlıyoruz.
GROQ_API_KEY = '#GROQ API'
client = Groq(api_key=GROQ_API_KEY)

# Gelen e-postaları kontrol

def check_mail():
    
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        print(f"IMAP bağlantısı kuruluyor: {IMAP_SERVER}:{IMAP_PORT}")
        
        try:
            # Standart kimlik doğrulama
            mail.login(EMAIL_USER, EMAIL_PASS)
            print("Giriş Başarılı")
        except Exception as e:
            print(f"IMAP Kimlik Doğrulama Hatası: {e}")
            return
            
        try:
            mail.select('inbox')
            print("Gelen kutusu kontrol ediliyor...")
        except imaplib.IMAP4.error as e:
            print(f"Gelen kutusuna erişilemedi!: {e}")
            return

    except imaplib.IMAP4.error as e:
        print(f"IMAP Hatası: {e}")
        return
    
    result, data = mail.search(None, 'UNSEEN')
    if result != "OK":
        print(f"Mail arama hatası!: {result}")
        mail.logout()
        return

    mail_ids = data[0].split()
    if not mail_ids or mail_ids == [b'']:
        print("Okunmamış bir mail yok")
        mail.logout()
        return
    
    # Devamında SMTP ile Groq API'sine gönderilen soruların işlenmesi, soruların ve cevapların veritabanına kaydedilmesi işlemleri yapılır.
    # Süreç boyunca tüm işlemler aşağıdaki örnekteki gibi Groq API'si üzerinden gerçekleştirilir.

prompt = f"""
Aşağıdaki e-posta içeriğini analiz et ve kategorisini belirle:
[
Bu e-posta aşağıdaki kategorilerden hangisine giriyor?
1. Teşekkür - Olumlu geri bildirim, memnuniyet ifadesi.
2. Şikayet - Olumsuz geri bildirim, sorun bildirimi.
3. Genel - Genel soru, bilgi talebi veya nötr içerik.
4. Hazırladığın mesaj'ın en başına "şikayet-genel-teşekkür" Yazma. Sen bir mail asistanısın yani bir insan gibi cevap veriyorsun o yüzden cevabında kategori göstermen yanlış bir durum!
]

Kategorilere göre aşağıdaki mail içeriğini düzenleyerek kullanıcıya ilet mesela {email_content} şikayet ise o zaman yaşadığınız sorunu anlıyoruz bu durum için
üzgünüz en kısa sürede durumu telafi edeceğiz gibi cümleler ile detaylandırabilirsin:

Merhaba,
Mesajınızı aldık. İlgili departmanımız konuyu değerlendirerek size geri dönüş yapacaktır.
Teşekkürler.

Sadece uygun kategori için cevabı ver, başka açıklama ekleme.
"""

# Model tercihiniz soruların token boyutlarına ve biçimlerine göre değişebilir.
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_completion_tokens=300,
            top_p=1,
            stream=False,
            stop=None,
        )
        content = completion.choices[0].message.content