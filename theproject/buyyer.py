import streamlit as st
import pymysql
import bcrypt

# Database Connection
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="system",
        database="crop",
        cursorclass=pymysql.cursors.DictCursor
    )

# Check if username exists
def username_exists(username):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM buyers WHERE username = %s", (username,))
        user = cursor.fetchone()
    conn.close()
    return user is not None

# Register a new buyer
def register_buyer(name, username, email, password, crop_type):
    if username_exists(username):
        return False  # Username already exists

   # hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO buyers (name, username, email, password, crop_type) VALUES (%s, %s, %s, %s, %s)", 
            (name, username, email, password, crop_type)
        )
        conn.commit()
    conn.close()
    return True

# Authenticate user
def authenticate_user(username, password):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM buyers WHERE username=%s", (username,))
        user = cursor.fetchone()
    conn.close()
    
    if user and password:
        return user
    return None

# Delete a buyer by ID
def delete_buyer(buyer_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM buyers WHERE id = %s", (buyer_id,))
        conn.commit()
    conn.close()

# Streamlit UI
st.title("🔐 Buyer Management System")

# Sidebar Navigation (Login / Register / Buyer List)
menu = st.sidebar.radio("Navigation", ["Login", "Register", "Buyer List"])

# ✅ Registration Section
if menu == "Register":
    st.subheader("📝 Register as a Buyer")
    
    name = st.text_input("Full Name")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    # Crop Type Selection
    crop_type = st.selectbox("Select Crop Type", ["Wheat", "Rice", "Corn", "Soybean", "Cotton", "Other"])
    
    register_btn = st.button("Register")

    if register_btn:
        if password != confirm_password:
            st.error("Passwords do not match! ❌")
        elif username_exists(username):
            st.error("Username already taken! ❌")
        else:
            success = register_buyer(name, username, email, password, crop_type)
            if success:
                st.success("Registration successful! 🎉 You can now log in.")
            else:
                st.error("Registration failed! Try again.")

# ✅ Login Section
elif menu == "Login":
    st.subheader("🔑 Buyer Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.button("Login")

    if login_btn:
        user = authenticate_user(username, password)
        if user:
            st.session_state["buyer_logged_in"] = True
            st.session_state["buyer_name"] = user["name"]
            st.session_state["is_admin"] = (user["username"] == "admin")  # Admin check
            st.success(f"Welcome, {user['name']}! 🎉")
            st.rerun()
        else:
            st.error("Invalid credentials!")

# ✅ Display Buyer List with Delete Option (Only for Logged-in Users)
elif menu == "Buyer List":
    if not st.session_state.get("buyer_logged_in"):
        st.warning("You must be logged in to view and manage buyers.")
    else:
        st.subheader("📋 Registered Buyers")

        # Fetch buyers
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, email, crop_type FROM buyers")
            buyers = cursor.fetchall()
        conn.close()

        if buyers:
            for buyer in buyers:
                col1, col2, col3, col4, col5 = st.columns([2, 3, 3, 2, 2])
                col1.write(buyer["id"])
                col2.write(buyer["name"])
                col3.write(buyer["email"])
                col4.write(buyer["crop_type"])
                
                # Show delete button if logged-in user is "admin"
                if st.session_state.get("is_admin"):
                    if col5.button("🗑️ Delete", key=f"delete_{buyer['id']}"):
                        delete_buyer(buyer["id"])
                        st.experimental_rerun()

        else:
            st.warning("No buyers found.")

        # Logout Button
        if st.button("Logout"):
            st.session_state.clear()
            rerun()
