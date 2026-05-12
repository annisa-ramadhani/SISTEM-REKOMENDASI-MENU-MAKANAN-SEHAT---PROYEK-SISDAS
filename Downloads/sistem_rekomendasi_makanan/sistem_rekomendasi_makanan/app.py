# =========================================================
# APP.PY
# SISTEM REKOMENDASI MAKANAN SEHAT
# HYBRID RULE-BASED + SCORING
# =========================================================

import random
import csv
import os

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
def simpan_hasil_pengguna(data):

    file_csv = "hasil_pengguna_sistem.csv"

    file_exists = os.path.isfile(file_csv)

    with open(

        file_csv,

        mode='a',

        newline='',

        encoding='utf-8'

    ) as file:

        writer = csv.writer(file)

        if not file_exists:

            writer.writerow([

                "Nama",
                "Gender",
                "Usia",
                "Berat",
                "Tinggi",
                "Aktivitas",
                "Tujuan",
                "BMI",
                "Kategori BMI",
                "Kalori Harian",
                "Rating",
                "Feedback"

            ])

        writer.writerow(data)

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

    width = 1600
    height = 2400

    img = Image.new(
        'RGB',
        (width, height),
        color=(248, 245, 235)
    )

    draw = ImageDraw.Draw(img)

    # =====================================================
    # FONT
    # =====================================================
    try:

        title_font = ImageFont.truetype(
            'arial.ttf',
            70
        )

        sub_font = ImageFont.truetype(
            'arial.ttf',
            40
        )

        text_font = ImageFont.truetype(
            'arial.ttf',
            32
        )

        small_font = ImageFont.truetype(
            'arial.ttf',
            26
        )

    except:

        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # =====================================================
    # HEADER
    # =====================================================
    draw.rounded_rectangle(
        (20, 20, 1580, 330),
        radius=40,
        fill=(34, 94, 54)
    )

    # =====================================================
    # LOGO UNRI
    # =====================================================
    try:

        logo = Image.open('static/logo_unri.jpg')

        logo = logo.resize((120, 120))

        img.paste(logo, (50, 60), logo)

    except:
        pass

    # =====================================================
    # INFO USER
    # =====================================================
    draw.rounded_rectangle(
        (200, 60, 760, 260),
        radius=30,
        fill=(245, 240, 225)
    )

    draw.text(
        (230, 90),
        f"Nama : {last_result['nama']}",
        fill='black',
        font=sub_font
    )

    draw.text(
        (230, 145),
        f"BMI : {last_result['bmi']} ({last_result['kategori']})",
        fill='darkgreen',
        font=text_font
    )

    draw.text(
        (230, 195),
        f"Kalori : {last_result['total_kalori']} kcal",
        fill='darkgreen',
        font=text_font
    )

    # =====================================================
    # TITLE
    # =====================================================
    draw.text(
        (900, 70),
        "WEEKLY",
        fill="white",
        font=title_font
    )

    draw.text(
        (860, 160),
        "MEALS PLAN",
        fill="white",
        font=title_font
    )

    draw.text(
        (830, 255),
        "REKOMENDASI MAKANAN SEHAT",
        fill=(255, 240, 210),
        font=sub_font
    )

    # =====================================================
    # POSISI CARD
    # =====================================================
    posisi = [
        (50, 380),
        (560, 380),
        (1070, 380),
        (50, 980),
        (560, 980),
        (1070, 980),
        (50, 1580)
    ]

    warna_card = [
        (236, 245, 220),
        (250, 240, 225),
        (238, 245, 220),
        (250, 236, 220),
        (238, 245, 220),
        (250, 236, 220),
        (236, 245, 220)
    ]

    # =====================================================
    # CARD MENU
    # =====================================================
    for i, item in enumerate(last_result['rekomendasi']):

        x, y = posisi[i]

        draw.rounded_rectangle(
            (x, y, x + 450, y + 520),
            radius=30,
            fill=warna_card[i]
        )

        draw.text(
            (x + 120, y + 20),
            item['hari'].upper(),
            fill=(20, 80, 35),
            font=sub_font
        )

        yy = y + 100

        # SARAPAN
        draw.text(
            (x + 30, yy),
            "☀ Sarapan",
            fill='orange',
            font=text_font
        )

        yy += 40

        draw.text(
            (x + 60, yy),
            item['sarapan']['nama'],
            fill='black',
            font=small_font
        )

        # SIANG
        yy += 70

        draw.text(
            (x + 30, yy),
            "🍱 Makan Siang",
            fill='darkgreen',
            font=text_font
        )

        yy += 40

        draw.text(
            (x + 60, yy),
            item['siang']['nama'],
            fill='black',
            font=small_font
        )

        # MALAM
        yy += 70

        draw.text(
            (x + 30, yy),
            "🌙 Makan Malam",
            fill='gold',
            font=text_font
        )

        yy += 40

        draw.text(
            (x + 60, yy),
            item['malam']['nama'],
            fill='black',
            font=small_font
        )

        # CEMILAN
        yy += 70

        draw.text(
            (x + 30, yy),
            "🍎 Cemilan",
            fill='red',
            font=text_font
        )

        yy += 40

        draw.text(
            (x + 60, yy),
            item['cemilan']['nama'],
            fill='black',
            font=small_font
        )

    # =====================================================
    # NOTES
    # =====================================================
    draw.rounded_rectangle(
        (560, 1580, 1550, 2120),
        radius=40,
        fill=(245, 235, 210)
    )

    draw.text(
        (920, 1630),
        "NOTES",
        fill='darkgreen',
        font=sub_font
    )

    draw.text(
        (650, 1760),
        '"Makanan sehat hari ini adalah investasi"',
        fill='black',
        font=text_font
    )

    draw.text(
        (700, 1820),
        '"terbaik untuk masa depan tubuhmu."',
        fill='black',
        font=text_font
    )

    # =====================================================
    # FOOTER
    # =====================================================
    draw.rounded_rectangle(
        (250, 2200, 1350, 2280),
        radius=30,
        fill=(34, 94, 54)
    )

    draw.text(
        (420, 2225),
        "Jaga Pola Makan, Jaga Kesehatan",
        fill='white',
        font=text_font
    )

    # =====================================================
    # SAVE
    # =====================================================
    file_path = 'hasil_rekomendasi.png'

    img.save(file_path)

    return send_file(
        file_path,
        as_attachment=True
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

    simpan_hasil_pengguna(data)

    return redirect(url_for('index'))

# =========================================================
# RUN
# =========================================================
if __name__ == '__main__':
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
