import streamlit as st
import json
import bcrypt
import os

USER_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_FILE):
        return []
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

# ===============================
# SIGNUP
# ===============================
def signup():

    st.subheader("📝 Create Account")

    name = st.text_input("Name", key="signup_name")
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")

    if st.button("Sign Up", key="signup_btn"):
        if not name or not email or not password:
            st.error("All fields required")
            return

        users = load_users()

        for u in users:
            if u["email"] == email:
                st.error("Email already exists")
                return

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        users.append({
            "name": name,
            "email": email,
            "password": hashed.decode()
        })

        save_users(users)
        st.success("Account created successfully")

# ===============================
# LOGIN
# ===============================
def login():

    st.subheader("🔐 Login")

    identifier = st.text_input(
        "Name or Email",
        key="login_identifier"
    )

    password = st.text_input(
        "Password",
        type="password",
        key="login_password"
    )

    if st.button("Login", key="login_btn"):

        users = load_users()
        found = False

        for u in users:
            if identifier in (u["name"], u["email"]):
                if bcrypt.checkpw(
                    password.encode(),
                    u["password"].encode()
                ):
                    st.session_state["login"] = True
                    st.session_state["user"] = u["name"]
                    st.success("Login successful")
                    found = True
                    st.rerun()

        if not found:
            st.error("Invalid credentials")