import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import database

app = Flask(__name__)
app.secret_key = 'sistem_pakar_certainty_factor_secret_key'

# Inisialisasi database saat aplikasi berjalan
database.init_db()

# Daftar Penyakit / Gangguan Mental (MB)
PENYAKIT = {
    'MB1': {
        'nama': 'Skizofrenia',
        'deskripsi': 'Gangguan mental berat yang memengaruhi cara seseorang berpikir, merasa, dan berperilaku. Penderita mungkin tampak seperti kehilangan kontak dengan kenyataan, ditandai dengan halusinasi, delusi, dan pola komunikasi yang kacau.',
        'saran': 'Konsultasi segera dengan psikiater untuk terapi medis antipsikotik. Terapi kognitif perilaku (CBT) dan dukungan sosial keluarga sangat disarankan untuk membantu proses rehabilitasi.'
    },
    'MB2': {
        'nama': 'Obsessive Compulsive Disorder (OCD)',
        'deskripsi': 'Gangguan mental yang menyebabkan seseorang memiliki pikiran yang tidak diinginkan (obsesi) dan dorongan untuk melakukan tindakan secara berulang-ulang (kompulsi) untuk mengurangi kecemasan tersebut.',
        'saran': 'Lakukan terapi psikologis khusus seperti Exposure and Response Prevention (ERP). Latih manajemen kecemasan melalui meditasi atau teknik relaksasi, dan hubungi psikolog atau psikiater jika gejala mengganggu produktivitas.'
    },
    'MB3': {
        'nama': 'Anorexia Nervosa',
        'deskripsi': 'Gangguan makan yang ditandai dengan ketakutan ekstrem terhadap kenaikan berat badan, pembatasan asupan makanan secara ekstrem, dan persepsi tubuh yang terdistorsi secara tidak realistis.',
        'saran': 'Diperlukan pendekatan multidisiplin yang melibatkan psikolog (untuk terapi psikis), ahli gizi (untuk pemulihan pola makan), dan dokter umum (memantau kesehatan fisik). Dukungan keluarga sangat penting.'
    },
    'MB4': {
        'nama': 'Depresi',
        'deskripsi': 'Gangguan suasana hati (mood) yang ditandai dengan perasaan sedih yang mendalam, kehilangan minat atau kegembiraan terhadap aktivitas sehari-hari, rasa bersalah, insomnia, serta keputusasaan yang berlangsung lama.',
        'saran': 'Konseling tatap muka dengan psikolog atau psikiater untuk terapi kognitif. Jaga pola tidur yang teratur, lakukan aktivitas fisik ringan (olahraga), luapkan emosi ke orang terdekat, dan pertimbangkan pengobatan jika diresepkan medis.'
    },
    'MB5': {
        'nama': 'Self Injuries',
        'deskripsi': 'Perilaku menyakiti atau melukai diri sendiri secara sengaja (seperti menyayat kulit atau membenturkan kepala) sebagai cara maladaptif untuk meluapkan tekanan emosional, kemarahan, atau rasa sakit psikologis yang mendalam.',
        'saran': 'Segera hubungi profesional kesehatan mental (psikolog/psikiater). Pelajari teknik koping alternatif saat dorongan muncul (seperti memegang es batu, menulis emosi di kertas, atau berolahraga), dan pastikan lingkungan aman.'
    },
    'MB6': {
        'nama': 'Homoseksual',
        'deskripsi': 'Berdasarkan aturan model Certainty Factor yang Anda miliki, kategori ini mendeteksi tingkat kepastian ketertarikan seksual dan emosional yang dominan terhadap sesama jenis serta kurangnya hasrat pada lawan jenis.',
        'saran': 'Konsultasikan dengan konselor psikologi profesional untuk mengeksplorasi emosi, mengatasi konflik internal/eksternal yang mungkin timbul akibat tekanan sosial, serta meningkatkan pemahaman dan penerimaan diri yang sehat.'
    }
}

# Daftar 30 Gejala Gangguan Mental (G001 - G030)
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

# Bobot Pakar (CF Expert) untuk masing-masing penyakit
# Format: { Kode_Penyakit: { Kode_Gejala: Nilai_CF_Expert } }
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

# Pilihan tingkat keyakinan pengguna beserta nilainya
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

@app.route('/diagnose', methods=['GET', 'POST'])
def diagnose():
    if request.method == 'POST':
        nama = request.form.get('nama', 'User Anonim').strip()
        if not nama:
            nama = 'User Anonim'
            
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
        # Untuk penjelasan rumus di hasil diagnosis
        perhitungan_langkah = {}

        for p_code, p_info in PENYAKIT.items():
            cf_he_list = []
            langkah = []
            
            # Hitung CF(H,E) = CF_User * CF_Expert untuk setiap gejala penyakit ini
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
            
            # Mengkombinasikan nilai CF
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
        
        # Simpan ke Database
        # Buat dictionary untuk rincian penyakit
        rincian_dict = {}
        for p_code, val in hasil_perhitungan.items():
            rincian_dict[PENYAKIT[p_code]['nama']] = val
            
        # Simpan hasil diagnosa ke database SQLite
        conn = database.get_db_connection()
        import json
        from datetime import datetime
        tanggal_sekarang = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # Di sini kita juga akan menyimpan perhitungan_langkah dalam session/db jika ingin menampilkannya
        # Untuk memudahkan, kita taruh perhitungan_langkah ini ke rincian_json agar bisa dirender
        rincian_penuh = {
            'cf_values': rincian_dict,
            'langkah_detail': perhitungan_langkah,
            'user_responses': {g: res['key'] for g, res in user_responses.items()}
        }
        
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO diagnosa (nama, tanggal, hasil_penyakit, hasil_cf, rincian_json)
            VALUES (?, ?, ?, ?, ?)
        ''', (nama, tanggal_sekarang, PENYAKIT[penyakit_tertinggi]['nama'], cf_tertinggi, json.dumps(rincian_penuh)))
        
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        
        return redirect(url_for('result', result_id=last_id))
        
    return render_template('diagnose.html', gejala=GEJALA, pilihan=PILIHAN_USER)

@app.route('/result/<int:result_id>')
def result(result_id):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM diagnosa WHERE id = ?', (result_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        flash('Riwayat diagnosis tidak ditemukan.', 'danger')
        return redirect(url_for('index'))
        
    import json
    rincian_penuh = json.loads(row['rincian_json'])
    
    # Cari penyakit info
    penyakit_info = None
    for p_code, p_val in PENYAKIT.items():
        if p_val['nama'] == row['hasil_penyakit']:
            penyakit_info = p_val
            penyakit_info['kode'] = p_code
            break
            
    # Jika tidak ketemu (fallback)
    if not penyakit_info:
        penyakit_info = {
            'kode': 'MB1',
            'nama': row['hasil_penyakit'],
            'deskripsi': 'Gangguan mental terdeteksi.',
            'saran': 'Konsultasikan dengan ahli psikologis atau psikiater.'
        }
        
    return render_template(
        'result.html', 
        diagnosa=row, 
        penyakit_info=penyakit_info, 
        rincian=rincian_penuh,
        semua_penyakit=PENYAKIT
    )

@app.route('/history')
def history():
    data_history = database.get_history()
    return render_template('history.html', history=data_history)

@app.route('/delete-history/<int:result_id>', methods=['POST'])
def delete_history(result_id):
    database.delete_history_item(result_id)
    flash('Riwayat diagnosis berhasil dihapus.', 'success')
    return redirect(url_for('history'))

@app.route('/clear-history', methods=['POST'])
def clear_history():
    database.clear_all_history()
    flash('Semua riwayat diagnosis berhasil dibersihkan.', 'success')
    return redirect(url_for('history'))

@app.route('/rules')
def rules():
    return render_template('rules.html', gejala=GEJALA, penyakit=PENYAKIT, cf_expert=CF_EXPERT)

if __name__ == '__main__':
    app.run(debug=True)
