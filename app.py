import os
import json
import uuid
import midtransclient
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from flask import (
    Flask, flash, jsonify, redirect, render_template, request, url_for, session, abort
)

# 1. Muat Environment Variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "haisen_official_secret_2026")

# ==========================================
# KEAMANAN: HOST/DOMAIN WHITELISTING
# ==========================================
# ALLOWED_HOSTS = [
#     '127.0.0.1:5000', 
#     'profile.haisen.my.id',
#     'haisen.my.id', 
#     'profile-haisen-2026-faqms11ph-husain-mulyansyah.vercel.app',
#     'profile-haisen-2026-ftgtmuw3z-husain-mulyansyah.vercel.app' 
# ]

# @app.before_request
# def restrict_host():
#     if request.host not in ALLOWED_HOSTS:
#         abort(403) 

# ==========================================
# SISTEM DATABASE LOKAL (JSON)
# ==========================================
DB_PATH = os.path.join(os.path.dirname(__file__), "core", "db_transaksi.json")

def load_db():
    if not os.path.exists(DB_PATH): return []
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f: return json.load(f)
    except: return []

def save_db(data):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

app.permanent_session_lifetime = timedelta(minutes=60)

# 2. Inisialisasi Midtrans Core API
IS_PRODUCTION = os.getenv("MIDTRANS_IS_PRODUCTION", "False").lower() == "true"
core = midtransclient.CoreApi(
    is_production=IS_PRODUCTION,
    server_key=os.getenv("MIDTRANS_SERVER_KEY"),
    client_key=os.getenv("MIDTRANS_CLIENT_KEY"),
)

# 3. Data Katalog Produk
KATALOG_PRODUK_DETAIL = {
    "company-profile": {
        "nama": "Website Company Profile",
        "kategori": "Pengembangan Software & Web Dev",
        "harga": 1500000,
        "harga_display": "Rp 1.500.000 – Rp 15.000.000",
        "harga_note": "*Harga menyesuaikan kompleksitas desain & jumlah halaman",
        "deskripsi": "Layanan pembuatan website profesional yang dirancang khusus untuk merepresentasikan identitas bisnis, sekolah, atau instansi Anda. Antarmuka eksklusif, responsif di seluruh perangkat, serta teroptimasi SEO.",
        "fitur": [
            {"judul": "Desain UI/UX Eksklusif & Responsif", "desc": "Tampilan modern yang menyesuaikan secara otomatis di layar ponsel, tablet, maupun komputer."},
            {"judul": "Integrasi CMS Mudah Digunakan", "desc": "Kelola konten, artikel, dan galeri mandiri melalui panel admin WordPress atau Custom Admin."},
            {"judul": "Optimasi SEO & Keamanan SSL", "desc": "Ditemukan lebih mudah di Google dengan struktur SEO friendly dan koneksi terenkripsi HTTPS."},
            {"judul": "Integrasi Widget & Analytics", "desc": "Tombol WhatsApp Chat langsung, Google Analytics, serta peta lokasi interaktif."}
        ],
        "alur": [
            {"step": "1", "judul": "Konsultasi & Pengumpulan Materi", "desc": "Diskusi referensi desain, warna brand, dan pengumpulan profil instansi."},
            {"step": "2", "judul": "Desain UI/UX & Wireframe", "desc": "Pembuatan tata letak awal untuk disetujui klien sebelum tahap penulisan kode."},
            {"step": "3", "judul": "Development & Integrasi CMS", "desc": "Pengembangan fungsionalitas web dan optimasi kecepatan muat halaman."},
            {"step": "4", "judul": "Testing, Training & Launch", "desc": "Pemeriksaan akhir, pelatihan admin, dan perilisan website ke publik."}
        ]
    },
    "ecommerce": {
        "nama": "Website E-Commerce",
        "kategori": "Pengembangan Software & Toko Online",
        "harga": 5000000,
        "harga_display": "Rp 5.000.000 – Rp 25.000.000",
        "harga_note": "*Harga menyesuaikan kapasitas inventaris & fitur payment gateway",
        "deskripsi": "Platform toko online berskala penuh dengan fitur keranjang belanja dinamis, penghitungan ongkos kirim otomatis, serta integrasi sistem pembayaran digital terverifikasi.",
        "fitur": [
            {"judul": "Keranjang Belanja & Katalog Dinamis", "desc": "Sistem belanja cepat tanpa ribet dengan manajemen variasi produk (warna, ukuran)."},
            {"judul": "Integrasi Payment Gateway", "desc": "Mendukung pembayaran QRIS, Virtual Account, E-Wallet, dan Kartu Kredit secara otomatis."},
            {"judul": "Ongkir Otomatis (JNE, J&T, dll)", "desc": "Penghitungan tarif pengiriman ke seluruh Indonesia secara real-time."},
            {"judul": "Manajemen Diskon & Inventaris", "desc": "Fitur kupon promo, flash sale, dan pemotongan stok otomatis saat terjadi pesanan."}
        ],
        "alur": [
            {"step": "1", "judul": "Analisis Katalog & Fitur Bisnis", "desc": "Pendataan kategori produk, sistem kurir, dan metode pembayaran yang dibutuhkan."},
            {"step": "2", "judul": "Setup Payment Gateway & Database", "desc": "Pendaftaran merchant payment dan pembuatan skema database inventaris."},
            {"step": "3", "judul": "Desain Antarmuka & Checkout Flow", "desc": "Membuat proses belanja yang konversional dan mudah dipahami pembeli."},
            {"step": "4", "judul": "Uji Transaksi (Sandbox) & Go-Live", "desc": "Simulasi transaksi dari keranjang hingga pembayaran sukses sebelum resmi dibuka."}
        ]
    },
    "mobile-app": {
        "nama": "Aplikasi Mobile iOS & Android",
        "kategori": "Pengembangan Software & Mobile Dev",
        "harga": 4000000,
        "harga_display": "Rp 4.000.000 – Rp 25.000.000+",
        "harga_note": "*Harga menyesuaikan kompleksitas backend & fitur API",
        "deskripsi": "Pengembangan aplikasi ponsel pintar native atau cross-platform berperforma tinggi dengan Flutter/React Native. Dirancang untuk efisiensi dan pengalaman pengguna terbaik.",
        "fitur": [
            {"judul": "Cross-Platform Development", "desc": "Satu basis kode untuk berjalan mulus di perangkat Android maupun Apple iOS."},
            {"judul": "Performa Tinggi & UI Modern", "desc": "Animasi 60fps yang lancar dan desain antarmuka mengacu pada pedoman Material/Human Interface."},
            {"judul": "Push Notification & Sensor API", "desc": "Kirim notifikasi real-time ke HP pengguna, integrasi kamera, GPS, dan biometrik."},
            {"judul": "Bantuan Upload Play Store & App Store", "desc": "Kami tangani seluruh proses verifikasi dan perilisan aplikasi ke toko resmi."}
        ],
        "alur": [
            {"step": "1", "judul": "Penyusunan PRD & Wireframe", "desc": "Perumusan alur logika aplikasi dan tata letak layar per layar."},
            {"step": "2", "judul": "Development Frontend & API Backend", "desc": "Pengkodean aplikasi mobile serta penghubungan dengan server database."},
            {"step": "3", "judul": "Alpha & Beta Testing (QA)", "desc": "Pengujian di berbagai resolusi layar dan tipe HP untuk memastikan bebas bug."},
            {"step": "4", "judul": "Submission & App Store Release", "desc": "Proses peninjauan oleh Google dan Apple hingga aplikasi siap diunduh publik."}
        ]
    },
    "dashboard-api": {
        "nama": "Dashboard Admin & API System",
        "kategori": "Pengembangan Software & ERP/CRM",
        "harga": 2000000,
        "harga_display": "Rp 2.000.000 – Rp 20.000.000",
        "harga_note": "*Harga menyesuaikan jumlah modul & kompleksitas relasi data",
        "deskripsi": "Sistem manajemen data internal (ERP/CRM/Custom SaaS) dengan arsitektur RESTful API atau GraphQL yang tangguh dan tingkat keamanan berlapis.",
        "fitur": [
            {"judul": "Role-Based Access Control (RBAC)", "desc": "Pembatasan hak akses yang berbeda untuk Super Admin, Manajer, Staf, atau Keuangan."},
            {"judul": "RESTful API / GraphQL High Performance", "desc": "Jembatan data yang aman dan cepat untuk dihubungkan ke aplikasi web atau mobile eksternal."},
            {"judul": "Visualisasi Data & Chart Interaktif", "desc": "Pantau metrik bisnis real-time melalui grafik yang dinamis dan mudah dibaca."},
            {"judul": "Export Laporan Otomatis (PDF/Excel)", "desc": "Unduh rekapitulasi data harian, bulanan, atau tahunan cukup dengan satu klik."}
        ],
        "alur": [
            {"step": "1", "judul": "Analisis Skema Database & Relasi", "desc": "Perancangan arsitektur data agar sistem berjalan optimal dan tidak redundan."},
            {"step": "2", "judul": "Pembuatan Core Engine & Endpoints API", "desc": "Pengkodean logika bisnis, autentikasi JWT/OAuth, dan keamanan server."},
            {"step": "3", "judul": "Integrasi UI Dashboard Admin", "desc": "Membangun antarmuka administrator untuk memodifikasi dan mengelola database."},
            {"step": "4", "judul": "Load Testing & Deployment", "desc": "Uji ketahanan server terhadap request massal dan implementasi ke production."}
        ]
    },
    "eo-seminar": {
        "nama": "Dokumentasi Event Organizer & Seminar",
        "kategori": "Foto & Videografi Kreatif",
        "harga": 350000,
        "harga_display": "Rp 350.000 – Rp 12.000.000",
        "harga_note": "*Harga menyesuaikan durasi acara & jumlah kru yang bertugas",
        "deskripsi": "Layanan liputan fotografi dan videografi profesional untuk konferensi, seminar nasional, workshop, dan event gathering organisasi Anda.",
        "fitur": [
            {"judul": "High-Resolution Full Edited Photos", "desc": "Seluruh foto melalui proses editing warna (color grading) profesional dan siap tayang."},
            {"judul": "Video Aftermovie / Highlight Sinematik", "desc": "Rekapitulasi momen penting acara dalam video berdurasi 1-3 menit yang menggugah emosi."},
            {"judul": "Multiple Kamera & Kru Lighting", "desc": "Dukungan fotografer, videografer, dan teknisi pencahayaan untuk hasil visual maksimal."},
            {"judul": "Penyerahan Cloud Drive Cepat", "desc": "Penyediaan akses file cepat untuk kebutuhan siaran pers (press release) atau media sosial."}
        ],
        "alur": [
            {"step": "1", "judul": "Briefing Rundown & Lokasi (Survey)", "desc": "Mempelajari jadwal acara, pencahayaan gedung, dan sudut pengambilan gambar terbaik."},
            {"step": "2", "judul": "Setup Peralatan & Gladi Bersih", "desc": "Kedatangan kru lebih awal untuk penataan kamera, mikrofon, dan lampu studio."},
            {"step": "3", "judul": "Eksekusi Liputan Hari H", "desc": "Pengambilan gambar secara agresif namun tidak mengganggu kenyamanan jalannya acara."},
            {"step": "4", "judul": "Post-Production Editing & Delivery", "desc": "Penyuntingan video, color grading foto, dan penyerahan tautan Google Drive premium."}
        ]
    },
    "wedding-graduation": {
        "nama": "Pernikahan & Wisuda (Wedding & Graduation)",
        "kategori": "Foto & Videografi Kreatif",
        "harga": 150000,
        "harga_display": "Rp 150.000 – Rp 5.000.000",
        "harga_note": "*Harga menyesuaikan paket personal, couple, atau liputan hari H",
        "deskripsi": "Abadikan momen paling bahagia dan bersejarah dalam hidup Anda dengan sentuhan visual yang elegan, romantis, dan penuh estetika.",
        "fitur": [
            {"judul": "Sesi Foto Pre-Wedding / Engagement", "desc": "Pengarahan gaya (directing) yang natural di lokasi indoor studio atau outdoor alam."},
            {"judul": "Video Cinematic Wedding & Teaser Sosmed", "desc": "Dokumentasi video bergaya film layar lebar serta potongan pendek untuk TikTok/Instagram."},
            {"judul": "Album Cetak Kolase & Bingkai Premium", "desc": "Hasil fisik berkualitas tinggi yang tahan lama sebagai kenang-kenangan keluarga."},
            {"judul": "Liputan Wisuda Personal & Angkatan", "desc": "Sesi foto selebrasi kelulusan bersama keluarga maupun teman seperjuangan kampus."}
        ],
        "alur": [
            {"step": "1", "judul": "Konsultasi Konsep & Moodboard", "desc": "Menentukan tema visual, referensi gaya berpakaian, dan pemilihan lokasi foto."},
            {"step": "2", "judul": "Sesi Pemotretan / Liputan Hari H", "desc": "Tim fotografer mengarahkan pose dengan santai, ramah, dan menyenangkan."},
            {"step": "3", "judul": "Seleksi Foto & Preview", "desc": "Klien memilih foto-foto terbaik yang akan dimasukkan ke tahap editing mendalam."},
            {"step": "4", "judul": "Cetak Album & Penyerahan Berkas Digital", "desc": "Pengiriman album fisik eksklusif serta seluruh file digital resolusi tinggi."}
        ]
    },
    "running-gathering": {
        "nama": "Running Event & Gathering Komunitas",
        "kategori": "Foto & Videografi Kreatif",
        "harga": 800000,
        "harga_display": "Rp 800.000 – Rp 7.000.000",
        "harga_note": "*Harga menyesuaikan panjang rute & jumlah fotografer rute",
        "deskripsi": "Layanan dokumentasi khusus olahraga lari (maraton/fun run) dan gathering komunitas dengan tangkapan lensa kecepatan tinggi (speed shutter).",
        "fitur": [
            {"judul": "Fotografer Titik Rute Strategis", "desc": "Penempatan kru di water station, rute menanjak, hingga garis finish untuk menangkap ekspresi terbaik."},
            {"judul": "Sports Photography Speed Shutter", "desc": "Kamera dengan autofokus cepat untuk menghasilkan foto pelari yang tajam dan tidak blur."},
            {"judul": "Sistem Cari Foto (Face Recognition / BIB)", "desc": "Peserta dapat menemukan fotonya sendiri dalam hitungan detik melalui teknologi AI."},
            {"judul": "Video Rekapitulasi & Wawancara Peserta", "desc": "Mengabadikan energi dan semangat kemeriahan acara dari garis start hingga garis finish."}
        ],
        "alur": [
            {"step": "1", "judul": "Survey Rute Lari & Titik Penempatan Kru", "desc": "Memetakan rute lomba untuk menentukan spot pencahayaan alami terbaik bagi fotografer."},
            {"step": "2", "judul": "Setup Server AI Face Recognition", "desc": "Mempersiapkan infrastruktur pencarian foto berbasis pengenalan wajah dan nomor BIB."},
            {"step": "3", "judul": "Eksekusi Pemotretan Cepat Hari H", "desc": "Kru memotret ribuan peserta secara berkelanjutan sejak flag-off subuh hingga selesai."},
            {"step": "4", "judul": "Rapid Upload & Publikasi Galeri", "desc": "Pengunggahan foto secara cepat agar peserta bisa langsung membagikan momen ke media sosial."}
        ]
    },
    "drone-aerial": {
        "nama": "Drone Photography & Aerial Videography",
        "kategori": "Foto & Videografi Kreatif",
        "harga": 1000000,
        "harga_display": "Rp 1.000.000 – Rp 3.000.000",
        "harga_note": "*Harga per sesi (half-day) atau full-day operasional",
        "deskripsi": "Pengambilan visual udara beresolusi tinggi 4K/60fps dengan armada drone sinematik terbaru, dipiloti oleh operator berlisensi resmi dan berpengalaman.",
        "fitur": [
            {"judul": "Visual Udara 4K / 60fps Ultra HD", "desc": "Kualitas rekaman video sinematik yang sangat tajam dan mendetail dari ketinggian."},
            {"judul": "Pilot Drone Berlisensi & Berpengalaman", "desc": "Mengutamakan keselamatan penerbangan (safety first) dan pemahaman regulasi zona udara."},
            {"judul": "Mapping Area & Proyek Konstruksi", "desc": "Cocok untuk dokumentasi progres proyek gedung, pemetaan lahan, maupun event outdoor skala besar."},
            {"judul": "Color Grading Sinematik", "desc": "Penyuntingan warna tone udara yang dramatis dan memukau."}
        ],
        "alur": [
            {"step": "1", "judul": "Analisis Zona Udara & Cuaca (Pre-Flight)", "desc": "Pemeriksaan izin terbang di lokasi serta perkiraan kecepatan angin dan cuaca."},
            {"step": "2", "judul": "Flight Plan & penentuan Sudut Visual", "desc": "Merancang jalur terbang drone untuk mendapatkan manuver kamera yang paling sinematik."},
            {"step": "3", "judul": "Penerbangan & Pengambilan Visual", "desc": "Eksekusi penerbangan drone dengan pengawasan ketat keselamatan di area operasional."},
            {"step": "4", "judul": "Stabilization & Video Editing", "desc": "Penyempurnaan kestabilan rekaman dan pewarnaan video visual udara sebelum diserahkan."}
        ]
    },
    "qr-checkin": {
        "nama": "QR Code Check-in & E-Ticket System",
        "kategori": "Event Digital Solution (Event Tech)",
        "harga": 800000,
        "harga_display": "Rp 800.000 – Rp 7.500.000",
        "harga_note": "*Harga menyesuaikan perkiraan jumlah peserta & tablet scanner",
        "deskripsi": "Solusi manajemen registrasi dan tiket acara modern. Mencegah antrean panjang di pintu masuk dengan teknologi pemindaian QR Code super cepat kurang dari 2 detik per orang.",
        "fitur": [
            {"judul": "E-Ticket & QR Otomatis via WA / Email", "desc": "Tiket langsung dikirimkan secara otomatis begitu peserta selesai mendaftar dan membayar."},
            {"judul": "Aplikasi Scanner Khusus Panitia (<2 Detik)", "desc": "Proses check-in kilat menggunakan kamera ponsel atau tablet tanpa perlu jaringan internet lambat."},
            {"judul": "Mencegah Tiket Palsu & Duplikasi Check-in", "desc": "Sistem mendeteksi secara real-time jika sebuah QR Code sudah pernah digunakan sebelumnya."},
            {"judul": "Cetak Badge / Name Tag Otomatis di Lokasi", "desc": "Integrasi ke printer label untuk mencetak kartu identitas peserta seketika setelah scan."}
        ],
        "alur": [
            {"step": "1", "judul": "Setup Landing Page & Form Registrasi", "desc": "Pembuatan halaman web pendaftaran acara dengan kolom data yang disesuaikan kebutuhan panitia."},
            {"step": "2", "judul": "Integrasi WhatsApp Blast Engine", "desc": "Menghubungkan server pengirim tiket QR Code otomatis ke WhatsApp peserta terdaftar."},
            {"step": "3", "judul": "Gladi Bersih & Pelatihan Scanner Panitia", "desc": "Simulasi check-in di venue dan briefing singkat kepada staf penjaga pintu masuk (gate)."},
            {"step": "4", "judul": "Live Standby Hari H & Rekapitulasi Data", "desc": "Tim teknis Haisen mengawasi kelancaran server check-in dan memberikan laporan kehadiran lengkap."}
        ]
    },
    "live-monitoring": {
        "nama": "Live Participant Monitoring System",
        "kategori": "Event Digital Solution (Event Tech)",
        "harga": 500000,
        "harga_display": "Rp 500.000 – Rp 8.000.000",
        "harga_note": "*Harga menyesuaikan layar display & integrasi sensor gate",
        "deskripsi": "Dasbor pemantauan kehadiran peserta secara real-time untuk panitia dan tamu VIP. Menampilkan statistik demografi dan grafik kehadiran di layar monitor besar venue.",
        "fitur": [
            {"judul": "Dasbor Pemantauan Real-Time VIP", "desc": "Pantau jumlah peserta yang sudah hadir maupun yang belum hadir dari layar tablet/laptop."},
            {"judul": "Grafik & Statistik Demografi Peserta", "desc": "Visualisasi data berdasarkan kategori instansi, jenis kelamin, atau usia peserta yang hadir."},
            {"judul": "Live Attendance Screen di Venue", "desc": "Tampilan selamat datang dinamis di layar LED panggung saat peserta melakukan check-in."},
            {"judul": "Export Data Kehadiran Lengkap (Excel)", "desc": "Unduh rekap data absensi presisi dengan cap waktu (timestamp) kehadiran detik per detik."}
        ],
        "alur": [
            {"step": "1", "judul": "Koneksi Sistem dengan Gateway Check-in", "desc": "Menghubungkan dasbor monitor dengan database pemindai tiket atau sensor RFID gate."},
            {"step": "2", "judul": "Kustomisasi Tampilan Layar (UI Display)", "desc": "Desain antarmuka grafik monitor sesuai dengan tema warna dan logo resmi acara."},
            {"step": "3", "judul": "Uji Beban & Konektivitas Lokal", "desc": "Memastikan transmisi data dari titik check-in ke layar monitor utama tidak mengalami delay."},
            {"step": "4", "judul": "Live Operation & Final Export", "desc": "Pengoperasian sistem saat acara berlangsung dan penyerahan spreadsheet absensi akhir."}
        ]
    },
    "rfid-timing": {
        "nama": "Leaderboard & Timing System (RFID)",
        "kategori": "Event Digital Solution & RFID Tech",
        "harga": 500000,
        "harga_display": "Rp 500.000 – Rp 10.000.000",
        "harga_note": "*Harga menyesuaikan kuota peserta & titik kontrol antena",
        "deskripsi": "Sistem pencatatan waktu otomatis berakurasi tinggi menggunakan teknologi cip RFID untuk perlombaan lari, maraton, dan kompetisi olahraga. Menghadirkan transparansi skor secara real-time di garis akhir.",
        "fitur": [
            {"judul": "Pencatatan Waktu Otomatis (Gun & Net Time)", "desc": "Mendeteksi waktu Gun Time dan Net Time pesepeda/pelari dengan akurasi hingga milidetik."},
            {"judul": "RFID Timing Chip Berakurasi Tinggi", "desc": "Cip ultra-ringan anti-air yang dipasangkan pada nomor dada (BIB) atau pergelangan kaki peserta."},
            {"judul": "Live Leaderboard Display di LED Finish", "desc": "Integrasi langsung ke layar LED panggung utama untuk klasemen juara secara instan."},
            {"judul": "WhatsApp Finish Notification Otomatis", "desc": "Peserta langsung menerima pesan WhatsApp berisi catatan waktu resmi sesaat setelah finish."}
        ],
        "alur": [
            {"step": "1", "judul": "Konsultasi & Analisis Rute Lomba", "desc": "Diskusi titik water station, checkpoint, garis start/finish, dan kapasitas peserta."},
            {"step": "2", "judul": "Encoding Cip RFID & Pembuatan BIB", "desc": "Memasukkan data identitas pelari ke dalam cip elektronik pada nomor dada peserta."},
            {"step": "3", "judul": "Setup Hardware Antena & Gladi Bersih", "desc": "Pemasangan karpet antena RFID di lokasi dan pengujian pembacaan cip sebelum hari H."},
            {"step": "4", "judul": "Eksekusi Event & Export Data Resmi", "desc": "Pengawasan sistem secara live dan penyerahan laporan hasil rekapitulasi waktu juara lengkap."}
        ]
    },
    "digital-cert": {
        "nama": "Sertifikat Digital & Mass Blast",
        "kategori": "Event Digital Solution (Event Tech)",
        "harga": 500000,
        "harga_display": "Rp 500.000 – Rp 3.000.000",
        "harga_note": "*Harga menyesuaikan volume peserta & kustomisasi verifikasi QR",
        "deskripsi": "Layanan pembuatan dan distribusi massal e-sertifikat terverifikasi QR Code. Dilengkapi portal pencarian mandiri dan pengiriman langsung ke ribuan WhatsApp serta Email peserta dalam hitungan menit.",
        "fitur": [
            {"judul": "Desain E-Sertifikat Dinamis + Verifikasi QR", "desc": "Sertifikat elegan yang dilengkapi kode QR unik untuk membuktikan keaslian dokumen."},
            {"judul": "Penomoran Otomatis Terintegrasi Data", "desc": "Nama, nomor sertifikat, dan predikat kelulusan dicetak otomatis dari database registrasi."},
            {"judul": "Distribusi Massal via WhatsApp & Email Blast", "desc": "Kirim sertifikat ke ribuan peserta sekaligus tanpa takut email masuk ke folder spam."},
            {"judul": "Portal Cek & Unduh Mandiri", "desc": "Peserta dapat mengunduh ulang sertifikat mereka kapan saja melalui halaman web khusus."}
        ],
        "alur": [
            {"step": "1", "judul": "Penerimaan Template Desain & Data Peserta", "desc": "Klien menyerahkan desain sertifikat kosong serta file Excel/CSV daftar nama peserta yang lulus."},
            {"step": "2", "judul": "Mapping Koordinat Teks & QR Code", "desc": "Tim kami mengonfigurasi posisi penempatan nama dan kode verifikasi pada template sertifikat."},
            {"step": "3", "judul": "Uji Coba Generasi (Sample Testing)", "desc": "Mengirimkan 5-10 contoh sertifikat hasil render kepada klien untuk pengecekan tata letak."},
            {"step": "4", "judul": "Mass Blast & Pembukaan Portal Unduh", "desc": "Eksekusi pengiriman massal ke seluruh peserta dan penyerahan tautan portal unduh mandiri."}
        ]
    },
    "bundling-sport": {
        "nama": "Paket Sport / Running Event All-in-One",
        "kategori": "Paket Bundling Spesial",
        "harga": 25000000,
        "harga_display": "Mulai dari Rp 25.000.000",
        "harga_note": "*Hemat hingga 15% dibanding memesan layanan secara terpisah",
        "deskripsi": "Solusi terintegrasi terlengkap untuk kemeriahan dan kelancaran perlombaan lari maraton, 5K, 10K, maupun bersepeda. Menggabungkan website registrasi, sistem timing RFID, hingga dokumentasi visual.",
        "fitur": [
            {"judul": "Website Registrasi & Pembayaran Online", "desc": "Portal pendaftaran resmi event dengan integrasi payment gateway untuk kemudahan peserta."},
            {"judul": "QR Code Check-in & Race Pack Collection", "desc": "Sistem pengambilan paket lomba (RPC) yang teratur, cepat, dan bebas antrean."},
            {"judul": "Leaderboard & Timing System RFID Finish", "desc": "Pencatatan waktu akurat menggunakan cip RFID dengan tayangan klasemen live di LED."},
            {"judul": "Tim Fotografer Rute, Drone & Video Aftermovie", "desc": "Dokumentasi lengkap foto aksi pelari di rute, visual udara start/finish, dan video highlight."}
        ],
        "alur": [
            {"step": "1", "judul": "Kick-off Meeting & Timeline Planning", "desc": "Penyusunan jadwal integrasi dari mulai pembukaan pendaftaran hingga hari perlombaan."},
            {"step": "2", "judul": "Peluncuran Website & Pembukaan Registrasi", "desc": "Web mulai menerima pendaftaran peserta dan pembayaran masuk otomatis ke rekening panitia."},
            {"step": "3", "judul": "Operasional RPC & Gladi Bersih Hardware", "desc": "Pengawalan teknis saat pengambilan race pack dan pemasangan sistem timing di venue."},
            {"step": "4", "judul": "Eksekusi Hari H, Live Leaderboard & Aftermovie", "desc": "Pengawalan penuh seluruh sistem teknologi event dan penyerahan dokumentasi paska-acara."}
        ]
    },
    "bundling-corporate": {
        "nama": "Paket Corporate Seminar Pro",
        "kategori": "Paket Bundling Spesial",
        "harga": 15000000,
        "harga_display": "Mulai dari Rp 15.000.000",
        "harga_note": "*Hemat hingga 10% untuk kebutuhan konferensi & gathering perusahaan",
        "deskripsi": "Standar profesional dan elegan untuk penyelenggaraan konferensi, seminar nasional, workshop, maupun gathering tahunan perusahaan Anda dengan teknologi interaktif.",
        "fitur": [
            {"judul": "Landing Page Acara & Form Registrasi Online", "desc": "Halaman web informasi pembicara, jadwal sesi, dan pendaftaran peserta seminar."},
            {"judul": "QR Code E-Ticket Scanner & Live Attendance", "desc": "Check-in tamu undangan VIP di meja resepsionis kurang dari 2 detik dan monitor absensi."},
            {"judul": "Dokumentasi Foto Liputan & Video Highlight", "desc": "Kamera profesional untuk mengabadikan momen pembicara dan antusiasme peserta."},
            {"judul": "E-Sertifikat Terverifikasi untuk Peserta", "desc": "Pengiriman sertifikat elektronik otomatis sesaat setelah seminar resmi ditutup."}
        ],
        "alur": [
            {"step": "1", "judul": "Koordinasi Konsep & Kebutuhan Staf", "desc": "Menentukan jumlah titik check-in dan kebutuhan peralatan liputan di gedung acara."},
            {"step": "2", "judul": "Publikasi Landing Page Seminar", "desc": "Perilisan halaman web untuk mulai mendata calon peserta yang akan hadir."},
            {"step": "3", "judul": "Setup Scanner & Kamera di Venue", "desc": "Persiapan alat di lokasi acara satu hari sebelum acara dimulai (H-1)."},
            {"step": "4", "judul": "Live Support Hari H & Blast Sertifikat", "desc": "Pengawalan kelancaran registrasi tamu dan pengiriman e-sertifikat paska-acara."}
        ]
    },
    "bundling-wedding": {
        "nama": "Paket Digital Wedding & Celebration",
        "kategori": "Paket Bundling Spesial",
        "harga": 12500000,
        "harga_display": "Mulai dari Rp 12.500.000",
        "harga_note": "*Paket lengkap perpaduan teknologi undangan digital dan dokumentasi",
        "deskripsi": "Perpaduan sempurna antara keanggunan dokumentasi visual sinematik dan kepraktisan teknologi undangan pernikahan digital masa kini untuk momen spesial Anda.",
        "fitur": [
            {"judul": "Undangan Digital Eksklusif (Website Wedding)", "desc": "Web undangan romantis dengan fitur RSVP, amplop digital, kisah cinta, dan galeri foto."},
            {"judul": "QR Code Buku Tamu Digital & Check-in Suvenir", "desc": "Gantikan buku tamu kertas dengan scan QR untuk mendata kehadiran tamu undangan."},
            {"judul": "Sesi Foto Pre-Wed & Video Cinematic Wedding", "desc": "Dokumentasi lengkap dari masa sebelum pernikahan hingga resepsi hari H oleh tim berpengalaman."},
            {"judul": "Galeri Foto Cloud Real-time untuk Akses Tamu", "desc": "Tamu undangan dapat melihat dan mengunduh foto-foto acara secara langsung via scan barcode."}
        ],
        "alur": [
            {"step": "1", "judul": "Pembuatan Web Undangan & Sesi Pre-Wedding", "desc": "Eksekusi foto pre-wed dan penyusunan informasi acara ke dalam website undangan."},
            {"step": "2", "judul": "Penyebaran Undangan & Pengumpulan RSVP", "desc": "Membantu pasangan memantau konfirmasi kehadiran tamu via dasbor online."},
            {"step": "3", "judul": "Setup Buku Tamu Digital di Venue Resepsi", "desc": "Menyiapkan tablet dan stan pemindai QR Code di meja penerima tamu (resepsionis)."},
            {"step": "4", "judul": "Liputan Sinematik Hari H & Cetak Album", "desc": "Merekam seluruh emosi kebahagiaan resepsi dan mencetak album kolase eksklusif."}
        ]
    }
}

# ==========================================
# AUTH ADMIN & DECORATOR
# ==========================================
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = generate_password_hash(os.getenv("ADMIN_PASSWORD", "rahasia"))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# RUTE AUTH ADMIN
# ==========================================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get('is_admin_logged_in'): return redirect(url_for('admin_dashboard'))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session.permanent = True
            session['is_admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        flash("Akses ditolak.")
    return render_template("admin/auth/login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop('is_admin_logged_in', None)
    return redirect(url_for('admin_login'))

# ==========================================
# RUTE ADMIN DASHBOARD
# ==========================================
@app.route("/admin")
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    db = load_db()
    stats = {
        "pendapatan": f"Rp {sum(int(item['jumlah']) for item in db if item['status_bayar'] in ['settlement', 'capture']):,}".replace(',', '.'),
        "total_pesanan": len(db),
        "menunggu_pembayaran": sum(1 for item in db if item["status_bayar"] == "pending"),
        "proyek_aktif": sum(1 for item in db if item["status_proyek"] == "In Progress")
    }
    return render_template("admin/dashboard/index.html", stats=stats)

@app.route("/admin/pesanan")
@admin_required
def admin_pesanan():
    db = list(reversed(load_db()))
    return render_template("admin/dashboard/pesanan.html", pesanan=db)

@app.route("/admin/transaksi")
@admin_required
def admin_transaksi():
    db = list(reversed(load_db()))
    for t in db: t["jumlah"] = f"Rp {t['jumlah']:,}".replace(',', '.')
    return render_template("admin/dashboard/transaksi.html", transaksi=db)

# ==========================================
# RUTE CHECKOUT & WEBHOOK (CORE API)
# ==========================================
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "POST":
        try:
            nama, email, whatsapp, produk_id = request.form.get("nama"), request.form.get("email"), request.form.get("whatsapp"), request.form.get("produk_id")
            payment_method = request.form.get("payment_method")

            if produk_id not in KATALOG_PRODUK_DETAIL: return jsonify({"error": "Produk invalid"}), 400

            detail_produk = KATALOG_PRODUK_DETAIL[produk_id]
            harga = int(detail_produk["harga"])
            order_id = f"INV-HSN-{uuid.uuid4().hex[:8].upper()}"

            param = {
                "transaction_details": {"order_id": order_id, "gross_amount": harga},
                "item_details": [{"id": produk_id, "price": harga, "quantity": 1, "name": detail_produk["nama"][:50]}],
                "customer_details": {"first_name": nama, "email": email, "phone": whatsapp},
            }

            if payment_method in ['bca', 'bni']:
                param.update({"payment_type": "bank_transfer", "bank_transfer": {"bank": payment_method}})
            elif payment_method == 'mandiri':
                param.update({"payment_type": "echannel", "echannel": {"bill_info1": "Bayar", "bill_info2": "Layanan Haisen"}})
            elif payment_method == 'qris':
                param["payment_type"] = "qris"

            charge_response = core.charge(param)
            
            # Simpan ke DB
            db = load_db()
            db.append({
                "id": order_id, "nama": nama, "email": email, "whatsapp": whatsapp,
                "layanan": detail_produk["nama"], "metode": payment_method.upper(),
                "jumlah": harga, "status_bayar": "pending",
                "status_proyek": "Menunggu Pembayaran", "tanggal": datetime.now().strftime("%d %b %Y %H:%M")
            })
            save_db(db)

            res = {"status": "success", "order_id": order_id, "payment_type": payment_method, "gross_amount": harga}
            if payment_method in ['bca', 'bni']: res["va_number"] = charge_response.get("va_numbers", [{}])[0].get("va_number", ""); res["bank"] = payment_method.upper()
            elif payment_method == 'mandiri': res["bill_key"] = charge_response.get("bill_key", ""); res["biller_code"] = charge_response.get("biller_code", ""); res["bank"] = "MANDIRI"
            elif payment_method == 'qris': res["qr_url"] = next((act["url"] for act in charge_response.get("actions", []) if act.get("name") == "generate-qr-code"), "")
            
            return jsonify(res)
        except Exception as e: return jsonify({"error": str(e)}), 500

    return render_template("transaksi/checkout.html", pilihan_produk=request.args.get("id", ""))

@app.route("/api/midtrans-callback", methods=["POST"])
def midtrans_callback():
    data = request.get_json()
    try:
        status_response = core.transactions.notification(data)
        order_id = status_response["order_id"]
        transaction_status = status_response["transaction_status"]
        
        db = load_db()
        for p in db:
            if p["id"] == order_id:
                p["status_bayar"] = transaction_status
                p["status_proyek"] = "In Progress" if transaction_status in ['settlement', 'capture'] else "Dibatalkan"
                break
        save_db(db)
        return jsonify({"status": "ok"}), 200
    except: return jsonify({"status": "error"}), 400

@app.route("/status-pembayaran/<order_id>")
def status_pembayaran(order_id):
    try:
        status = core.transactions.status(order_id).get("transaction_status")
        if status in ['capture', 'settlement']: return render_template("callback/succes.html", order_id=order_id)
        if status == 'pending': return render_template("callback/pending.html", order_id=order_id)
        if status in ['deny', 'expire', 'failure']: return render_template("callback/gagal.html", order_id=order_id)
        return render_template("callback/cancelled.html", order_id=order_id)
    except: return redirect(url_for('cek_pesanan', query=order_id))

# ==========================================
# RUTE UTAMA & INFORMASI
# ==========================================
@app.route("/")
def home(): return render_template("index.html")

@app.route("/about")
def about(): return render_template("informasi/about_me.html")

@app.route("/contact")
def contact(): return render_template("informasi/contact.html")

@app.route("/logo")
def logo(): return render_template("informasi/logo.html")

@app.route("/privacy-policy")
def privacy_policy(): return render_template("informasi/privacy_policy.html")

@app.route("/terms-and-conditions")
def terms_and_conditions(): return render_template("informasi/terms_and_conditions.html")

@app.route("/produk")
def produk(): return render_template("public/produk.html")

@app.route("/detail-produk")
def detail_produk():
    produk_id = request.args.get("id", "rfid-timing")
    if produk_id not in KATALOG_PRODUK_DETAIL:
        produk_id = "rfid-timing"
    produk_data = KATALOG_PRODUK_DETAIL.get(produk_id, {})
    return render_template("public/detail_produk.html", produk_id=produk_id, produk=produk_data)

@app.route("/cek-pesanan")
def cek_pesanan():
    invoice_query = request.args.get("query", "").strip()
    pesanan = None
    error_msg = None

    if invoice_query:
        try:
            status_response = core.transactions.status(invoice_query)
            gross_amount = int(float(status_response.get("gross_amount", 0)))
            payment_type = status_response.get("payment_type")
            
            payment_method_display = payment_type.replace("_", " ").title()
            if payment_type == "bank_transfer":
                bank = status_response.get("va_numbers", [{}])[0].get("bank", "Bank Transfer").upper()
                payment_method_display = f"Virtual Account {bank}"
            elif payment_type == "echannel":
                payment_method_display = "Mandiri Bill Payment"
            elif payment_type == "qris":
                payment_method_display = "QRIS"

            pesanan = {
                "order_id": status_response.get("order_id"),
                "status": status_response.get("transaction_status"),
                "gross_amount_format": f"Rp {gross_amount:,}".replace(",", "."),
                "payment_method": payment_method_display,
                "waktu": status_response.get("transaction_time")
            }
            
        except Exception as e:
            error_msg = f"Pesanan dengan Invoice '{invoice_query}' tidak ditemukan atau belum terdaftar."

    return render_template("transaksi/cek-pesanan-saya.html", invoice=invoice_query, pesanan=pesanan, error=error_msg)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=os.getenv("FLASK_DEBUG", "True") == "True")