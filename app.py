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

from supabase import create_client, Client

# 1. Muat Environment Variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "haisen_official_secret_2026")

# Supabase Client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# KEAMANAN: HOST/DOMAIN WHITELISTING
# ==========================================
ALLOWED_HOSTS = [
    '127.0.0.1:5000', 
    'profile.haisen.my.id',
    'www.haisen.my.id',
    'haisen.my.id', 
    'profile-haisen-2026-faqms11ph-husain-mulyansyah.vercel.app',
    'profile-haisen-2026-ftgtmuw3z-husain-mulyansyah.vercel.app' 
]

@app.before_request
def restrict_host():
    if request.host not in ALLOWED_HOSTS:
        abort(403) 

# ==========================================
# SISTEM DATABASE SUPABASE
# ==========================================
TABLE_NAME = "transaksi"
TABLE_PRODUK = "produk"
TABLE_KATEGORI = "kategori"

def get_db():
    return supabase.table(TABLE_NAME).select("*").execute().data

def add_to_db(data):
    return supabase.table(TABLE_NAME).insert(data).execute()

def update_db(order_id, data):
    return supabase.table(TABLE_NAME).update(data).eq("id", order_id).execute()

# --- Fungsi Produk & Kategori ---
def get_semua_produk():
    response = supabase.table(TABLE_PRODUK).select("id, nama, harga, deskripsi, kategori_id, kategori(nama)").execute()
    return response.data

def get_semua_kategori():
    response = supabase.table(TABLE_KATEGORI).select("*").execute()
    return response.data

app.permanent_session_lifetime = timedelta(minutes=60)

# 2. Inisialisasi Midtrans Core API
IS_PRODUCTION = os.getenv("MIDTRANS_IS_PRODUCTION", "False").lower() == "true"
core = midtransclient.CoreApi(
    is_production=IS_PRODUCTION,
    server_key=os.getenv("MIDTRANS_SERVER_KEY"),
    client_key=os.getenv("MIDTRANS_CLIENT_KEY"),
)

# 3. Data Katalog Produk
def load_katalog():
    katalog_path = os.path.join(os.path.dirname(__file__), "core", "KATALOG_PRODUK_DETAIL.json")
    with open(katalog_path, "r", encoding="utf-8") as f:
        return json.load(f)

KATALOG_PRODUK_DETAIL = load_katalog()

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

@app.route("/admin/produk")
@admin_required
def admin_produk():
    produk = get_semua_produk()
    return render_template("admin/dashboard/produk.html", produk=produk, kategori=get_semua_kategori())

@app.route("/admin/kategori")
@admin_required
def admin_kategori():
    kategori = get_semua_kategori()
    print(f"DEBUG: Kategori fetched: {kategori}")
    return render_template("admin/dashboard/kategori.html", kategori=kategori)

@app.route("/api/produk", methods=["POST", "PUT", "DELETE"])
@admin_required
def api_produk():
    try:
        if request.method == "POST":
            data = request.json
            supabase.table(TABLE_PRODUK).insert(data).execute()
            return jsonify({"status": "success"}), 201
        
        if request.method == "PUT":
            data = request.json
            produk_id = data.pop("id")
            supabase.table(TABLE_PRODUK).update(data).eq("id", produk_id).execute()
            return jsonify({"status": "success"}), 200
            
        if request.method == "DELETE":
            produk_id = request.json.get("id")
            supabase.table(TABLE_PRODUK).delete().eq("id", produk_id).execute()
            return jsonify({"status": "success"}), 200
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/pesanan", methods=["PUT"])
@admin_required
def api_pesanan():
    try:
        data = request.json
        update_db(data['id'], {"status_proyek": data['status_proyek']})
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/admin/logout")
def admin_logout():
    session.pop('is_admin_logged_in', None)
    return redirect(url_for('admin_login'))

# ==========================================
# HELPER SINKRONISASI
# ==========================================
def sync_transaction_status(transaction):
    """Sinkronisasi status transaksi dengan Midtrans API."""
    if transaction.get("status_bayar") == "pending":
        try:
            status_response = core.transactions.status(transaction["id"])
            new_status = status_response.get("transaction_status")
            if new_status != "pending":
                new_proyek_status = "In Progress" if new_status in ['settlement', 'capture'] else "Dibatalkan"
                update_db(transaction["id"], {
                    "status_bayar": new_status,
                    "status_proyek": new_proyek_status
                })
                transaction["status_bayar"] = new_status
                transaction["status_proyek"] = new_proyek_status
        except Exception as e:
            print(f"Error syncing {transaction['id']}: {e}")
            pass
    return transaction

# ==========================================
# RUTE ADMIN DASHBOARD
# ==========================================
@app.route("/admin")
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    db = get_db()
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
    db = get_db()
    for p in db:
        sync_transaction_status(p)
        p["status"] = p["status_proyek"]
    return render_template("admin/dashboard/pesanan.html", pesanan=list(reversed(db)))

@app.route("/admin/transaksi")
@admin_required
def admin_transaksi():
    db = get_db()
    for t in db:
        sync_transaction_status(t)
        t["jumlah"] = f"Rp {t['jumlah']:,}".replace(',', '.')
        # Sinkronisasi status untuk tampilan template (template mengharapkan Settlement/Pending)
        if t["status_bayar"] in ['settlement', 'capture']:
            t["status_bayar"] = "Settlement"
        elif t["status_bayar"] == "pending":
            t["status_bayar"] = "Pending"
        else:
            t["status_bayar"] = "Gagal/Batal"
            
    return render_template("admin/dashboard/transaksi.html", transaksi=list(reversed(db)))

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
            
            # Simpan ke Supabase
            add_to_db({
                "id": order_id, "nama": nama, "email": email, "whatsapp": whatsapp,
                "layanan": detail_produk["nama"], "metode": payment_method.upper(),
                "jumlah": harga, "status_bayar": "pending",
                "status_proyek": "Menunggu Pembayaran", "tanggal": datetime.now().strftime("%d %b %Y %H:%M")
            })

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
        
        # Update di Supabase
        update_db(order_id, {
            "status_bayar": transaction_status,
            "status_proyek": "In Progress" if transaction_status in ['settlement', 'capture'] else "Dibatalkan"
        })
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
def produk(): return render_template("produk/produk.html")


@app.route("/debug-templates")
def debug_templates():
    import os
    # Mendapatkan path absolut folder templates
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    
    files_list = []
    if os.path.exists(template_dir):
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                files_list.append(os.path.join(root, file))
        return jsonify({"status": "OK", "found_files": files_list})
    else:
        return jsonify({"status": "Error", "message": "Folder templates tidak ditemukan di server!"})
    

@app.route("/detail-produk")
def detail_produk():
    produk_id = request.args.get("id", "rfid-timing")
    if produk_id not in KATALOG_PRODUK_DETAIL:
        produk_id = "rfid-timing"
    produk_data = KATALOG_PRODUK_DETAIL.get(produk_id, {})
    return render_template("produk/detail_produk.html", produk_id=produk_id, produk=produk_data)

@app.route("/cek-pesanan")
def cek_pesanan():
    invoice_query = request.args.get("query", "").strip()
    pesanan = None
    error_msg = None

    if invoice_query:
        try:
            # Ambil data dari Supabase
            response = supabase.table(TABLE_NAME).select("*").eq("id", invoice_query).single().execute()
            
            if response.data:
                p = response.data
                # Sinkronisasi status jika masih pending
                sync_transaction_status(p)
                
                pesanan = {
                    "order_id": p["id"],
                    "nama": p["nama"],
                    "email": p["email"],
                    "whatsapp": p["whatsapp"],
                    "layanan": p["layanan"],
                    "metode": p["metode"],
                    "jumlah": p["jumlah"],
                    "status_bayar": p["status_bayar"],
                    "status_proyek": p["status_proyek"],
                    "gross_amount_format": f"Rp {int(p['jumlah']):,}".replace(",", "."),
                    "waktu": p["tanggal"]
                }
            else:
                error_msg = f"Pesanan dengan Invoice '{invoice_query}' tidak ditemukan."
                
        except Exception as e:
            error_msg = f"Terjadi kesalahan saat mencari pesanan: {str(e)}"

    return render_template("transaksi/cek-pesanan-saya.html", invoice=invoice_query, pesanan=pesanan, error=error_msg)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=os.getenv("FLASK_DEBUG", "True") == "True")