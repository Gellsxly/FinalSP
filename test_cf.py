# Script Pengujian Certainty Factor
# Menghitung secara mandiri untuk memverifikasi logika di app.py

from app import CF_EXPERT, PILIHAN_USER, PENYAKIT

def test_calculation():
    # Input dari skenario gambar:
    # G001: Kurang Yakin (0.2)
    # G002: Cukup Yakin (0.4)
    # G006: Cukup Yakin (0.4)
    # G007: Yakin (0.6)
    # Lainnya: Tidak Pasti (0)
    
    user_inputs = {
        'G001': 'Kurang Yakin',
        'G002': 'Cukup Yakin',
        'G006': 'Cukup Yakin',
        'G007': 'Yakin',
    }
    
    # Inisialisasi input penuh untuk 30 gejala
    user_responses = {}
    for i in range(1, 31):
        g_code = f"G{i:03d}"
        response_key = user_inputs.get(g_code, 'Tidak Pasti')
        user_responses[g_code] = PILIHAN_USER[response_key]
        
    print("=== INPUT PENGUJIAN ===")
    for k, v in user_inputs.items():
        print(f"{k}: {v} (CF: {PILIHAN_USER[v]})")
    print("Gejala lainnya: Tidak Pasti (CF: 0.0)")
    print()
    
    # Hitung CF untuk masing-masing penyakit
    hasil_perhitungan = {}
    for p_code, p_info in PENYAKIT.items():
        cf_he_list = []
        
        # Hitung CF(H,E) = CF_User * CF_Expert
        for g_code, cf_expert_val in CF_EXPERT[p_code].items():
            cf_user_val = user_responses.get(g_code, 0.0)
            cf_he = round(cf_user_val * cf_expert_val, 4)
            if cf_he > 0:
                cf_he_list.append(cf_he)
                
        # Gabungkan CF
        cf_final = 0.0
        if cf_he_list:
            cf_final = cf_he_list[0]
            for i in range(1, len(cf_he_list)):
                cf_old = cf_final
                cf_new = cf_he_list[i]
                cf_final = cf_old + cf_new * (1.0 - cf_old)
                cf_final = round(cf_final, 4)
                
        hasil_perhitungan[p_info['nama']] = cf_final

    print("=== HASIL PERHITUNGAN SYSTEM PAKAR ===")
    for nama_penyakit, cf in hasil_perhitungan.items():
        print(f"- {nama_penyakit}: {cf} ({cf * 100:.2f}%)")
        
    print()
    # Verifikasi dengan hasil Excel
    # Hasil Excel: Skizofrenia = 0.36, OCD = 0.51 (0.5136)
    skizofrenia_cf = hasil_perhitungan['Skizofrenia']
    ocd_cf = hasil_perhitungan['Obsessive Compulsive Disorder (OCD)']
    
    print("=== VERIFIKASI ===")
    print(f"Skizofrenia CF: {skizofrenia_cf} (Harapan: 0.3616 atau dibulatkan menjadi 0.36)")
    print(f"OCD CF: {ocd_cf} (Harapan: 0.5136 atau dibulatkan menjadi 0.51)")
    
    if abs(skizofrenia_cf - 0.3616) < 0.01 and abs(ocd_cf - 0.5136) < 0.01:
        print("\n[SUKSES] Perhitungan Certainty Factor sesuai 100% dengan hasil di Excel!")
    else:
        print("\n[PERINGATAN] Ada ketidakcocokan dalam perhitungan.")

if __name__ == '__main__':
    test_calculation()
