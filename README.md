# 🏥 Clinic Management System

## 📌 Project Overview
The **Clinic Management System** is a software application designed to manage the daily operations of a medical clinic.  
The system allows clinic staff to authenticate users, register patients, and schedule appointments in an organized and secure way.

This project was developed as part of the **Software Engineering (CSCI 2313)** and **Web & Multimedia Engineering (WDMM 3314)** courses.  
It follows the **Boundary–Control–Entity (BCE)** architecture and uses **UML diagrams** for system analysis and design.

---

## 🎯 Project Objectives
- Provide a secure login system for clinic users  
- Allow registering new patients  
- Allow scheduling appointments with doctors  
- Prevent appointment conflicts  
- Store and retrieve data using a database  

---

## 🛠 Technologies Used
- **Python 3**  
- **SQLite**  
- **Visual Paradigm** (for UML modeling)  
- **GitHub**  

---

## ⚙ System Features
- User login (Admin, Receptionist, Doctor)  
- Patient registration  
- Appointment scheduling  
- Appointment conflict checking  
- View patients, doctors, and appointments  

---

## ▶ How to Run the System

### 1️⃣ Install Python
Make sure Python 3 is installed on your computer.  
Check by running:
```bash
python --version
```

### 2️⃣ Download the Project
Clone or download this repository from GitHub.

### 3️⃣ Open Terminal
Navigate to the project folder where `CMS.py` is located:
```bash
cd path_to_project_folder
```

### 4️⃣ Run the Program
```bash
python CMS.py
```

---

## 🔐 Default Login Accounts

| Role | Username | Password |
|------|--------|----------|
| Admin | admin | admin123 |
| Receptionist | reception | recep123 |
| Doctor | doctor | doc123 |

---

## 📘 How to Use the System

1. Run the program and log in using one of the accounts.  
2. After login, the main menu will appear.  
3. Use the menu options to:
   - Register new patients  
   - Schedule appointments  
   - View patients, doctors, and appointments  
4. Only **Admin** and **Receptionist** users can register patients and schedule appointments.  
5. Enter **0** to log out.

---

## 📂 Project Structure

| File | Description |
|------|------------|
| `CMS.py` | Main application file |
| `clinic.db` | SQLite database (created automatically) |
| `README.md` | Project documentation |

---

## 🧪 Testing
The system was tested using:
- Valid and invalid login attempts  
- Patient registration  
- Appointment scheduling with available and unavailable time slots  

All tests passed successfully.

---

## 👨‍🎓 Course Information
- **Course:** Software Engineering (CSCI 2313)  
- **Course:** Web & Multimedia Engineering (WDMM 3314)  
- **Instructor:** Dr. Abdelkareem Alashqar  
- **Semester:** 1st Semester 2025/2026  
