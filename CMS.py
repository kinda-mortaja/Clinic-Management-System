"""
Clinic Management System (No Frameworks)
Features:
- Login (Admin/Doctor/Receptionist)
- Register Patient
- Schedule Appointment with conflict checking
Database: SQLite
"""

import sqlite3
import hashlib
import getpass
from dataclasses import dataclass
from datetime import datetime


# =========================
# Database Layer
# =========================

class DBConnection:
    def __init__(self, db_path: str = "clinic.db"):
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn


class BaseRepository:
    def __init__(self, db: DBConnection):
        self.db = db

    def execute(self, sql: str, params: tuple = ()) -> None:
        with self.db.connect() as conn:
            conn.execute(sql, params)
            conn.commit()

    def fetchone(self, sql: str, params: tuple = ()):
        with self.db.connect() as conn:
            cur = conn.execute(sql, params)
            return cur.fetchone()

    def fetchall(self, sql: str, params: tuple = ()):
        with self.db.connect() as conn:
            cur = conn.execute(sql, params)
            return cur.fetchall()


class UserDB(BaseRepository):
    def create_table(self) -> None:
        self.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','doctor','receptionist'))
        );
        """)

    def create_user(self, username: str, password_hash: str, role: str) -> None:
        self.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?);",
            (username, password_hash, role)
        )

    def find_user(self, username: str):
        return self.fetchone(
            "SELECT id, username, password_hash, role FROM users WHERE username = ?;",
            (username,)
        )


class PatientDB(BaseRepository):
    def create_table(self) -> None:
        self.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL CHECK(age >= 0),
            gender TEXT NOT NULL CHECK(gender IN ('Male','Female')),
            phone TEXT,
            address TEXT
        );
        """)

    def save_patient(self, name: str, age: int, gender: str, phone: str, address: str) -> None:
        self.execute("""
        INSERT INTO patients (name, age, gender, phone, address)
        VALUES (?, ?, ?, ?, ?);
        """, (name, age, gender, phone, address))

    def get_patient_by_id(self, patient_id: int):
        return self.fetchone("""
        SELECT id, name, age, gender, phone, address
        FROM patients WHERE id = ?;
        """, (patient_id,))

    def list_patients(self):
        return self.fetchall("""
        SELECT id, name, age, gender FROM patients ORDER BY id DESC;
        """)


class DoctorDB(BaseRepository):
    def create_table(self) -> None:
        self.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty TEXT NOT NULL
        );
        """)

    def seed_default_doctors(self) -> None:
        # Insert some doctors if table is empty
        row = self.fetchone("SELECT COUNT(*) FROM doctors;")
        if row and row[0] == 0:
            doctors = [
                ("Dr. Ahmed", "General"),
                ("Dr. Sara", "Pediatrics"),
                ("Dr. Omar", "Dermatology"),
            ]
            with self.db.connect() as conn:
                conn.executemany("INSERT INTO doctors (name, specialty) VALUES (?, ?);", doctors)
                conn.commit()

    def list_doctors(self):
        return self.fetchall("SELECT id, name, specialty FROM doctors ORDER BY id;")

    def get_doctor_by_id(self, doctor_id: int):
        return self.fetchone("SELECT id, name, specialty FROM doctors WHERE id = ?;", (doctor_id,))


class AppointmentDB(BaseRepository):
    def create_table(self) -> None:
        self.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            appt_datetime TEXT NOT NULL,
            reason TEXT,
            status TEXT NOT NULL DEFAULT 'Scheduled',
            FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE,
            FOREIGN KEY(doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
        );
        """)

    def is_doctor_available(self, doctor_id: int, appt_datetime: str) -> bool:
        row = self.fetchone("""
        SELECT COUNT(*)
        FROM appointments
        WHERE doctor_id = ?
          AND appt_datetime = ?
          AND status = 'Scheduled';
        """, (doctor_id, appt_datetime))
        return (row[0] == 0) if row else True

    def save_appointment(self, patient_id: int, doctor_id: int, appt_datetime: str, reason: str) -> None:
        self.execute("""
        INSERT INTO appointments (patient_id, doctor_id, appt_datetime, reason)
        VALUES (?, ?, ?, ?);
        """, (patient_id, doctor_id, appt_datetime, reason))

    def list_appointments(self):
        return self.fetchall("""
        SELECT a.id, p.name, d.name, a.appt_datetime, a.status
        FROM appointments a
        JOIN patients p ON p.id = a.patient_id
        JOIN doctors d ON d.id = a.doctor_id
        ORDER BY a.appt_datetime DESC;
        """)


# =========================
# Entity Layer (Optional)
# =========================

@dataclass
class CurrentUser:
    user_id: int
    username: str
    role: str


# =========================
# Control Layer
# =========================

class AuthController:
    def __init__(self, user_db: UserDB):
        self.user_db = user_db

    @staticmethod
    def hash_password(password: str) -> str:
        # Simple SHA-256 hash (good for course project; real systems use salted hashing)
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def login(self, username: str, password: str) -> CurrentUser | None:
        user = self.user_db.find_user(username)
        if not user:
            return None

        user_id, uname, stored_hash, role = user
        if self.hash_password(password) != stored_hash:
            return None

        return CurrentUser(user_id=user_id, username=uname, role=role)


class PatientController:
    def __init__(self, patient_db: PatientDB):
        self.patient_db = patient_db

    def validate_patient_data(self, name: str, age: str, gender: str) -> tuple[bool, str]:
        if not name.strip():
            return False, "Name is required."
        if not age.isdigit():
            return False, "Age must be a number."
        age_int = int(age)
        if age_int < 0 or age_int > 120:
            return False, "Age must be between 0 and 120."
        if gender not in ("Male", "Female"):
            return False, "Gender must be Male or Female."
        return True, ""

    def register_patient(self, name: str, age: str, gender: str, phone: str, address: str) -> tuple[bool, str]:
        ok, msg = self.validate_patient_data(name, age, gender)
        if not ok:
            return False, msg
        self.patient_db.save_patient(name=name.strip(), age=int(age), gender=gender, phone=phone.strip(), address=address.strip())
        return True, "Patient registered successfully."


class AppointmentController:
    def __init__(self, appointment_db: AppointmentDB, patient_db: PatientDB, doctor_db: DoctorDB):
        self.appointment_db = appointment_db
        self.patient_db = patient_db
        self.doctor_db = doctor_db

    def validate_datetime(self, dt_str: str) -> tuple[bool, str]:
        try:
            # Expected format: YYYY-MM-DD HH:MM
            datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            return True, ""
        except ValueError:
            return False, "Invalid date/time format. Use: YYYY-MM-DD HH:MM"

    def schedule_appointment(self, patient_id: str, doctor_id: str, appt_datetime: str, reason: str) -> tuple[bool, str]:
        if not patient_id.isdigit():
            return False, "Patient ID must be a number."
        if not doctor_id.isdigit():
            return False, "Doctor ID must be a number."

        pid = int(patient_id)
        did = int(doctor_id)

        if not self.patient_db.get_patient_by_id(pid):
            return False, "Patient not found."
        if not self.doctor_db.get_doctor_by_id(did):
            return False, "Doctor not found."

        ok, msg = self.validate_datetime(appt_datetime)
        if not ok:
            return False, msg

        if not self.appointment_db.is_doctor_available(did, appt_datetime):
            return False, "This doctor is not available at the selected time."

        self.appointment_db.save_appointment(pid, did, appt_datetime, reason.strip())
        return True, "Appointment scheduled successfully."


# =========================
# UI Layer (Console UI)
# =========================

class LoginUI:
    def __init__(self, auth_controller: AuthController):
        self.auth = auth_controller

    def show(self) -> CurrentUser | None:
        print("\n=== Login ===")
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        user = self.auth.login(username, password)
        if not user:
            print("❌ Invalid username or password.")
            return None
        print(f"✅ Welcome {user.username} ({user.role})")
        return user


class ClinicMenuUI:
    def __init__(self, patient_controller: PatientController, appointment_controller: AppointmentController,
                 patient_db: PatientDB, doctor_db: DoctorDB, appointment_db: AppointmentDB):
        self.patient_controller = patient_controller
        self.appointment_controller = appointment_controller
        self.patient_db = patient_db
        self.doctor_db = doctor_db
        self.appointment_db = appointment_db

    def show_menu(self, current_user: CurrentUser) -> None:
        while True:
            print("\n=== Clinic Management System ===")
            print("1) Register Patient")
            print("2) Schedule Appointment")
            print("3) List Patients")
            print("4) List Doctors")
            print("5) List Appointments")
            print("0) Logout")

            choice = input("Choose: ").strip()

            if choice == "1":
                self.register_patient_flow(current_user)
            elif choice == "2":
                self.schedule_appointment_flow(current_user)
            elif choice == "3":
                self.list_patients_flow()
            elif choice == "4":
                self.list_doctors_flow()
            elif choice == "5":
                self.list_appointments_flow()
            elif choice == "0":
                print("✅ Logged out.")
                break
            else:
                print("❌ Invalid choice.")

    def register_patient_flow(self, current_user: CurrentUser) -> None:
        if current_user.role not in ("admin", "receptionist"):
            print("❌ Access denied. Only admin/receptionist can register patients.")
            return

        print("\n--- Register Patient ---")
        name = input("Name: ")
        age = input("Age: ")
        gender = input("Gender (Male/Female): ")
        phone = input("Phone (optional): ")
        address = input("Address (optional): ")

        ok, msg = self.patient_controller.register_patient(name, age, gender, phone, address)
        print(("✅ " if ok else "❌ ") + msg)

    def schedule_appointment_flow(self, current_user: CurrentUser) -> None:
        if current_user.role not in ("admin", "receptionist"):
            print("❌ Access denied. Only admin/receptionist can schedule appointments.")
            return

        print("\n--- Schedule Appointment ---")
        self.list_patients_flow()
        patient_id = input("Enter Patient ID: ")

        self.list_doctors_flow()
        doctor_id = input("Enter Doctor ID: ")

        appt_datetime = input("Appointment DateTime (YYYY-MM-DD HH:MM): ")
        reason = input("Reason (optional): ")

        ok, msg = self.appointment_controller.schedule_appointment(patient_id, doctor_id, appt_datetime, reason)
        print(("✅ " if ok else "❌ ") + msg)

    def list_patients_flow(self) -> None:
        print("\n--- Patients ---")
        rows = self.patient_db.list_patients()
        if not rows:
            print("(No patients)")
            return
        for pid, name, age, gender in rows:
            print(f"ID={pid} | {name} | {age} | {gender}")

    def list_doctors_flow(self) -> None:
        print("\n--- Doctors ---")
        rows = self.doctor_db.list_doctors()
        for did, name, specialty in rows:
            print(f"ID={did} | {name} | {specialty}")

    def list_appointments_flow(self) -> None:
        print("\n--- Appointments ---")
        rows = self.appointment_db.list_appointments()
        if not rows:
            print("(No appointments)")
            return
        for aid, patient_name, doctor_name, appt_dt, status in rows:
            print(f"ID={aid} | Patient={patient_name} | Doctor={doctor_name} | {appt_dt} | {status}")


# =========================
# Setup / Main
# =========================

def setup_database(db: DBConnection) -> tuple[UserDB, PatientDB, DoctorDB, AppointmentDB]:
    user_db = UserDB(db)
    patient_db = PatientDB(db)
    doctor_db = DoctorDB(db)
    appointment_db = AppointmentDB(db)

    user_db.create_table()
    patient_db.create_table()
    doctor_db.create_table()
    appointment_db.create_table()

    doctor_db.seed_default_doctors()

    # Create default accounts if not exist
    auth = AuthController(user_db)
    defaults = [
        ("admin", "admin123", "admin"),
        ("reception", "recep123", "receptionist"),
        ("doctor", "doc123", "doctor"),
    ]
    for u, p, r in defaults:
        try:
            user_db.create_user(u, auth.hash_password(p), r)
        except sqlite3.IntegrityError:
            pass  # already exists

    return user_db, patient_db, doctor_db, appointment_db


def main():
    db = DBConnection("clinic.db")
    user_db, patient_db, doctor_db, appointment_db = setup_database(db)

    auth_controller = AuthController(user_db)
    patient_controller = PatientController(patient_db)
    appointment_controller = AppointmentController(appointment_db, patient_db, doctor_db)

    login_ui = LoginUI(auth_controller)
    menu_ui = ClinicMenuUI(patient_controller, appointment_controller, patient_db, doctor_db, appointment_db)

    print("=== Clinic Management System (Console) ===")
    print("Default accounts:")
    print("  admin / admin123")
    print("  reception / recep123")
    print("  doctor / doc123")

    while True:
        user = login_ui.show()
        if user:
            menu_ui.show_menu(user)

        again = input("\nLogin again? (y/n): ").strip().lower()
        if again != "y":
            print("Bye!")
            break


if __name__ == "__main__":
    main()
