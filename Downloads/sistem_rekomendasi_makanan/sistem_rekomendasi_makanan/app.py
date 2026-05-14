# =========================================================
# APP.PY
# SISTEM REKOMENDASI MAKANAN SEHAT
# HYBRID RULE-BASED + SCORING
# =========================================================

import random
import io
import gspread
import csv
import os

from google.oauth2.service_account import Credentials

from flask import (
    Flask,
    render_template,
    request,
    send_file,
    redirect,
    url_for
)

from PIL import (
    Image,
    ImageDraw,
    ImageFont
)

app = Flask(__name__)

# =========================================================
# GLOBAL
# =========================================================
last_result = {}

# =========================================================
# HITUNG BMI
# =========================================================
def hitung_bmi(berat, tinggi):

    tinggi_meter = tinggi / 100

    bmi = berat / (tinggi_meter ** 2)

    return round(bmi, 1)

# =========================================================
# KATEGORI BMI
# =========================================================
def kategori_bmi(bmi):

    if bmi < 18.5:
        return "Kurus"

    elif bmi < 25:
        return "Normal"

    elif bmi < 30:
        return "Overweight"

    else:
        return "Obesitas"

# =========================================================
# HITUNG BMR
# =========================================================
def hitung_bmr(gender, berat, tinggi, usia):

    if gender == "Laki-laki":

        return (
            10 * berat +
            6.25 * tinggi -
            5 * usia + 5
        )

    return (
        10 * berat +
        6.25 * tinggi -
        5 * usia - 161
    )

# =========================================================
# HITUNG KALORI
# =========================================================
def hitung_kalori(bmr, aktivitas):

    faktor = {

        "Ringan": 1.2,

        "Sedang": 1.55,

        "Berat": 1.725
    }

    return bmr * faktor[aktivitas]

# =========================================================
# PENYESUAIAN TUJUAN
# =========================================================
def sesuaikan_tujuan(kalori, tujuan):

    if tujuan == "Menurunkan Berat Badan":

        kalori *= 0.8

    elif tujuan == "Menambah Massa Otot":

        kalori *= 1.15

    return round(kalori)

# =========================================================
# AMBIL DATA MAKANAN
# =========================================================
def ambil_data():

    data = []

    with open(
        'data_makanan_lengkap.csv',
        newline='',
        encoding='utf-8'
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            data.append({

                "nama": row["nama"],

                "kalori": int(row["kalori"]),

                "protein": int(row["protein"]),

                "lemak": int(row["lemak"]),

                "karbohidrat": int(row["karbohidrat"]),

                "kategori": row["kategori"],

                "deskripsi": row["deskripsi"],

                "sumber_protein": row["sumber_protein"],

                "sumber_karbo": row["sumber_karbo"],

                "sumber_serat": row["sumber_serat"]

            })

    return data

# =========================================================
# PILIH MENU BERDASARKAN SCORING
# =========================================================
def pilih_menu(data_list, target):

    kandidat = sorted(

        data_list,

        key=lambda x: abs(
            x["kalori"] - target
        )
    )

    return random.choice(kandidat[:5])

# =========================================================
# BUAT MEAL PLAN
# =========================================================
def buat_meal_plan(kebutuhan_kalori):

    data = ambil_data()

    hari_list = [

        "Senin",
        "Selasa",
        "Rabu",
        "Kamis",
        "Jumat",
        "Sabtu",
        "Minggu"
    ]

    meal_plan = []

    sarapan_list = [
        x for x in data
        if x["kategori"] == "Sarapan"
    ]

    siang_list = [
        x for x in data
        if x["kategori"] == "Makan Siang"
    ]

    malam_list = [
        x for x in data
        if x["kategori"] == "Makan Malam"
    ]

    buah_list = [
        x for x in data
        if x["kategori"] == "Buah"
    ]

    minuman_list = [
        x for x in data
        if x["kategori"] == "Minuman"
    ]

    cemilan_list = [
        x for x in data
        if x["kategori"] == "Cemilan"
    ]

    for hari in hari_list:

        sarapan = pilih_menu(
            sarapan_list,
            kebutuhan_kalori * 0.25
        )

        siang = pilih_menu(
            siang_list,
            kebutuhan_kalori * 0.35
        )

        malam = pilih_menu(
            malam_list,
            kebutuhan_kalori * 0.25
        )

        buah = pilih_menu(
            buah_list,
            kebutuhan_kalori * 0.05
        )

        minuman = pilih_menu(
            minuman_list,
            kebutuhan_kalori * 0.03
        )

        cemilan = pilih_menu(
            cemilan_list,
            kebutuhan_kalori * 0.07
        )

        total = (

            sarapan["kalori"] +

            siang["kalori"] +

            malam["kalori"] +

            buah["kalori"] +

            minuman["kalori"] +

            cemilan["kalori"]

        )

        meal_plan.append({

            "hari": hari,

            "sarapan": sarapan,

            "siang": siang,

            "malam": malam,

            "buah": buah,

            "minuman": minuman,

            "cemilan": cemilan,

            "total": total
        })

    return meal_plan

# =========================================================
# SIMPAN CSV
# =========================================================
def connect_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(
        'credentials.json', scopes=scope
    )
    client = gspread.authorize(creds)
    return client.open_by_key('1EobTwQTF4eyx9caOHFwkWrSdORWpM5LEkbQcA1V6XH4')

def simpan_data_pengguna(data):
    try:
        sheet = connect_sheet()
        ws = sheet.worksheet('Data Pengguna')
        ws.append_row(data)
        print("Data pengguna berhasil masuk!")
    except Exception as e:
        print(f"ERROR: {e}")

def simpan_feedback(data):
    try:
        sheet = connect_sheet()
        ws = sheet.worksheet('Data Feedback')
        ws.append_row(data)
        print("Feedback berhasil masuk!")
    except Exception as e:
        print(f"ERROR: {e}")

# =========================================================
# ROUTE UTAMA
# =========================================================
@app.route('/', methods=['GET', 'POST'])
def index():

    global last_result

    rekomendasi = None

    total_kalori = None

    bmi = None

    kategori = None

    tujuan = None

    nama = ""

    gender = ""

    usia = ""

    berat = ""

    tinggi = ""

    aktivitas = ""

    if request.method == 'POST':

        nama = request.form.get('nama')

        gender = request.form.get('gender')

        usia = int(request.form.get('usia'))

        berat = float(request.form.get('berat'))

        tinggi = float(request.form.get('tinggi'))

        aktivitas = request.form.get('aktivitas')

        tujuan = request.form.get('tujuan')

        bmi = hitung_bmi(
            berat,
            tinggi
        )

        kategori = kategori_bmi(
            bmi
        )

        bmr = hitung_bmr(
            gender,
            berat,
            tinggi,
            usia
        )

        total_kalori = hitung_kalori(
            bmr,
            aktivitas
        )

        total_kalori = sesuaikan_tujuan(
            total_kalori,
            tujuan
        )

        rekomendasi = buat_meal_plan(
            total_kalori
        )

        simpan_data_pengguna([
            nama, gender, usia, berat, tinggi,
            aktivitas, tujuan, bmi, kategori, total_kalori
        ])

        last_result = {

            "nama": nama,
            "gender": gender,
            "usia": usia,
            "berat": berat,
            "tinggi": tinggi,
            "aktivitas": aktivitas,
            "tujuan": tujuan,
            "bmi": bmi,
            "kategori": kategori,
            "total_kalori": total_kalori,
            "rekomendasi": rekomendasi
        }

    return render_template(

        'index.html',

        rekomendasi=rekomendasi,

        total_kalori=total_kalori,

        bmi=bmi,

        kategori=kategori,

        tujuan=tujuan,

        nama=nama,

        gender=gender,

        usia=usia,

        berat=berat,

        tinggi=tinggi,

        aktivitas=aktivitas
    )

# =========================================================
# DOWNLOAD HASIL GAMBAR
# =========================================================
@app.route('/download_hasil')
def download_hasil():

    global last_result

    import tempfile, os
    from jinja2 import Environment, FileSystemLoader
    from playwright.sync_api import sync_playwright

    # Render HTML template with meal plan data
    template_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'templates'
    )
    env      = Environment(loader=FileSystemLoader(template_path))
    template = env.get_template('meal_plan_download.html')

    html_content = template.render(
        nama          = last_result['nama'],
        bmi           = last_result['bmi'],
        kategori      = last_result['kategori'],
        total_kalori  = last_result['total_kalori'],
        rekomendasi   = last_result['rekomendasi'],
    )

    # Screenshot via Playwright → PNG
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page    = browser.new_page(viewport={'width': 1400, 'height': 900})
        page.set_content(html_content, wait_until='networkidle')

        # Full-page screenshot at 2x device scale for crisp quality
        png_bytes = page.screenshot(
            full_page    = True,
            scale        = 'device',
        )
        browser.close()

    img_io = io.BytesIO(png_bytes)
    img_io.seek(0)
    return send_file(
        img_io,
        mimetype      = 'image/png',
        as_attachment = True,
        download_name = 'meal_plan_mingguan.png'
    )

# =========================================================
# FEEDBACK
# =========================================================
@app.route('/feedback', methods=['POST'])
def feedback():

    data = [

        request.form.get('nama'),
        request.form.get('gender'),
        request.form.get('usia'),
        request.form.get('berat'),
        request.form.get('tinggi'),
        request.form.get('aktivitas'),
        request.form.get('tujuan'),
        request.form.get('bmi'),
        request.form.get('kategori'),
        request.form.get('kalori'),
        request.form.get('rating'),
        request.form.get('feedback')

    ]

    simpan_feedback([
        request.form.get('nama'),
        request.form.get('rating'),
        request.form.get('feedback')
    ])

    return redirect(url_for('index'))

# =========================================================
# RUN
# =========================================================
if __name__ == '__main__':
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
