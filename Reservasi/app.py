import streamlit as st
import sqlite3
from datetime import datetime, date, time

# ------------------ DB SETUP ------------------ #
def get_conn():
    conn = sqlite3.connect("booking.db", check_same_thread=False)
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # tabel user sederhana (username, password plaintext, role)
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """)

    # tabel reservasi
    c.execute("""
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        computer_name TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING'
    )
    """)

    # buat user default kalau belum ada
    # admin: admin / admin
    # user: user / user
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    if count == 0:
        c.execute("INSERT INTO users (username, password, role) VALUES ('rana', 'rana', 'admin')")
        c.execute("INSERT INTO users (username, password, role) VALUES ('bintang', 'bintang', 'admin')")
        # c.execute("INSERT INTO users (username, password, role) VALUES ('user', 'user', 'user')")
        conn.commit()

    conn.close()

def check_login(username, password):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT role FROM users WHERE username=? AND password=?",
        (username, password),
    )
    row = c.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def create_reservation(username, computer_name, start_date, end_date, start_time, end_time):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO reservations (username, computer_name, start_date, end_date, start_time, end_time, status)
        VALUES (?, ?, ?, ?, ?, ?, 'PENDING')
    """, (username, computer_name, start_date, end_date, start_time, end_time))
    conn.commit()
    conn.close()


def get_user_reservations(username):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, computer_name, start_date, end_date, start_time, end_time, status
        FROM reservations
        WHERE username=?
        ORDER BY start_date
    """, (username,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_all_reservations(status_filter=None):
    conn = get_conn()
    c = conn.cursor()
    if status_filter and status_filter != "ALL":
        c.execute("""
            SELECT id, username, computer_name, start_date, end_date, start_time, end_time, status
            FROM reservations
            WHERE status=?
            ORDER BY start_date
        """, (status_filter,))
    else:
        c.execute("""
            SELECT id, username, computer_name, start_date, end_date, start_time, end_time, status
            FROM reservations
            ORDER BY start_date
        """)
    rows = c.fetchall()
    conn.close()
    return rows

def get_available_computers(current_date, current_time):
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        SELECT computer_name FROM reservations
        WHERE status='APPROVED'
        AND date(?) BETWEEN date(start_date) AND date(end_date)
    """, (current_date))

    booked_computers = [row[0] for row in c.fetchall()]
    conn.close()

    all_computers = ["S2IF-1", "S2IF-2", "S2IF-5", "S2IF-6", "S2IF-7", "S2IF-8", "S2IF-9"]
    available = [pc for pc in all_computers if pc not in booked_computers]
    return available

# Tambahkan data spesifikasi komputer
COMPUTER_SPECS = {
    "S2IF-1": "Quadro RTX 6000| 12th Gen Intel(R) Core(TM) i9-12900 3.20 GHz | RAM 32GB",
    "S2IF-2": "RTX 3070 | Intel(R) Core(TM) i7-3770 CPU @ 3.40 GHz | RAM 8GB",
    "S2IF-5": "NVIDIA GeForce GT 430 | Intel(R) Core(TM) i7-3770 CPU @ 3.40 GHz | RAM 8GB",
    "S2IF-6": "NVIDIA GeForce GT 430 | Intel(R) Core(TM) i7-3770 CPU @ 3.40 GHz | RAM 8GB",
    "S2IF-7": "Intel® UHD Graphics 770 | 12th Gen Intel(R) Core(TM) i5-12500 3.00 GHz | RAM 16GB",
    "S2IF-8": "Intel® UHD Graphics 770 | 12th Gen Intel(R) Core(TM) i5-12500 3.00 GHz | RAM 16GB",
    "S2IF-9": "Intel® UHD Graphics 770 | 12th Gen Intel(R) Core(TM) i5-12500 3.00 GHz | RAM 16GB"
}

def add_user(username, password, role="user"):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  (username, password, role))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def delete_user(username):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        return True
    except:
        return False


def get_all_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT username, password, role FROM users")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_reservation(res_id):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM reservations WHERE id=?", (res_id,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def update_reservation_status(res_id, new_status):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE reservations SET status=? WHERE id=?", (new_status, res_id))
    conn.commit()
    conn.close()



# ------------------ UI ------------------ #
init_db()
st.set_page_config(page_title="Reservasi Komputer", layout="wide")
# Custom CSS styling
st.markdown("""
    <style>
    .main {
        background-color: #F7F9FC;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .reservation-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        border-left: 5px solid #4C8BF5;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
    }
    .status-approved {
        color: #0FA958;
        font-weight: bold;
    }
    .status-pending {
        color: #E5B300;
        font-weight: bold;
    }
    .status-rejected {
        color: #D33A2C;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("APLIKASI RESERVASI KOMPUTER RESIDENSI S2 INFORMATIKA TELU")

st.markdown("---")


st.subheader("Status Ketersediaan Komputer Yang Tersedia")

# now = datetime.now()
# current_date = now.date().isoformat()
# current_time = now.strftime("%H:%M")

# available = get_available_computers(current_date, current_time)


# if available:
#     st.success("💻 Tersedia: " + ", ".join(available))
# else:
#     st.error("🚫 Tidak ada komputer yang tersedia saat ini.")

# now = datetime.now()
# current_date = now.date().isoformat()
# current_time = now.strftime("%H:%M")

# available = get_available_computers(current_date, current_time)

now = datetime.now()
current_date = now.date().isoformat()

available = get_available_computers(current_date)

status_data = []
for pc, spec in COMPUTER_SPECS.items():
    status = "AVAILABLE" if pc in available else "NOT AVAILABLE"
    status_style = (
        "<span style='color:#0FA958;font-weight:bold;'>AVAILABLE</span>"
        if status == "AVAILABLE" else
        "<span style='color:#D33A2C;font-weight:bold;'>NOT AVAILABLE</span>"
    )
    status_data.append([pc, status_style, spec])

st.markdown("""
<table>
    <tr>
        <th>Komputer</th>
        <th>Status</th>
        <th>Spesifikasi</th>
    </tr>
""" + "".join([
    f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>"
    for row in status_data
]) + "</table>", unsafe_allow_html=True)


st.markdown("---")


# Session state login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None

# ------------------ LOGIN FORM ------------------ #
if not st.session_state.logged_in:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        role = check_login(username, password)
        if role:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = role
            st.success(f"Login berhasil sebagai {role}")
        else:
            st.error("Username / password salah")
    st.info("User default: Login User Baru Silahkan Menghubungi Mbak Rana (Adm Prodi S2IF) untuk Regristasi Akun")
else:
    st.sidebar.write(f"Login sebagai: **{st.session_state.username} ({st.session_state.role})**")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()


st.markdown("---")


# ------------------ HALAMAN USER ------------------ #
if st.session_state.logged_in and st.session_state.role == "user":

    st.header("Menu User - Reservasi Rentang Tanggal + Jam")

    col1, col2 = st.columns(2)
    with col1:
        computer_name = st.selectbox(
            "Pilih Komputer",
            ["S2IF-1", "S2IF-2", "S2IF-5", "S2IF-6", "S2IF-7", "S2IF-8", "S2IF-9"]
        )
        tanggal_range = st.date_input(
            "Pilih rentang tanggal (mulai - selesai)",
            value=(date.today(), date.today())
        )
    with col2:
        jam_mulai = st.time_input("Jam mulai", value=time(0, 0))
        jam_selesai = st.time_input("Jam selesai", value=time(23, 59))

    # Pastikan harus ada 2 tanggal (start & end)
    if isinstance(tanggal_range, (list, tuple)) and len(tanggal_range) == 2:
        start_date, end_date = tanggal_range
    else:
        st.warning("⚠ Pilih rentang tanggal (mulai & selesai)!")
        st.stop()

    if st.button("Ajukan Reservasi"):
        if end_date < start_date:
            st.error("Tanggal selesai harus setelah atau sama dengan tanggal mulai.")
        elif end_date == start_date and jam_selesai <= jam_mulai:
            st.error("Untuk tanggal yang sama, jam selesai harus setelah jam mulai.")
        else:
            create_reservation(
                st.session_state.username,
                computer_name,
                start_date.isoformat(),
                end_date.isoformat(),
                jam_mulai.strftime("%H:%M"),
                jam_selesai.strftime("%H:%M"),
            )
            st.success("Reservasi diajukan. Menunggu persetujuan admin.")

    # ---- TAMPILKAN RESERVASI KOMPUTER ---- #
    st.subheader(f"Reservasi yang sudah ada untuk {computer_name} 💻")

    all_rows = get_all_reservations()
    comp_rows = [r for r in all_rows if r[2] == computer_name]

    if comp_rows:
        for r in comp_rows:
            rid, uname, comp, sdate, edate, stime, etime, status = r
            status_label = "🟢 Approved" if status=="APPROVED" else ("🟡 Pending" if status=="PENDING" else "🔴 Rejected")

            st.markdown(f"""
            <div class="reservation-card">
                <strong>Reservasi #{rid}</strong><br>
                📌 User: {uname} <br>
                🖥 Komputer: {comp}<br>
                📅 {sdate} → {edate}<br>
                ⏱ {stime} - {etime} <br><br>
                {status_label}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Belum ada reservasi untuk komputer ini.")

    # # ---- RESERVASI SAYA ---- #
    # st.subheader("Reservasi saya")
    # rows = get_user_reservations(st.session_state.username)
    # if rows:
    #     for r in rows:
    #         rid, comp, sdate, edate, stime, etime, status = r
    #         st.write(f"ID: {rid} | {sdate} → {edate} | {stime}-{etime} | PC: {comp} | {status}")
    # else:
    #     st.write("Belum ada reservasi.")

    # ---- RESERVASI SAYA ---- #
    st.subheader("Reservasi Saya")

    rows = get_user_reservations(st.session_state.username)
    if rows:
        # Konversi data ke format tabel
        data = [
            {
                "ID": rid,
                "PC": comp,
                "Tanggal Mulai": sdate,
                "Tanggal Selesai": edate,
                "Jam Mulai": stime,
                "Jam Selesai": etime,
                "Status": status
            }
            for rid, comp, sdate, edate, stime, etime, status in rows
        ]
        
        st.dataframe(data, use_container_width=True)
    else:
        st.info("Belum ada reservasi.")

    st.markdown("---")



# ------------------ HALAMAN ADMIN ------------------ #
if st.session_state.logged_in and st.session_state.role == "admin":

    st.header("Menu Admin - Approve Reservasi")

    status_filter = st.selectbox("Filter status", ["ALL", "PENDING", "APPROVED", "REJECTED"])
    rows = get_all_reservations(status_filter)

    if not rows:
        st.info("Belum ada data reservasi.")
    else:
        # Konversi ke format tabel dict list
        data = []
        for r in rows:
            rid, uname, comp, sdate, edate, stime, etime, status = r
            data.append({
                "ID": rid,
                "User": uname,
                "Komputer": comp,
                "Tanggal Mulai": sdate,
                "Tanggal Selesai": edate,
                "Jam Mulai": stime,
                "Jam Selesai": etime,
                "Status": status
            })

        import pandas as pd
        df = pd.DataFrame(data)

        st.dataframe(df, use_container_width=True)

        st.markdown("### Aksi Reservasi")

        for r in rows:
            rid, uname, comp, sdate, edate, stime, etime, status = r
            col1, col2, col3, col4, col5 = st.columns([1.2, 2, 2, 2, 2])
        
            with col1:
                st.write(f"ID: {rid}")
            with col2:
                st.write(f"{uname} - {comp}")
            with col3:
                st.write(f"{status}")
            
            # Tombol APPROVE
            with col4:
                if status != "APPROVED":
                    if st.button("✔ APPROVE", key=f"approve_{rid}"):
                        update_reservation_status(rid, "APPROVED")
                        st.success("Reservasi di-approve.")
                        st.rerun()
        
                if status != "REJECTED":
                    if st.button("✖ REJECT", key=f"reject_{rid}"):
                        update_reservation_status(rid, "REJECTED")
                        st.warning("Reservasi di-reject.")
                        st.rerun()

            # Tombol DELETE
            with col5:
                if st.button("🗑 DELETE", key=f"delete_{rid}"):
                    if delete_reservation(rid):
                        st.success("Reservasi dihapus!")
                        st.rerun()
                    else:
                        st.error("Gagal menghapus!")


    st.markdown("---")

    st.subheader("Kelola Pengguna")

    # Form Tambah User
    new_user = st.text_input("Username mahasiswa baru")
    new_pass = st.text_input("Password mahasiswa baru", type="password")

    if st.button("Tambah User"):
        if new_user and new_pass:
            if add_user(new_user, new_pass):
                st.success("User berhasil ditambahkan!")
            else:
                st.error("Gagal! Username mungkin sudah terdaftar.")
        else:
            st.warning("Lengkapi username dan password!")

    st.info("Username = NIM Mahasiswa, Password = NAMA Mahasiswa")

    st.markdown("---")

    # List User
    st.markdown("### Daftar User")
    users = get_all_users()

    # Ubah hasil fetchall menjadi DataFrame agar kolom muncul
    import pandas as pd
    df_users = pd.DataFrame(users, columns=["Username", "Password", "Role"])

    st.dataframe(df_users, use_container_width=True)

    st.markdown("---")
    
    st.markdown("### Hapus User")

    for user in users:
        uname, password, role = user

        if role == "admin":
            continue

        col1, col2 = st.columns([3, 1])

        with col1:
            st.write(f"{uname} - {role}")

        with col2:
            if st.button("🗑 Hapus", key=f"del_{uname}"):
                if delete_user(uname):
                    st.success(f"User {uname} berhasil dihapus!")
                    st.rerun()
                else:
                    st.error("Gagal menghapus user!")


    st.markdown("---")












