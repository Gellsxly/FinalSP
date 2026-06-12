import sqlite3
import json
from datetime import datetime

DB_NAME = 'diagnosa.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diagnosa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            tanggal TEXT NOT NULL,
            hasil_penyakit TEXT NOT NULL,
            hasil_cf REAL NOT NULL,
            rincian_json TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_diagnosa(nama, hasil_penyakit, hasil_cf, rincian_dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    tanggal_sekarang = datetime.now().strftime('%Y-%m-%d %H:%M')
    rincian_json = json.dumps(rincian_dict)
    
    cursor.execute('''
        INSERT INTO diagnosa (nama, tanggal, hasil_penyakit, hasil_cf, rincian_json)
        VALUES (?, ?, ?, ?, ?)
    ''', (nama, tanggal_sekarang, hasil_penyakit, hasil_cf, rincian_json))
    
    conn.commit()
    conn.close()

def get_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM diagnosa ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            'id': row['id'],
            'nama': row['nama'],
            'tanggal': row['tanggal'],
            'hasil_penyakit': row['hasil_penyakit'],
            'hasil_cf': row['hasil_cf'],
            'rincian': json.loads(row['rincian_json'])
        })
    return history

def delete_history_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM diagnosa WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()

def clear_all_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM diagnosa')
    conn.commit()
    conn.close()
