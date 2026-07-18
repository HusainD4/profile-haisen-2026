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
# Daftar domain yang diizinkan mengakses aplikasi
ALLOWED_HOSTS = ['127.0.0.1:5000', 'profile.haisen.my.id', 'haisen.my.id']

@app.before_request
def restrict_host():
    """Membatasi akses hanya dari domain/host yang terdaftar."""
    # request.host akan mengambil host (domain/ip:port) dari request pengunjung
    if request.host not in ALLOWED_HOSTS:
        # Menolak akses jika domain tidak terdaftar
        abort(403) 

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

# Konfigurasi Sesi
app.permanent_session_lifetime = timedelta(minutes=60)

# 2. Inisialisasi Midtrans Core API
IS_PRODUCTION = os.getenv("MIDTRANS_IS_PRODUCTION", "False").lower() == "true"
core = midtransclient.CoreApi(
    is_production=IS_PRODUCTION,
    server_key=os.getenv("MIDTRANS_SERVER_KEY"),
    client_key=os.getenv("MIDTRANS_CLIENT_KEY"),
)

# 3. Muat Data Katalog
JSON_PATH = os.path.join(os.path.dirname(__file__), "core", "KATALOG_PRODUK_DETAIL.json")
try:
    with open(JSON_PATH, "r", encoding="utf-8") as f: KATALOG_PRODUK_DETAIL = json.load(f)
except: KATALOG_PRODUK_DETAIL = {}

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
            # Panggil status API ke server Midtrans berdasarkan Order ID
            status_response = core.transactions.status(invoice_query)
            
            # Parsing dan pemformatan data penting dari Midtrans
            gross_amount = int(float(status_response.get("gross_amount", 0)))
            payment_type = status_response.get("payment_type")
            
            # Pemetaan nama metode pembayaran agar lebih rapi dibaca
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
            # Jika Order ID tidak ditemukan di sistem Midtrans atau format salah
            error_msg = f"Pesanan dengan Invoice '{invoice_query}' tidak ditemukan atau belum terdaftar."

    return render_template("transaksi/cek-pesanan-saya.html", invoice=invoice_query, pesanan=pesanan, error=error_msg)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=os.getenv("FLASK_DEBUG", "True") == "True")