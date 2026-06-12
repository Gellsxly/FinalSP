import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
import requests
import database

app = Flask(__name__)
app.secret_key = 'sistem_pakar_certainty_factor_secret_key'

# Inisialisasi database MySQL saat aplikasi berjalan
db_error = False
try:
    database.init_db()
except Exception as e:
    print("WARNING: Database MySQL tidak aktif. Silakan aktifkan MySQL via XAMPP Control Panel.", e)
    db_error = True

# Middleware untuk mengecek koneksi database
@app.before_request
def check_db_connection():
    global db_error
    # Jangan cegat request static files
    if request.path.startswith('/static'):
        return
        
    if db_error:
        # Coba koneksi lagi
        try:
            database.init_db()
            db_error = False
        except Exception:
            # Jika masih gagal, render halaman error khusus
            return render_template('db_error.html')

# --- Decorators untuk Proteksi Route ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan masuk (login) terlebih dahulu untuk melanjutkan.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan masuk (login) terlebih dahulu.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Akses ditolak. Halaman ini hanya untuk Administrator.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Daftar Penyakit & Gejala (Saran level-based) ---
PENYAKIT = {
    'MB1': {
        'nama': 'Skizofrenia',
        'deskripsi': 'Gangguan mental berat yang memengaruhi cara seseorang berpikir, merasa, dan berperilaku. Penderita mungkin tampak seperti kehilangan kontak dengan kenyataan, ditandai dengan halusinasi, delusi, dan pola komunikasi yang kacau.',
        'saran': {
            'rendah': 'Meskipun tingkat kepastian tergolong rendah, waspadai adanya kecenderungan menarik diri dari lingkungan sosial dan pola pikir yang tidak teratur. Disarankan untuk beristirahat dengan cukup, membatasi paparan stresor berat, serta menceritakan kondisi kecemasan Anda kepada orang terdekat. Lakukan evaluasi gejala secara berkala.',
            'sedang': 'Gejala menunjukkan indikasi sedang ke arah gangguan persepsi atau komunikasi yang kurang terorganisir. Disarankan untuk mulai berkonsultasi dengan konselor profesional atau psikolog klinis untuk konseling awal. Hindari lingkungan yang memicu kecemasan ekstrem, dan cobalah untuk tetap terhubung secara aktif dengan keluarga atau teman tepercaya.',
            'tinggi': 'Sangat direkomendasikan untuk segera menemui Psikiater (Dokter Spesialis Kedokteran Jiwa) untuk mendapatkan diagnosis medis formal dan terapi antipsikotik. Terapi kognitif perilaku (CBT) dan dukungan sosial keluarga sangat disarankan untuk membantu proses rehabilitasi. Dukungan penuh dan pengawasan ketat dari keluarga sangat krusial pada tahap ini guna menjamin keselamatan pasien.'
        }
    },
    'MB2': {
        'nama': 'Obsessive Compulsive Disorder (OCD)',
        'deskripsi': 'Gangguan mental yang menyebabkan seseorang memiliki pikiran yang tidak diinginkan (obsesi) dan dorongan untuk melakukan tindakan secara berulang-ulang (kompulsi) untuk mengurangi kecemasan tersebut.',
        'saran': {
            'rendah': 'Kecenderungan perilaku obsesif atau kecemasan berulang masih bersifat ringan. Cobalah teknik relaksasi pikiran, meditasi, serta latihan untuk menunda dorongan kompulsif secara bertahap (misal: menunda mencuci tangan beberapa menit). Catat pemicu kecemasan Anda dalam jurnal.',
            'sedang': 'Pikiran obsesif dan tindakan berulang sudah mulai mengganggu produktivitas harian Anda. Sangat disarankan berkonsultasi dengan psikolog untuk menjalani terapi kognitif perilaku awal, khususnya latihan manajemen kecemasan dan metode Exposure and Response Prevention (ERP) ringan.',
            'tinggi': 'Obsesi dan kompulsi berada pada tingkat yang sangat mengganggu aktivitas sehari-hari secara signifikan. Segera hubungi Psikolog Klinis atau Psikiater untuk penanganan intensif (terapi ERP formal) dan pertimbangkan opsi pengobatan medis jika diresepkan oleh psikiater guna membantu menyeimbangkan kecemasan.'
        }
    },
    'MB3': {
        'nama': 'Anorexia Nervosa',
        'deskripsi': 'Gangguan makan yang ditandai dengan ketakutan ekstrem terhadap kenaikan berat badan, pembatasan asupan makanan secara ekstrem, dan persepsi tubuh yang terdistorsi secara tidak realistis.',
        'saran': {
            'rendah': 'Waspadai adanya kecemasan awal mengenai berat badan atau bentuk tubuh. Disarankan untuk mulai menerapkan pola makan teratur dan seimbang, berkonsultasi dengan ahli gizi untuk panduan nutrisi sehat, serta fokus pada kesehatan tubuh alih-alih angka pada timbangan.',
            'sedang': 'Gejala pembatasan makanan dan ketakutan akan kenaikan berat badan mulai mengganggu kesehatan fisik Anda. Disarankan untuk melakukan konseling dengan psikolog klinis guna mengatasi distorsi citra tubuh (body image) serta berkonsultasi dengan dokter umum untuk memantau indikator vital tubuh Anda.',
            'tinggi': 'Tingkat kepastian sangat tinggi dan berisiko mengancam jiwa akibat malnutrisi ekstrem. Sangat disarankan segera berkonsultasi dengan tim medis multidisiplin yang melibatkan Psikiater (untuk aspek psikologis), Psikolog Klinis (terapi citra tubuh), and Ahli Gizi (untuk pemulihan nutrisi intensif).'
        }
    },
    'MB4': {
        'nama': 'Depresi',
        'deskripsi': 'Gangguan suasana hati (mood) yang ditandai dengan perasaan sedih yang mendalam, kehilangan minat atau kegembiraan terhadap aktivitas sehari-hari, rasa bersalah, insomnia, serta keputusasaan yang berlangsung lama.',
        'saran': {
            'rendah': 'Perasaan sedih yang mendalam atau hilangnya minat masih tergolong ringan. Disarankan untuk meningkatkan aktivitas fisik ringan (seperti olahraga), menjaga jadwal tidur yang konsisten, bergaul dengan orang terdekat, serta menghindari isolasi diri.',
            'sedang': 'Rasa putus asa, rasa bersalah, atau gangguan tidur mulai mengganggu rutinitas harian Anda secara nyata. Sangat disarankan untuk menjadwalkan sesi konseling tatap muka dengan psikolog untuk terapi psikologis seperti Terapi Kognitif Perilaku (CBT) guna membantu mengurai pola pikir negatif.',
            'tinggi': 'Kondisi depresi berada pada tingkat yang sangat berat dan membutuhkan perhatian mendesak. Segera hubungi Psikiater atau Psikolog Klinis untuk terapi intensif dan penanganan medis (seperti obat antidepresan). Pastikan lingkungan aman dan didampingi keluarga terdekat untuk mencegah tindakan membahayakan diri sendiri.'
        }
    },
    'MB5': {
        'nama': 'Self Injuries',
        'deskripsi': 'Perilaku menyakiti atau melukai diri sendiri secara sengaja (seperti menyayat kulit atau membenturkan kepala) sebagai cara maladaptif untuk meluapkan tekanan emosional, kemarahan, atau rasa sakit psikologis yang mendalam.',
        'saran': {
            'rendah': 'Dorongan untuk menyakiti diri sendiri saat menghadapi tekanan emosional masih tergolong jarang/awal. Pelajari teknik koping alternatif saat emosi meluap (seperti memegang es batu, merobek kertas, menulis emosi di kertas, atau berolahraga), dan carilah bantuan dari orang yang Anda percayai.',
            'sedang': 'Dorongan menyakiti diri sendiri sebagai pelampiasan emosi mulai sering muncul. Sangat disarankan untuk segera berkonsultasi dengan psikolog klinis guna mengidentifikasi akar emosi dan mempelajari teknik regulasi emosi yang aman bagi diri sendiri.',
            'tinggi': 'Tindakan melukai diri sendiri sudah dilakukan secara aktif atau memiliki intensitas bahaya yang tinggi. SANGAT PENTING untuk segera menemui Psikiater atau Psikolog Klinis untuk penanganan darurat/terapi psikologis intensif. Amankan barang-barang berbahaya dari sekitar Anda dan pastikan ada pendampingan penuh dari keluarga.'
        }
    },
    'MB6': {
        'nama': 'Homoseksual',
        'deskripsi': 'Berdasarkan aturan model Certainty Factor yang Anda miliki, kategori ini mendeteksi tingkat kepastian ketertarikan seksual dan emosional yang dominan terhadap sesama jenis serta kurangnya hasrat pada lawan jenis.',
        'saran': {
            'rendah': 'Konflik atau ketertarikan emosional/seksual terhadap sesama jenis masih berada di tingkat awal. Gunakan waktu untuk memahami diri secara tenang tanpa tekanan. Disarankan untuk berdiskusi dengan konselor terpercaya untuk eksplorasi diri yang sehat.',
            'sedang': 'Tekanan psikologis atau konflik identitas diri mulai memicu kecemasan atau depresi sedang. Disarankan untuk berkonsultasi dengan psikolog atau konselor profesional guna mengeksplorasi emosi secara sehat, mengatasi konflik internal/eksternal akibat tekanan sosial, serta meningkatkan pemahaman diri.',
            'tinggi': 'Tingkat kepastian ketertarikan sesama jenis sangat tinggi berdasarkan kriteria yang dipilih, disertai konflik emosional mendalam akibat tekanan lingkungan. Sangat disarankan berkonsultasi dengan konselor psikologi profesional atau psikolog klinis untuk terapi suportif, manajemen stres, memperkuat kestabilan emosional, serta penerimaan diri secara sehat guna mencegah kecemasan.'
        }
    }
}

GEJALA = {
    'G001': 'Munculnya halusinasi secara visual dan pendengaran',
    'G002': 'Berkomunikasi kacau',
    'G003': 'Suka menyendiri',
    'G004': 'Tingkah laku tidak dapat mengontrol',
    'G005': 'Obsesi (pikiran) dan kompulsi (prilaku) sifatnya berulang-ulang',
    'G006': 'Selalu cemas dalam tindakan',
    'G007': 'Pikiran dan tindakan yang merasakan kekhawatiran yang berlebihan',
    'G008': 'Terobsesi melukai tubuh diri sendiri',
    'G009': 'Terganggunya kegiatan sosial dan hubungan dengan orang lain',
    'G010': 'Tidak mau mempertahankan berat badan pada level normal',
    'G011': 'Ketakutan bahwa berat akan naik',
    'G012': 'Tidak mengalami mentrulasi',
    'G013': 'Evaluasi yang tidak pas terhadap berat badan atau bentuk tubuhnya',
    'G014': 'Rasa cemas yang tidak dapat dikendalikan',
    'G015': 'Rasa putus asa yang luar biasa',
    'G016': 'Rasa berasalah yang luar biasa',
    'G017': 'Tidak dapat nyenyak atau mengalami insomnia',
    'G018': 'Kegelisahan yang berlebihan',
    'G019': 'Selalu menghindari masalah',
    'G020': 'Sulit mengendalikan emosi',
    'G021': 'Kurang mampu mengurus dirinya sendiri',
    'G022': 'Tidak berfikir logis',
    'G023': 'Tidak menyukai dirinya sendiri',
    'G024': 'Tidak suka akan perubahan',
    'G025': 'Mengalami rasa yang berlebihan terhadap sesama jenis',
    'G026': 'Memiliki kelainan dalam prilaku',
    'G027': 'Memiliki sensitifitas yang sangat berlebihan',
    'G028': 'Kesulitan mengontrol hasrat seksual',
    'G029': 'Merasakan kesan yang berbeda ketika bergaul sesama jenis',
    'G030': 'Tidak memiliki hasrat pada lawan jenis'
}

CF_EXPERT = {
    'MB1': {
        'G001': 0.8,
        'G002': 0.6,
        'G003': 0.4,
        'G004': 0.6,
        'G022': 0.8
    },
    'MB2': {
        'G005': 0.8,
        'G006': 0.6,
        'G007': 0.6,
        'G009': 0.4,
        'G014': 0.4,
        'G024': 0.4
    },
    'MB3': {
        'G010': 0.8,
        'G011': 0.8,
        'G012': 0.6,
        'G013': 0.6,
        'G023': 0.4
    },
    'MB4': {
        'G003': 0.4,
        'G009': 0.4,
        'G014': 0.6,
        'G015': 0.8,
        'G016': 0.6,
        'G017': 0.6,
        'G018': 0.4,
        'G019': 0.4,
        'G020': 0.4,
        'G021': 0.4
    },
    'MB5': {
        'G008': 0.8,
        'G023': 0.8,
        'G026': 0.4,
        'G027': 0.4,
        'G028': 0.6
    },
    'MB6': {
        'G025': 0.8,
        'G026': 0.4,
        'G027': 0.4,
        'G028': 0.6,
        'G029': 0.8,
        'G030': 0.8
    }
}

PILIHAN_USER = {
    'Tidak Pasti': 0.0,
    'Kurang Yakin': 0.2,
    'Cukup Yakin': 0.4,
    'Yakin': 0.6,
    'Sangat Yakin': 0.8,
    'Pasti': 1.0
}

@app.route('/')
def index():
    return render_template('index.html')

# --- AUTH ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not nama or not email or not password:
            flash('Semua kolom wajib diisi.', 'danger')
            return render_template('register.html')
            
        # Periksa apakah email sudah terdaftar
        user_exist = database.get_user_by_email(email)
        if user_exist:
            flash('Email sudah terdaftar. Silakan login.', 'warning')
            return redirect(url_for('login'))
            
        success = database.create_user(email, password, nama)
        if success:
            flash('Registrasi berhasil! Silakan masuk.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registrasi gagal. Coba lagi.', 'danger')
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        user = database.get_user_by_email(email)
        if user and user['password_hash'] and database.check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['nama'] = user['nama']
            session['role'] = user['role']
            flash(f'Selamat datang kembali, {user["nama"]}!', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        else:
            flash('Email atau password salah.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda berhasil keluar dari sistem.', 'success')
    return redirect(url_for('login'))

@app.route('/login-google', methods=['POST'])
def login_google():
    data = request.get_json()
    token = data.get('credential')
    if not token:
        return jsonify({'success': False, 'message': 'Token tidak ditemukan.'}), 400
        
    try:
        # Verifikasi token lewat Google Token Info API (sederhana & tanpa library berat)
        resp = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={token}")
        if resp.status_code != 200:
            return jsonify({'success': False, 'message': 'Token Google tidak valid.'}), 400
            
        id_info = resp.json()
        email = id_info.get('email')
        google_id = id_info.get('sub')
        nama = id_info.get('name', email.split('@')[0])
        
        if not email or not google_id:
            return jsonify({'success': False, 'message': 'Informasi akun Google tidak lengkap.'}), 400
            
        user = database.create_or_get_google_user(email, google_id, nama)
        if user:
            session['user_id'] = user['id']
            session['nama'] = user['nama']
            session['role'] = user['role']
            return jsonify({'success': True, 'redirect': url_for('index')})
        else:
            return jsonify({'success': False, 'message': 'Gagal memproses data pengguna.'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# --- DIAGNOSE ROUTES ---

@app.route('/diagnose', methods=['GET', 'POST'])
@login_required
def diagnose():
    if request.method == 'POST':
        nama = request.form.get('nama', session.get('nama', 'User Anonim')).strip()
        if not nama:
            nama = session.get('nama', 'User Anonim')
            
        # Mengambil pilihan user untuk 30 gejala
        user_responses = {}
        for g_code in GEJALA.keys():
            response_key = request.form.get(g_code, 'Tidak Pasti')
            cf_val = PILIHAN_USER.get(response_key, 0.0)
            user_responses[g_code] = {
                'key': response_key,
                'val': cf_val
            }
            
        # Perhitungan Certainty Factor untuk masing-masing penyakit
        hasil_perhitungan = {}
        perhitungan_langkah = {}

        for p_code, p_info in PENYAKIT.items():
            cf_he_list = []
            langkah = []
            
            for g_code, cf_expert_val in CF_EXPERT[p_code].items():
                cf_user_val = user_responses[g_code]['val']
                cf_he = round(cf_user_val * cf_expert_val, 4)
                
                if cf_he > 0:
                    cf_he_list.append(cf_he)
                    langkah.append({
                        'gejala_kode': g_code,
                        'gejala_nama': GEJALA[g_code],
                        'cf_user': cf_user_val,
                        'cf_expert': cf_expert_val,
                        'cf_he': cf_he
                    })
            
            cf_final = 0.0
            if cf_he_list:
                cf_final = cf_he_list[0]
                gabungan_steps = []
                for i in range(1, len(cf_he_list)):
                    cf_old = cf_final
                    cf_new = cf_he_list[i]
                    cf_final = cf_old + cf_new * (1.0 - cf_old)
                    cf_final = round(cf_final, 4)
                    gabungan_steps.append({
                        'cf_old': cf_old,
                        'cf_new': cf_new,
                        'hasil': cf_final
                    })
                
                perhitungan_langkah[p_code] = {
                    'he_steps': langkah,
                    'combine_steps': gabungan_steps,
                    'cf_final': cf_final
                }
            else:
                perhitungan_langkah[p_code] = {
                    'he_steps': [],
                    'combine_steps': [],
                    'cf_final': 0.0
                }
                
            hasil_perhitungan[p_code] = cf_final
            
        # Cari penyakit dengan CF tertinggi
        penyakit_tertinggi = max(hasil_perhitungan, key=hasil_perhitungan.get)
        cf_tertinggi = hasil_perhitungan[penyakit_tertinggi]
        
        # Simpan ke Database MySQL
        rincian_dict = {}
        for p_code, val in hasil_perhitungan.items():
            rincian_dict[PENYAKIT[p_code]['nama']] = val
            
        rincian_penuh = {
            'cf_values': rincian_dict,
            'langkah_detail': perhitungan_langkah,
            'user_responses': {g: res['key'] for g, res in user_responses.items()}
        }
        
        last_id = database.save_diagnosa(
            user_id=session['user_id'],
            nama=nama,
            hasil_penyakit=PENYAKIT[penyakit_tertinggi]['nama'],
            hasil_cf=cf_tertinggi,
            rincian_dict=rincian_penuh
        )
        
        return redirect(url_for('result', result_id=last_id))
        
    return render_template('diagnose.html', gejala=GEJALA, pilihan=PILIHAN_USER)

@app.route('/result/<int:result_id>')
@login_required
def result(result_id):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM diagnosa WHERE id = %s', (result_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        flash('Riwayat diagnosis tidak ditemukan.', 'danger')
        return redirect(url_for('index'))
        
    # Validasi kepemilikan data (kecuali admin)
    if row['user_id'] != session['user_id'] and session.get('role') != 'admin':
        flash('Anda tidak memiliki akses untuk melihat riwayat diagnosa ini.', 'danger')
        return redirect(url_for('index'))
        
    import json
    rincian_penuh = json.loads(row['rincian_json'])
    
    penyakit_info = None
    for p_code, p_val in PENYAKIT.items():
        if p_val['nama'] == row['hasil_penyakit']:
            # copy dictionary to avoid mutating global PENYAKIT
            penyakit_info = p_val.copy()
            penyakit_info['kode'] = p_code
            break
            
    if not penyakit_info:
        penyakit_info = {
            'kode': 'MB1',
            'nama': row['hasil_penyakit'],
            'deskripsi': 'Gangguan mental terdeteksi.',
            'saran': {
                'rendah': 'Konsultasikan dengan konselor terdekat untuk diskusi awal.',
                'sedang': 'Disarankan berkonsultasi dengan psikolog untuk konseling awal.',
                'tinggi': 'Sangat disarankan segera berkonsultasi dengan psikolog klinis atau psikiater.'
            }
        }
        
    return render_template(
        'result.html', 
        diagnosa=row, 
        penyakit_info=penyakit_info, 
        rincian=rincian_penuh,
        semua_penyakit=PENYAKIT
    )

@app.route('/history')
@login_required
def history():
    # Mengambil riwayat khusus untuk user yang sedang login
    data_history = database.get_history_by_user(session['user_id'])
    return render_template('history.html', history=data_history)

@app.route('/delete-history/<int:result_id>', methods=['POST'])
@login_required
def delete_history(result_id):
    database.delete_history_item(result_id, user_id=session['user_id'], is_admin=(session.get('role') == 'admin'))
    flash('Riwayat diagnosis berhasil dihapus.', 'success')
    if session.get('role') == 'admin':
        return redirect(request.referrer or url_for('admin_dashboard'))
    return redirect(url_for('history'))

@app.route('/clear-history', methods=['POST'])
@login_required
def clear_history():
    database.clear_all_history(user_id=session['user_id'], is_admin=(session.get('role') == 'admin'))
    flash('Semua riwayat diagnosis berhasil dibersihkan.', 'success')
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('history'))

@app.route('/rules')
def rules():
    return render_template('rules.html', gejala=GEJALA, penyakit=PENYAKIT, cf_expert=CF_EXPERT)

# --- ADMIN PANEL ROUTES ---

@app.route('/admin')
@admin_required
def admin_dashboard():
    stats = database.get_admin_stats()
    users = database.get_all_users_with_diagnose_count()
    diagnoses = database.get_all_diagnoses_with_user()
    return render_template('admin.html', stats=stats, users=users, diagnoses=diagnoses)

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    if user_id == session['user_id']:
        flash('Anda tidak dapat menghapus akun admin Anda sendiri.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()
    flash('Pengguna berhasil dihapus dari sistem.', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
