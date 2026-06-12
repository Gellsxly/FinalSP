import pymysql
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = 'finalsp_db'

def get_mysql_server_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        cursorclass=pymysql.cursors.DictCursor
    )

def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    # Connect directly to MySQL server to create the schema if not exists
    conn = get_mysql_server_connection()
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    conn.commit()
    conn.close()
    
    # Connect to database to initialize tables
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Table users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(150) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NULL,
            google_id VARCHAR(255) NULL,
            nama VARCHAR(100) NOT NULL,
            role VARCHAR(20) DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Table diagnosa (associated with user_id)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diagnosa (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NULL,
            nama VARCHAR(100) NOT NULL,
            tanggal VARCHAR(50) NOT NULL,
            hasil_penyakit VARCHAR(100) NOT NULL,
            hasil_cf DOUBLE NOT NULL,
            rincian_json LONGTEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    ''')
    
    # Check if an default admin user exists, if not create one
    cursor.execute("SELECT * FROM users WHERE email = 'admin@mindcare.com'")
    if not cursor.fetchone():
        hashed_pw = generate_password_hash('admin123')
        cursor.execute(
            "INSERT INTO users (email, password_hash, nama, role) VALUES (%s, %s, %s, %s)",
            ('admin@mindcare.com', hashed_pw, 'Administrator MindCare', 'admin')
        )
        
    conn.commit()
    conn.close()

# --- Authentication Helpers ---

def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_google_id(google_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE google_id = %s", (google_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(email, password, nama, role='user'):
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    try:
        cursor.execute(
            "INSERT INTO users (email, password_hash, nama, role) VALUES (%s, %s, %s, %s)",
            (email, password_hash, nama, role)
        )
        conn.commit()
        success = True
    except Exception as e:
        print("Error creating user:", e)
        success = False
    finally:
        conn.close()
    return success

def create_or_get_google_user(email, google_id, nama):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Check if user exists by google_id or email
    cursor.execute("SELECT * FROM users WHERE google_id = %s OR email = %s", (google_id, email))
    user = cursor.fetchone()
    
    if user:
        # If user exists but google_id wasn't set, update it
        if not user['google_id']:
            cursor.execute("UPDATE users SET google_id = %s WHERE id = %s", (google_id, user['id']))
            conn.commit()
            user['google_id'] = google_id
        conn.close()
        return user
    
    # Create new Google user
    try:
        cursor.execute(
            "INSERT INTO users (email, google_id, nama, role) VALUES (%s, %s, %s, 'user')",
            (email, google_id, nama)
        )
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE id = %s", (cursor.lastrowid,))
        new_user = cursor.fetchone()
    except Exception as e:
        print("Error creating Google user:", e)
        new_user = None
    finally:
        conn.close()
    return new_user

# --- Diagnostics Helpers ---

def save_diagnosa(user_id, nama, hasil_penyakit, hasil_cf, rincian_dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    tanggal_sekarang = datetime.now().strftime('%Y-%m-%d %H:%M')
    rincian_json = json.dumps(rincian_dict)
    
    cursor.execute('''
        INSERT INTO diagnosa (user_id, nama, tanggal, hasil_penyakit, hasil_cf, rincian_json)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (user_id, nama, tanggal_sekarang, hasil_penyakit, hasil_cf, rincian_json))
    
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_id

def get_history_by_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM diagnosa WHERE user_id = %s ORDER BY id DESC', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            'id': row['id'],
            'user_id': row['user_id'],
            'nama': row['nama'],
            'tanggal': row['tanggal'],
            'hasil_penyakit': row['hasil_penyakit'],
            'hasil_cf': row['hasil_cf'],
            'rincian': json.loads(row['rincian_json'])
        })
    return history

def delete_history_item(item_id, user_id=None, is_admin=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    if is_admin:
        cursor.execute('DELETE FROM diagnosa WHERE id = %s', (item_id,))
    else:
        cursor.execute('DELETE FROM diagnosa WHERE id = %s AND user_id = %s', (item_id, user_id))
    conn.commit()
    conn.close()

def clear_all_history(user_id=None, is_admin=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    if is_admin:
        cursor.execute('DELETE FROM diagnosa')
    else:
        cursor.execute('DELETE FROM diagnosa WHERE user_id = %s', (user_id,))
    conn.commit()
    conn.close()

# --- Admin Dashboard Stats & Operations ---

def get_admin_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Total Users
    cursor.execute("SELECT COUNT(*) as total FROM users WHERE role = 'user'")
    total_users = cursor.fetchone()['total']
    
    # 2. Total Diagnoses
    cursor.execute("SELECT COUNT(*) as total FROM diagnosa")
    total_diagnoses = cursor.fetchone()['total']
    
    # 3. Diagnostics count grouped by disease
    cursor.execute("SELECT hasil_penyakit, COUNT(*) as count, AVG(hasil_cf) as avg_cf FROM diagnosa GROUP BY hasil_penyakit ORDER BY count DESC")
    diagnose_stats = cursor.fetchall()
    
    conn.close()
    return {
        'total_users': total_users,
        'total_diagnoses': total_diagnoses,
        'diagnose_stats': diagnose_stats
    }

def get_all_users_with_diagnose_count():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.id, u.email, u.nama, u.role, u.created_at, COUNT(d.id) as total_diagnosa
        FROM users u
        LEFT JOIN diagnosa d ON u.id = d.user_id
        GROUP BY u.id
        ORDER BY u.created_at DESC
    ''')
    users = cursor.fetchall()
    conn.close()
    return users

def get_all_diagnoses_with_user():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.id, d.nama as nama_pasien, d.tanggal, d.hasil_penyakit, d.hasil_cf, u.email as user_email
        FROM diagnosa d
        LEFT JOIN users u ON d.user_id = u.id
        ORDER BY d.id DESC
    ''')
    diagnoses = cursor.fetchall()
    conn.close()
    return diagnoses
