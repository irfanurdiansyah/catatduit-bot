from flask import Flask
from threading import Thread
import telebot
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# === GANTI INI DENGAN DATA LU ===
BOT_TOKEN = "8355778608:AAEJgysVKdFrT353Ltv0HbokfHQefKlw5xU"
SPREADSHEET_ID = "10z_zn9NMBbCbSBNhFm-GVLmRWkfDue7BtXcPCr5W5b8"

# Setup bot
bot = telebot.TeleBot(BOT_TOKEN)

# Setup Google Sheets
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# === FUNGSI UTAMA ===
def catat_ke_sheet(jenis, nominal, keterangan):
    tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [tanggal, jenis, nominal, keterangan]
    sheet.append_row(row)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, """
👋 Halo! Ini bot catat keuangan pribadi.
Perintah:
/pemasukan [nominal] [keterangan]
/pengeluaran [nominal] [keterangan]
/laporan → lihat total sementara

Contoh:
/pemasukan 50000 jual gorengan
/pengeluaran 20000 beli bensin
""")

@bot.message_handler(commands=['pemasukan'])
def handle_pemasukan(message):
    try:
        text = message.text.split(' ', 2)
        nominal = int(text[1])
        keterangan = text[2] if len(text) > 2 else "-"
        catat_ke_sheet("Pemasukan", nominal, keterangan)
        bot.reply_to(message, f"✅ Pemasukan Rp{nominal} ({keterangan}) berhasil dicatat!")
    except:
        bot.reply_to(message, "❌ Format salah. Contoh: /pemasukan 50000 jual nasi")

@bot.message_handler(commands=['pengeluaran'])
def handle_pengeluaran(message):
    try:
        text = message.text.split(' ', 2)
        nominal = int(text[1])
        keterangan = text[2] if len(text) > 2 else "-"
        catat_ke_sheet("Pengeluaran", nominal, keterangan)
        bot.reply_to(message, f"✅ Pengeluaran Rp{nominal} ({keterangan}) berhasil dicatat!")
    except:
        bot.reply_to(message, "❌ Format salah. Contoh: /pengeluaran 20000 beli bensin")

def hitung_laporan():
    records = sheet.get_all_records()
    total_pemasukan = 0
    total_pengeluaran = 0

    for r in records:
        jenis = r.get('Jenis', '')  # Ambil Jenis, kalau nggak ada → ""
        nominal_str = r.get('Nominal', '')  # Ambil Nominal sebagai string

        try:
            nominal = float(nominal_str)  # Ubah jadi angka (biar aman)
        except:
            continue  # Skip jika bukan angka

        if jenis == 'Pemasukan':
            total_pemasukan += nominal
        elif jenis == 'Pengeluaran':
            total_pengeluaran += nominal

    saldo = total_pemasukan - total_pengeluaran
    return total_pemasukan, total_pengeluaran, saldo

@bot.message_handler(commands=['laporan'])
def handle_laporan(message):
    try:
        pemasukan, pengeluaran, saldo = hitung_laporan()
        reply = f"""
📊 LAPORAN KEUANGAN:
Pemasukan: Rp{pemasukan:,}
Pengeluaran: Rp{pengeluaran:,}
-------------------
Saldo: Rp{saldo:,}
"""
        bot.reply_to(message, reply)
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# === FLASK SERVER (Biar bot nggak mati) ===
app = Flask('')

@app.route('/')
def home():
    return "Bot Catat Duit Online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# === JALANKAN SEMUA ===
keep_alive()
print("✅ Server Flask jalan di port 8080")
print("✅ Bot Telegram jalan...")
bot.polling()