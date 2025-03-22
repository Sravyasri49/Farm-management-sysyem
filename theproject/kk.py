import streamlit as st
import pymysql
import hashlib
import pandas as pd
import joblib
import numpy as np
import warnings
from streamlit_option_menu import option_menu
from googletrans import Translator
from deep_translator import GoogleTranslator
import matplotlib.pyplot as plt
import seaborn as sns
import google.generativeai as genai

import base64

warnings.filterwarnings("ignore")
st.set_page_config(page_title=" System", layout="wide")

# Database Connection
conn = pymysql.connect(host="localhost", user="root", password="system", database="crop")
cursor = conn.cursor()


# Language selection options
language_options = {
    "English": "en",
    "हिन्दी (Hindi)": "hi",
    "తెలుగు (Telugu)": "te",
    "मराठी (Marathi)": "mr",
    "தமிழ் (Tamil)": "ta",
}
selected_language = st.sidebar.selectbox("🌍 Select Language", list(language_options.keys()))


# Function to translate text dynamically
def translate_text(text):
    if selected_language == "English":  # No need to translate English
        return text
    try:
        translated = GoogleTranslator(source="auto", target=language_options[selected_language]).translate(text)
        return translated
    except:
        return text  # Fallback in case of API failure

# User Authentication
def authenticate_user(username, password):
    cursor.execute("SELECT username, acres, phone FROM users WHERE username=%s AND password=%s", (username, password))
    return cursor.fetchone()

def register_user(username, password, acres, phone):
    try:
        cursor.execute("INSERT INTO users (username, password, acres, phone) VALUES (%s, %s, %s, %s)",
                       (username, password, acres, phone))
        conn.commit()
        return True
    except pymysql.err.IntegrityError:
        return False

def reset_password(username, phone, new_password):
    cursor.execute("SELECT * FROM users WHERE username=%s AND phone=%s", (username, phone))
    if cursor.fetchone():
        cursor.execute("UPDATE users SET password=%s WHERE username=%s", (new_password, username))
        conn.commit()
        return True
    return False

# Streamlit UI
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user_info"] = None  # Store user details

if not st.session_state["authenticated"]:
    menu = option_menu(
            menu_title=None,
            options=[translate_text("Login"), translate_text("Register"), translate_text("Forgot Password")],
            icons=["box-arrow-in-right", "person-plus", "key"],
            menu_icon="list", 
            default_index=0
        )
    
    if menu == translate_text("Login"):
        st.title(translate_text("Login"))
        username = st.text_input(translate_text("Username"))
        password = st.text_input(translate_text("Password"), type="password")
        
        if st.button(translate_text("Login")):
            user = authenticate_user(username, password)
            if user:
                st.session_state["authenticated"] = True
                st.session_state["user_info"] = {"username": user[0], "acres": user[1], "phone": user[2]}
                st.rerun()
            else:
                st.error(translate_text("Invalid username or password"))

    elif menu == translate_text("Register"):
        st.title(translate_text("Register"))
        new_username = st.text_input(translate_text("Username"))
        new_password = st.text_input(translate_text("Password"), type="password")
        acres = st.number_input(translate_text("How many acres do you own?"), min_value=1)
        phone = st.text_input(translate_text("Phone Number"))
        
        if st.button(translate_text("Register")):
            if register_user(new_username,new_password, acres, phone):
                st.success(translate_text("Registration successful! Please login."))
            else:
                st.error(translate_text("Username already exists."))
    
    elif menu == translate_text("Forgot Password"):
        st.title(translate_text("Reset Password"))
        reset_username = st.text_input(translate_text("Enter your Username"))
        reset_phone = st.text_input(translate_text("Enter your Phone Number"))
        new_password = st.text_input(translate_text("Enter New Password"), type="password")
        
        if st.button(translate_text("Reset Password")):
            if reset_password(reset_username, reset_phone, new_password):
                st.success(translate_text("Password reset successful! You can now login."))
            else:
                st.error(translate_text("Invalid username or phone number."))

else:
    user_info = st.session_state["user_info"]
    st.sidebar.success(f"👤 {translate_text('Logged in as')} **{user_info['username']}**")
    st.sidebar.info(f"🌾 {translate_text('Acres Owned')}: **{user_info['acres']}**")
    st.sidebar.info(f"📞 {translate_text('Contact')}: **{user_info['phone']}**")
    if st.button(translate_text("Logout")):
        st.session_state["authenticated"] = False
        st.session_state["user_info"] = None
        st.rerun()


        
    # Load models and encoders for market prediction
    price_model = joblib.load("model_price.pkl")
    location_model = joblib.load("model_location.pkl")
    industry_model = joblib.load("encoder_crop.pkl")

    # Load encoders for crop, season, district, etc.
    le_crop = joblib.load("le_crop.pkl")
    le_district = joblib.load("encoder_district.pkl")
    le_season = joblib.load("encoder_season.pkl")
    le_location = joblib.load("encoder_location.pkl")
    le_industry = joblib.load("le_industry.pkl")

    # Crop details for display
    crop_details = {
        "Lentil": {"desc": translate_text("Lentil is a cool-season crop that prefers well-drained soil."), "img": "images/lentil.jpg"},
        "Bajra": {"desc": translate_text("Bajra (Pearl Millet) is a drought-resistant crop grown in dry regions."), "img": "images\\Bajra.jpg"},
        "Barley": {"desc": translate_text("Barley is a versatile crop used for food, beer production, and fodder."), "img": "images/Barley.webp"},
        "Chickpea": {"desc": translate_text("Chickpea is a protein-rich legume commonly grown in arid regions."), "img": "images/Chickpea.jpg"},
        "Coconut": {"desc": translate_text("Coconut is a tropical tree crop used for oil, water, and fiber."), "img": "images/Coconut.png"},
        "Coffee": {"desc": translate_text("Coffee is a globally consumed beverage crop grown in hilly areas."), "img": "images/Coffee.jpg"},
        "Cotton": {"desc": translate_text("Cotton is a fiber crop used in textiles and garment production."), "img": "images/Cotton.jpg"},
        "Fruits": {"desc": translate_text("Fruits provide essential vitamins and are grown in different climates."), "img": "images/Fruits.webp"},
        "Groundnut": {"desc": translate_text("Groundnut (Peanut) is an oilseed crop rich in protein and fat."), "img": "images/Groundnut.webp"},
        "Jowar": {"desc": translate_text("Jowar (Sorghum) is a drought-tolerant cereal crop."), "img": "images/Jowar.webp"},
        "Jute": {"desc": translate_text("Jute is a fiber crop used for making ropes, mats, and bags."), "img": "images/Jute.jpg"},
        "Maize": {"desc": translate_text("Maize (Corn) is a staple cereal crop grown worldwide."), "img": "images/Maize.jpeg"},
        "Millets": {"desc": translate_text("Millets are small-seeded cereals known for their nutritional benefits."), "img": "images/Millets.webp"},
        "Mustard": {"desc": translate_text("Mustard is an oilseed crop used for cooking oil and condiments."), "img": "images/Mustard.png"},
        "Peas": {"desc": translate_text("Peas are nutritious legumes grown in cool weather."), "img": "images/Peas.jpg"},
        "Pulses": {"desc": translate_text("Pulses are edible seeds of leguminous plants, rich in protein."), "img": "images/Pulses.webp"},
        "Rice": {"desc": translate_text("Rice is a staple food crop requiring high water availability."), "img": "images/Rice.jpg"},
        "Soybean": {"desc": translate_text("Soybean is an oilseed crop used in food and industrial applications."), "img": "images/Soybean.jpg"},
        "Sugarcane": {"desc": translate_text("Sugarcane is a tropical grass used for sugar and ethanol production."), "img": "images/Sugarcane.jpg"},
        "Sunflower": {"desc": translate_text("Sunflower is an oilseed crop known for its edible oil."), "img": "images/Sunflower.jpg"},
        "Tea": {"desc": translate_text("Tea is a popular beverage crop grown in hilly regions."), "img": "images/Tea.jpg"},
        "Tobacco": {"desc": translate_text("Tobacco is a commercial crop used for cigarettes and chewing products."), "img": "images/Tobacco.jpg"},
        "Vegetables": {"desc": translate_text("Vegetables are rich in vitamins and minerals, essential for health."), "img": "images/Vegetables.webp"},
        "Wheat": {"desc": translate_text("Wheat is a major staple crop used for making flour and bread."), "img": "images/Wheat.jpg"}
    }

    # Streamlit app title with sidebar for navigation
    with st.sidebar:
        selected = option_menu(
            menu_title=translate_text("Features"),  
            options=["main", "🌾 " + translate_text("Crop Recommendation System"), "🌱 " + translate_text("Fertilizer Recommendation System"), "📊 " + translate_text("Telangana Crop Market Predictor"), "📈 " + translate_text("Market Visualization"), "💬Chatbot"],  
            icons=["menu-app", "seedling", "leaf", "tag", "graph-up", "chat-fill"],  
            menu_icon="list",  
            default_index=0  
        )
        



    if selected == "📊 " + translate_text("Telangana Crop Market Predictor"):
        st.title("📊 " + translate_text("Telangana Crop Market Predictor"))
        st.write(translate_text("Select a crop and season to predict the market price, best selling location, and the nearest industry."))
        
                # Input fields for crop and season selection
        crop = st.selectbox(translate_text("Select Crop"), le_crop.classes_)
        season = st.selectbox(translate_text("Select Season"), le_season.classes_)
        district = st.selectbox(translate_text("Select District"), le_district.classes_)
        year = st.selectbox(translate_text("Select Year"), list(range(2020, 2026)))

        # Encode inputs for market prediction
        crop_encoded = le_crop.transform([crop])[0]
        season_encoded = le_season.transform([season])[0]
        district_encoded = le_district.transform([district])[0]

        # Prediction button for crop market details
        if st.button(translate_text("Predict Crop Market Details")):
            try:
                # Prepare input data for market prediction
                input_features = np.array([[crop_encoded, district_encoded, year, season_encoded]])

                # Predict market details
                predicted_price = price_model.predict(input_features)[0]
                predicted_location_enc = location_model.predict(input_features)[0]
                predicted_industry_enc = industry_model.predict(input_features)[0]

                # Decode the outputs
                predicted_location = le_location.inverse_transform([predicted_location_enc])[0]
                predicted_industry = le_industry.inverse_transform([predicted_industry_enc])[0]

                # Display the results
                st.success(translate_text(f"💰 Estimated Selling Price: ₹ {round(predicted_price, 2)} per quintal"))
                st.info(translate_text(f"📍 Recommended Selling Location: {predicted_location}"))
                st.warning(translate_text(f"🏭 Nearest Industry Name: {predicted_industry}"))

            except Exception as e:
                st.error(f"Error occurred: {e}")
           # st.markdown('<a href="http://localhost:8501/" target="_blank">Visualization</a>', unsafe_allow_html=True)
    
    

 


    elif selected == "🌱" + translate_text(" Fertilizer Recommendation System"):
        model = joblib.load("fertilizer_model.pkl")
        label_encoders = joblib.load("label_encoders.pkl")

        st.title(translate_text("🌱 Fertilizer Recommendation System"))
        st.markdown(translate_text("### Enter the soil and climate details to get the best fertilizer recommendation"))

        soil_type = st.selectbox(translate_text("Select Soil Type"), label_encoders["soiltype"].classes_)
        crop_name = st.selectbox(translate_text("Select Crop Name"), label_encoders["cropname"].classes_)

        st.markdown(translate_text("#### **Nutrient & Climate Conditions**"))
        col1, col2, col3 = st.columns(3)

        with col1:
            nitrogen = st.slider(translate_text("Nitrogen"), 0, 100, 50)
            phosphorus = st.slider(translate_text("Phosphorus"), 0, 100, 50)

        with col2:
            potassium = st.slider(translate_text("Potassium"), 0, 100, 50)
            temperature = st.slider(translate_text("Temperature (°C)"), 10, 50, 25)

        with col3:
            moisture = st.slider(translate_text("Moisture (%)"), 10, 90, 50)
            humidity = st.slider(translate_text("Humidity (%)"), 20, 90, 50)

        soil_type_enc = label_encoders["soiltype"].transform([soil_type])[0]
        crop_name_enc = label_encoders["cropname"].transform([crop_name])[0]

        if st.button(translate_text("🌾 Recommend Fertilizer")):
            input_features = np.array([[nitrogen, phosphorus, potassium, temperature, moisture, humidity, soil_type_enc, crop_name_enc]])
            prediction = model.predict(input_features)[0]
            recommended_fertilizer = label_encoders["recommended_fertilizer"].inverse_transform([prediction])[0]
            st.success(f"✅ {translate_text('Recommended Fertilizer')}: {recommended_fertilizer}")


    elif selected == "🌾 " + translate_text("Crop Recommendation System"):
        # Load the trained model and encoders for crop recommendation
        model = joblib.load("crop_model.pkl")
        le_season = joblib.load("season_encoder.pkl")
        le_crop = joblib.load("crop_encoder.pkl")

        st.title("🌾 Crop Recommendation System")
        st.write("Enter the soil and environmental parameters to get the best crop recommendation.")

        # Input fields
        nitrogen = st.number_input("Nitrogen (N)", min_value=0, max_value=150, value=50)
        phosphorus = st.number_input("Phosphorus (P)", min_value=0, max_value=150, value=50)
        potassium = st.number_input("Potassium (K)", min_value=0, max_value=150, value=50)
        temperature = st.number_input("Temperature (°C)", min_value=0.0, max_value=50.0, value=25.0)
        humidity = st.number_input("Humidity (%)", min_value=0.0, max_value=100.0, value=60.0)
        rainfall = st.number_input("Rainfall (mm)", min_value=0.0, max_value=500.0, value=100.0)
        ph = st.number_input("Soil pH", min_value=4.0, max_value=9.0, value=6.5)
        season = st.selectbox("Season", le_season.classes_)

        # Convert season to encoded form
        season_encoded = le_season.transform([season])[0]

        # Check the input features shape
        input_features = np.array([[nitrogen, phosphorus, potassium, temperature, humidity, rainfall, ph, season_encoded]])
        print(input_features.shape)  # To check the shape of the input

        # Recommendation button
        if st.button("Recommend Crop"):
            input_data = np.array([[nitrogen, phosphorus, potassium, temperature, humidity, rainfall, ph, season_encoded]])
            prediction = model.predict(input_data)[0]
            crop = le_crop.inverse_transform([prediction])[0]
            st.markdown(f"<h3 style='font-weight:bold;'>{crop}: {crop_details[crop]['desc']}</h3>", unsafe_allow_html=True)

            st.image(crop_details[crop]['img'], caption=crop)
    elif selected=="📊 Market Visualization":
        st.title("📊 Market Visualization")
        df = pd.read_csv("telangana_crop_market_realistic_dataset.csv")
        # Extract unique crop names for dropdown
        crop_options = sorted(df["crop"].unique())  

        # Sidebar

        st.sidebar.header("Market Visual")
        selected_crop = st.sidebar.selectbox("Select Crop Type", crop_options)
        visualization_type = st.sidebar.selectbox("Select Visualization Type", [
            "Bar Chart", "Scatter Plot", "Pie Chart", "Line Graph", "Area Chart",
            "Heatmap", "Histogram", "Bubble Chart", "Boxplot"
        ])



        # Filter data for selected crop
        crop_data = df[df["crop"] == selected_crop].copy()

        # Convert price range to numerical values (taking average)
        def get_avg_price(price_range):
            prices = [int(price.replace(" ₹/quintal", "").replace(",", "")) for price in price_range.split("–")]
            return sum(prices) / len(prices)

        crop_data["avg_price"] = crop_data["selling_price_range"].apply(get_avg_price)

        # Extract available years
        years = sorted(crop_data["year"].unique())
        avg_prices = {year: crop_data[crop_data["year"] == year]["avg_price"].mean() for year in years}

        # Plot visualizations
        fig, ax = plt.subplots()

        if visualization_type == "Bar Chart":
            ax.bar(avg_prices.keys(), avg_prices.values(), color='green')
            ax.set_xlabel("Year")
            ax.set_ylabel("Average Selling Price (₹/quintal)")
            ax.set_title(f"Price Trend for {selected_crop}")

        elif visualization_type == "Scatter Plot":
            ax.scatter(avg_prices.keys(), avg_prices.values(), color='blue')
            ax.set_xlabel("Year")
            ax.set_ylabel("Average Selling Price (₹/quintal)")
            ax.set_title(f"Price Trend for {selected_crop}")

        elif visualization_type == "Pie Chart":
            ax.pie(avg_prices.values(), labels=avg_prices.keys(), autopct='%1.1f%%', colors=sns.color_palette("pastel"))
            ax.set_title(f"Price Distribution for {selected_crop}")

        elif visualization_type == "Line Graph":
            ax.plot(avg_prices.keys(), avg_prices.values(), marker='o', linestyle='-', color='red')
            ax.set_xlabel("Year")
            ax.set_ylabel("Average Selling Price (₹/quintal)")
            ax.set_title(f"Price Trend for {selected_crop}")

        elif visualization_type == "Area Chart":
            ax.fill_between(avg_prices.keys(), avg_prices.values(), color='skyblue', alpha=0.5)
            ax.set_xlabel("Year")
            ax.set_ylabel("Average Selling Price (₹/quintal)")
            ax.set_title(f"Price Trend for {selected_crop}")

        elif visualization_type == "Heatmap":
            pivot_table = crop_data.pivot_table(index='year', columns='district', values='avg_price', aggfunc='mean')
            plt.figure(figsize=(10, 6))
            sns.heatmap(pivot_table, cmap='coolwarm', annot=True)
            st.pyplot()
            st.stop()

        elif visualization_type == "Histogram":
            ax.hist(crop_data["avg_price"], bins=10, color='purple', alpha=0.7)
            ax.set_xlabel("Price Range (₹/quintal)")
            ax.set_ylabel("Frequency")
            ax.set_title(f"Price Distribution for {selected_crop}")

        elif visualization_type == "Bubble Chart":
            ax.scatter(crop_data["year"], crop_data["avg_price"], s=crop_data["avg_price"]*0.1, alpha=0.5, color='orange')
            ax.set_xlabel("Year")
            ax.set_ylabel("Average Selling Price (₹/quintal)")
            ax.set_title(f"Bubble Chart for {selected_crop}")

        elif visualization_type == "Boxplot":
            sns.boxplot(x=crop_data["year"], y=crop_data["avg_price"], ax=ax)
            ax.set_xlabel("Year")
            ax.set_ylabel("Average Selling Price (₹/quintal)")
            ax.set_title(f"Price Variation for {selected_crop}")


        # Show chart
        st.pyplot(fig)



    elif selected == "main":
    # Background image setup
        def set_background(image_file):
            with open(image_file, "rb") as file:
                encoded_string = base64.b64encode(file.read()).decode()
                css = f"""
                <style>
                .stApp {{
                    background-image: url("data:image/png;base64,{encoded_string}");
                    background-size: cover;
                    background-attachment: fixed;
                    background-position: center;
                }}
                </style>
                """
                st.markdown(css, unsafe_allow_html=True)

        set_background("bg/farm.jpg")

        # Glassmorphism Styling
        st.markdown("""
            <style>
            .glass-box {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 18px;
                padding: 20px 30px;
                margin: 30px auto;
                width: 85%;
                min-height: 150px;
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
                color: #ffffff;
                # text-align: center;
            }
            .nav-row {{
                display: flex;
                justify-content: center;
                gap: 15px;
                margin-bottom: 30px;
                flex-wrap: wrap;
            }}
            .nav-btn button {{
                background-color: rgba(255, 255, 255, 0.2);
                border: none;
                padding: 10px 20px;
                border-radius: 10px;
                color: white;
                font-size: 16px;
                cursor: pointer;
            }}
            </style>
        """, unsafe_allow_html=True)

        # Session state for navigation
        if "page" not in st.session_state:
            st.session_state.page = "home"

        # Navigation Buttons
        def navigation_buttons():
            st.markdown('<div class="nav-row">', unsafe_allow_html=True)
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            with col1:
                if st.button("🏠  Home"):
                    st.session_state.page = "home"
            with col2:
                if st.button("✨ Features"):
                    st.session_state.page = "features"
            with col5:
                if st.button("✉️ Contact us"):
                    st.session_state.page = "contact us"
            with col4:
                if st.button("📞 Agro Directory"):
                    st.session_state.page = "directory"
            with col3:
                if st.button("📘 Schemes"):
                    st.session_state.page = "schemes"
            with col6:
                if st.button("📜 About Project"):
                    st.session_state.page = "about"
            st.markdown('</div>', unsafe_allow_html=True)

        # Go Back Button
        def go_back_button():
            if st.button("🔙 Go Back to Home"):
                st.session_state.page = "home"

        # Display Pages
        if st.session_state.page == "home":
            st.markdown("""
                <div class="glass-box">
                    <h1>🌱 FARM MANAGEMENT SYSTEM</h1>
                    <h3>Empowering Farmers with AI-Powered Agriculture Technology</h3>
                    <p style="font-size:18px;">
                        Our system provides intelligent solutions to support farmers in making better decisions, improving productivity, and getting the best value for their crops.
                    </p>
                    <p style="font-size:20px;"><strong>👉 Click any button below to explore the system features.</strong></p>
                </div>
            """, unsafe_allow_html=True)
            navigation_buttons()

        elif st.session_state.page == "features":
            st.markdown("""
                <div class="glass-box">
                    <h1>🚀 Project Features</h1>
                    <ul>
                        <li><strong>Crop Recommendation System</strong>: Suggests the best crops based on soil type, temperature, humidity, and season.</li>
                    <li><strong>Fertilizer Recommendation System</strong>: Recommends suitable fertilizers based on soil and crop needs.</li>
                    <li><strong>Crop Price Prediction</strong>: Predicts minimum, maximum, and final market prices along with ideal selling locations.</li>
                    <li><strong>Data Visualization</strong>: Visual analytics of crop trends across districts, seasons, and prices.</li>
                    <li><strong>Login Authentication System</strong>: Secure user login for farmers, buyers, and admin roles.</li>
                    <li><strong>Farmer-Buyer Directory</strong>: Connects farmers directly to buyers, eliminating middlemen.</li>
                    <li><strong>AI Chatbot Assistance</strong>: Smart voice assistant to help users in their preferred language.</li>
                    <li><strong>Multilingual Support</strong>: Interface available in English, Hindi, and Telugu.</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)
            go_back_button()
        elif st.session_state.page == "directory":
            st.markdown("<h2 style='color:white;'>📞 Agro Support Directory</h2>", unsafe_allow_html=True)

            language = st.selectbox("Select Language / भाषा चुनें / భాషను ఎంచుకోండి", ["English", "Hindi", "Telugu"])

            # Full 33-district multilingual data
            directory_data = {
                "English": [
                    ["Adilabad", "Mr. Ramesh Goud", "9001234561"],
                    ["Bhadradri Kothagudem", "Ms. Anitha Kumari", "9001234562"],
                    ["Hanamkonda", "Mr. Ravi Teja", "9001234563"],
                    ["Hyderabad", "Dr. Sruthi Rao", "9001234564"],
                    ["Jagtial", "Mr. Mallesh Yadav", "9001234565"],
                    ["Jangaon", "Ms. Deepika Sharma", "9001234566"],
                    ["Jayashankar Bhupalpally", "Mr. Kiran Kumar", "9001234567"],
                    ["Jogulamba Gadwal", "Ms. Swapna Reddy", "9001234568"],
                    ["Kamareddy", "Mr. Harsha Vardhan", "9001234569"],
                    ["Karimnagar", "Mr. Sumanth Reddy", "9001234570"],
                    ["Khammam", "Ms. Sravani", "9001234571"],
                    ["Komaram Bheem Asifabad", "Mr. Venkat Rao", "9001234572"],
                    ["Mahabubabad", "Ms. Lavanya", "9001234573"],
                    ["Mahabubnagar", "Mr. Vijay Kumar", "9001234574"],
                    ["Mancherial", "Ms. Rajeshwari", "9001234575"],
                    ["Medak", "Mr. Narasimha Rao", "9001234576"],
                    ["Medchal–Malkajgiri", "Ms. Neha Verma", "9001234577"],
                    ["Mulugu", "Mr. Praveen Yadav", "9001234578"],
                    ["Nagarkurnool", "Ms. Shalini Devi", "9001234579"],
                    ["Nalgonda", "Mr. Anil Kumar", "9001234580"],
                    ["Nirmal", "Ms. Priya Reddy", "9001234581"],
                    ["Nizamabad", "Mr. Arvind Rao", "9001234582"],
                    ["Peddapalli", "Ms. Sneha Sharma", "9001234583"],
                    ["Rajanna Sircilla", "Mr. Raghav Reddy", "9001234584"],
                    ["Ranga Reddy", "Ms. Meena Das", "9001234585"],
                    ["Sangareddy", "Mr. Venkatesh", "9001234586"],
                    ["Siddipet", "Ms. Anjali Rao", "9001234587"],
                    ["Suryapet", "Mr. Karthik Reddy", "9001234588"],
                    ["Vikarabad", "Ms. Ramya Kumari", "9001234589"],
                    ["Wanaparthy", "Mr. Bharat Kumar", "9001234590"],
                    ["Warangal", "Ms. Divya Rao", "9001234591"],
                    ["Yadadri Bhuvanagiri", "Mr. Manohar Reddy", "9001234592"]
                ],
                "Hindi": [
                    ["आदिलाबाद", "श्री रमेश गौड़", "9001234561"],
                    ["भद्राद्री कोठागुडेम", "सुश्री अनिता कुमारी", "9001234562"],
                    ["हनमकोंडा", "श्री रवि तेजा", "9001234563"],
                    ["हैदराबाद", "डॉ. श्रुति राव", "9001234564"],
                    ["जगतियाल", "श्री मल्लेश यादव", "9001234565"],
                    ["जंगांव", "सुश्री दीपिका शर्मा", "9001234566"],
                    ["जयशंकर भूपालपल्ली", "श्री किरण कुमार", "9001234567"],
                    ["जोगुलम्बा गडवाल", "सुश्री स्वप्ना रेड्डी", "9001234568"],
                    ["कामारेड्डी", "श्री हर्ष वर्धन", "9001234569"],
                    ["करीमनगर", "श्री सुमंत रेड्डी", "9001234570"],
                    ["खम्मम", "सुश्री श्रावणी", "9001234571"],
                    ["कोमराम भीम आसिफाबाद", "श्री वेंकट राव", "9001234572"],
                    ["महबूबाबाद", "सुश्री लावण्या", "9001234573"],
                    ["महबूबनगर", "श्री विजय कुमार", "9001234574"],
                    ["मंचेरियल", "सुश्री राजेश्वरी", "9001234575"],
                    ["मेडक", "श्री नरसिम्हा राव", "9001234576"],
                    ["मेडचल-मल्काजगिरी", "सुश्री नेहा वर्मा", "9001234577"],
                    ["मुलुगु", "श्री प्रवीण यादव", "9001234578"],
                    ["नागरकुरनूल", "सुश्री शालिनी देवी", "9001234579"],
                    ["नालगोंडा", "श्री अनिल कुमार", "9001234580"],
                    ["निर्मल", "सुश्री प्रिया रेड्डी", "9001234581"],
                    ["निजामाबाद", "श्री अरविंद राव", "9001234582"],
                    ["पेड्डापल्ली", "सुश्री स्नेहा शर्मा", "9001234583"],
                    ["राजन्ना सिर्सिल्ला", "श्री राघव रेड्डी", "9001234584"],
                    ["रंगारेड्डी", "सुश्री मीना दास", "9001234585"],
                    ["संगारेड्डी", "श्री वेंकटेश", "9001234586"],
                    ["सिद्दीपेट", "सुश्री अंजली राव", "9001234587"],
                    ["सूर्यापेट", "श्री कार्तिक रेड्डी", "9001234588"],
                    ["विकाराबाद", "सुश्री राम्या कुमारी", "9001234589"],
                    ["वनपर्थी", "श्री भरत कुमार", "9001234590"],
                    ["वारंगल", "सुश्री दिव्या राव", "9001234591"],
                    ["यदाद्री भुवनगिरी", "श्री मनोहर रेड्डी", "9001234592"]
                ],
                "Telugu": [
                    ["ఆదిలాబాద్", "శ్రీ రమేష్ గౌడ్", "9001234561"],
                    ["భద్రాద్రి కొత్తగూడెం", "శ్రీమతి అనిత కుమారి", "9001234562"],
                    ["హనమకొండ", "శ్రీ రవి తేజ", "9001234563"],
                    ["హైదరాబాద్", "డా. శ్రుతి రావు", "9001234564"],
                    ["జగిత్యాల", "శ్రీ మల్లేష్ యాదవ్", "9001234565"],
                    ["జన్గాన్", "శ్రీమతి దీపికా శర్మ", "9001234566"],
                    ["జయశంకర్ భూపాలపల్లి", "శ్రీ కిరణ్ కుమార్", "9001234567"],
                    ["జోగులాంబ గద్వాల", "శ్రీమతి స్వప్నా రెడ్డి", "9001234568"],
                    ["కామారెడ్డి", "శ్రీ హర్ష వర్ధన్", "9001234569"],
                    ["కరీంనగర్", "శ్రీ సుమంత్ రెడ్డి", "9001234570"],
                    ["ఖమ్మం", "శ్రీమతి శ్రావణి", "9001234571"],
                    ["కొమరంభీం ఆసిఫాబాద్", "శ్రీ వెంకట్ రావు", "9001234572"],
                    ["మహబూబాబాద్", "శ్రీమతి లావణ్య", "9001234573"],
                    ["మహబూబ్‌నగర్", "శ్రీ విజయ్ కుమార్", "9001234574"],
                    ["మంచెరిఅల్", "శ్రీమతి రాజేశ్వరి", "9001234575"],
                    ["మేడక్", "శ్రీ నరసింహ రావు", "9001234576"],
                    ["మేడ్చల్-మల్కాజ్గిరి", "శ్రీమతి నేహా వర్మ", "9001234577"],
                    ["ములుగు", "శ్రీ ప్రవీణ్ యాదవ్", "9001234578"],
                    ["నాగర్‌కర్నూల్", "శ్రీమతి శాలినీ దేవి", "9001234579"],
                    ["నల్గొండ", "శ్రీ అనిల్ కుమార్", "9001234580"],
                    ["నిర్మల్", "శ్రీమతి ప్రియా రెడ్డి", "9001234581"],
                    ["నిజామాబాద్", "శ్రీ అరవింద్ రావు", "9001234582"],
                    ["పెద్దపల్లి", "శ్రీమతి స్నేహా శర్మ", "9001234583"],
                    ["రాజన్న సిరిసిల్ల", "శ్రీ రాఘవ్ రెడ్డి", "9001234584"],
                    ["రంగారెడ్డి", "శ్రీమతి మీనా దాస్", "9001234585"],
                    ["సంగారెడ్డి", "శ్రీ వెంకటేష్", "9001234586"],
                    ["సిద్దిపేట", "శ్రీమతి అంజలి రావు", "9001234587"],
                    ["సూర్యాపేట", "శ్రీ కార్తీక్ రెడ్డి", "9001234588"],
                    ["వికారాబాద్", "శ్రీమతి రమ్య కుమారి", "9001234589"],
                    ["వనపర్తి", "శ్రీ భరత్ కుమార్", "9001234590"],
                    ["వరంగల్", "శ్రీమతి దివ్యా రావు", "9001234591"],
                    ["యాదాద్రి భువనగిరి", "శ్రీ మనోహర్ రెడ్డి", "9001234592"]
                ]
            }

            headers = {
                "English": ["District", "Agro Officer", "Contact Number"],
                "Hindi": ["जिला", "कृषि अधिकारी", "संपर्क नंबर"],
                "Telugu": ["జిల్లా", "వ్యవసాయ అధికారి", "సంప్రదించండి"]
            }

            note_text = {
                "English": "📌 Note: For latest updates, contact your nearest Agri Office or call 1800-180-1551.",
                "Hindi": "📌 नोट: नवीनतम जानकारी के लिए अपने निकटतम कृषि कार्यालय से संपर्क करें या 1800-180-1551 पर कॉल करें।",
                "Telugu": "📌 గమనిక: తాజా సమాచారం కోసం మీకు దగ్గరలోని వ్యవసాయ కార్యాలయాన్ని సంప్రదించండి లేదా 1800-180-1551 కి కాల్ చేయండి."
            }

            table_html = f"""<style> .glass-box {{background: rgba(255,255,255,0.08); backdrop-filter: blur(10px); border-radius: 20px; padding: 25px; color: white; font-family: 'Segoe UI', sans-serif;}} table {{width:100%; border-collapse: collapse;}} th,td {{border: 1px solid #ddd; padding:10px;}} th {{background:#4CAF50; color:white;}}</style><div class="glass-box"><table><tr><th>{headers[language][0]}</th><th>{headers[language][1]}</th><th>{headers[language][2]}</th></tr>"""

            for row in directory_data[language]:
                table_html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>"

            table_html += "</table><p style='margin-top:10px;'><em></em></p></div>"
            st.markdown(table_html, unsafe_allow_html=True)

            if st.button("🔙 Go Back to Home"):
                st.session_state.page = "home"
        elif  st.session_state.page == "contact us":
            st.markdown("""
                <style>
                    .contact-box {
                        background: rgba(255, 255, 255, 0.15);
                        border-radius: 20px;
                        padding: 30px;
                        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                        backdrop-filter: blur(10px);
                        -webkit-backdrop-filter: blur(10px);
                        border: 1px solid rgba(255, 255, 255, 0.18);
                        margin-top: 40px;
                    }
                    .contact-box h1 {
                        color: #ffffff;
                        font-size: 32px;
                        text-align: center;
                    }
                    .contact-box h3 {
                        color: #ffffff;
                        font-size: 22px;
                        margin-top: 25px;
                    }
                    .contact-box p {
                        color: #ffffff;
                        font-size: 18px;
                        line-height: 1.6;
                    }
                    .contact-box a {
                        color: #00ffe7;
                        text-decoration: none;
                    }
                    .contact-box a:hover {
                        text-decoration: underline;
                    }
                </style>

                <div class="contact-box">
                    <h1>📌 Contact Help</h1>
                    <p>
                        The <strong>Farm Management System</strong> was initiated with a noble vision — <strong>to empower farmers using modern AI-based technologies</strong> that simplify decision-making and enhance agricultural outcomes.
                    </p>
                    <h3>📞 Contact Details:</h3>
                    <p>
                        <strong>Phone Number:</strong> +91 87864 98706<br>
                        <strong>Email:</strong> <a href="mailto:agrointel@gmail.com">agrointel@gmail.com</a>
                    </p>
                    <h3>📱 Connect with us on Social Media:</h3>
                    <p>
                        <strong>Instagram:</strong> <a href="https://www.instagram.com/_Agrointel_" target="_blank">@_Agrointel_</a><br>
                        <strong>Facebook:</strong> <a href="https://www.facebook.com/Agrointel17" target="_blank">Agrointel17</a>
                    </p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("🔙 Go Back to Home"):
                st.session_state.page = "home"
        elif st.session_state.page == "about":
            st.markdown("""
                    <div class="glass-box">
                        <h1>📘 About the Project</h1>
                        <p style="font-size:18px;">
                            The <strong>Telangana Crop Market Price Prediction & Farm Management System</strong> is a smart, farmer-centric platform built to empower farmers through data-driven technology.
                            It merges Artificial Intelligence, Machine Learning, and user-friendly digital tools to improve agriculture productivity and decision-making.
                        </p>
                        <p style="font-size:18px;">
                            🌱 The integrated <strong>Farm Management System</strong> helps farmers track farming activities, select crops, manage soil health, and boost yield through intelligent insights.
                        </p>
                        <p style="font-size:18px;">
                            💡 The <strong>Fertilizer Recommendation System</strong> uses AI models to suggest optimal nutrients (NPK) based on soil and crop data—ensuring eco-friendly, profitable farming.
                        </p>
                        <p style="font-size:18px;">
                            📊 The <strong>Market Price Prediction System</strong> forecasts crop prices (Min, Max, Final Selling Price), suggests selling locations, and connects farmers directly to nearby industries or buyers.
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            if st.button("🔙 Go Back to Home"):
                st.session_state.page = "home"
        elif st.session_state.page == "schemes":
            lang = st.sidebar.selectbox("🌐 Select Language", ["English", "हिंदी", "తెలుగు"])
            # Content Dictionary (Multilingual Display) 
            acts_content = {
                "English": [
                    '1. PM-KISAN Samman Nidhi Yojana – ₹6000/year direct support <a href="https://pmkisan.gov.in" target="_blank">Visit</a>',
                    '2. Kisan Credit Card (KCC) Scheme – Low interest loans <a href="https://vikaspedia.in/schemesall/schemes-for-farmers/kisan-credit-card-scheme" target="_blank">Visit</a>',
                    '3. PM Fasal Bima Yojana – Crop insurance <a href="https://pmfby.gov.in" target="_blank">Visit</a>',
                    '4. Interest Subvention on Crop Loans <a href="https://agricoop.nic.in/en/Interest-Subvention-Scheme" target="_blank">Visit</a>',
                    '5. Soil Health Card Scheme <a href="https://soilhealth.dac.gov.in" target="_blank">Visit</a>',
                    '6. PM Krishi Sinchayee Yojana <a href="https://pmksy.gov.in" target="_blank">Visit</a>',
                    '7. eNAM - National Agriculture Market <a href="https://www.enam.gov.in" target="_blank">Visit</a>',
                    '8. Sub-Mission on Agricultural Mechanization (SMAM) <a href="https://agrimachinery.nic.in" target="_blank">Visit</a>',
                    '9. Rashtriya Krishi Vikas Yojana (RKVY) <a href="https://rkvy.nic.in" target="_blank">Visit</a>',
                    '10. National Mission for Sustainable Agriculture (NMSA) <a href="https://nmsa.dac.gov.in" target="_blank">Visit</a>',
                    '11. Agricultural Infrastructure Fund (AIF) <a href="https://www.agriinfra.dac.gov.in" target="_blank">Visit</a>',
                    '12. Minimum Support Price (MSP) Policy <a href="https://agricoop.nic.in/en/MSP" target="_blank">Visit</a>',
                    '13. Farmers’ Produce Trade & Commerce Act 2020 <a href="https://egazette.nic.in/WriteReadData/2020/222039.pdf" target="_blank">Visit</a>',
                    '14. PM-AASHA Scheme <a href="https://pib.gov.in/PressReleasePage.aspx?PRID=1545274" target="_blank">Visit</a>',
                ],
                
                "हिंदी": [
                    '1. पीएम किसान सम्मान निधि योजना – ₹6000 वार्षिक सहायता <a href="https://pmkisan.gov.in" target="_blank">देखें</a>',
                    '2. किसान क्रेडिट कार्ड योजना – कम ब्याज पर ऋण <a href="https://vikaspedia.in/schemesall/schemes-for-farmers/kisan-credit-card-scheme" target="_blank">देखें</a>',
                    '3. प्रधानमंत्री फसल बीमा योजना <a href="https://pmfby.gov.in" target="_blank">देखें</a>',
                    '4. फसल ऋण पर ब्याज सब्सिडी <a href="https://agricoop.nic.in/en/Interest-Subvention-Scheme" target="_blank">देखें</a>',
                    '5. मृदा स्वास्थ्य कार्ड योजना <a href="https://soilhealth.dac.gov.in" target="_blank">देखें</a>',
                    '6. पीएम कृषि सिंचाई योजना <a href="https://pmksy.gov.in" target="_blank">देखें</a>',
                    '7. ई-नाम राष्ट्रीय कृषि बाजार <a href="https://www.enam.gov.in" target="_blank">देखें</a>',
                    '8. कृषि यंत्रीकरण मिशन <a href="https://agrimachinery.nic.in" target="_blank">देखें</a>',
                    '9. राष्ट्रीय कृषि विकास योजना <a href="https://rkvy.nic.in" target="_blank">देखें</a>',
                    '10. सतत कृषि मिशन <a href="https://nmsa.dac.gov.in" target="_blank">देखें</a>',
                    '11. कृषि इंफ्रास्ट्रक्चर फंड <a href="https://www.agriinfra.dac.gov.in" target="_blank">देखें</a>',
                    '12. न्यूनतम समर्थन मूल्य नीति <a href="https://agricoop.nic.in/en/MSP" target="_blank">देखें</a>',
                    '13. किसान उपज व्यापार एवं वाणिज्य अधिनियम 2020 <a href="https://egazette.nic.in/WriteReadData/2020/222039.pdf" target="_blank">देखें</a>',
                    '14. पीएम-आशा योजना <a href="https://pib.gov.in/PressReleasePage.aspx?PRID=1545274" target="_blank">देखें</a>',
                ],

                "తెలుగు": [
                    '1. పీఎం-కిసాన్ సమ్మాన్ నిధి – ₹6000 వార్షిక సహాయం <a href="https://pmkisan.gov.in" target="_blank">చూడండి</a>',
                    '2. రైతు క్రెడిట్ కార్డ్ – తక్కువ వడ్డీ రుణాలు <a href="https://vikaspedia.in/schemesall/schemes-for-farmers/kisan-credit-card-scheme" target="_blank">చూడండి</a>',
                    '3. పీఎం పంటల బీమా పథకం <a href="https://pmfby.gov.in" target="_blank">చూడండి</a>',
                    '4. పంట రుణాలపై వడ్డీ సబ్సిడీ <a href="https://agricoop.nic.in/en/Interest-Subvention-Scheme" target="_blank">చూడండి</a>',
                    '5. మట్టి ఆరోగ్య కార్డు పథకం <a href="https://soilhealth.dac.gov.in" target="_blank">చూడండి</a>',
                    '6. పీఎం వ్యవసాయ సాగునీటి పథకం <a href="https://pmksy.gov.in" target="_blank">చూడండి</a>',
                    '7. ఈ-నామ్ – జాతీయ వ్యవసాయ మార్కెట్ <a href="https://www.enam.gov.in" target="_blank">చూడండి</a>',
                    '8. వ్యవసాయ యంత్రాల మిషన్ <a href="https://agrimachinery.nic.in" target="_blank">చూడండి</a>',
                    '9. జాతీయ వ్యవసాయ అభివృద్ధి పథకం <a href="https://rkvy.nic.in" target="_blank">చూడండి</a>',
                    '10. స్థిర వ్యవసాయం మిషన్ <a href="https://nmsa.dac.gov.in" target="_blank">చూడండి</a>',
                    '11. వ్యవసాయ మౌలిక సదుపాయాల నిధి <a href="https://www.agriinfra.dac.gov.in" target="_blank">చూడండి</a>',
                    '12. కనిష్ఠ మద్దతు ధర విధానం <a href="https://agricoop.nic.in/en/MSP" target="_blank">చూడండి</a>',
                    '13. రైతుల ఉత్పత్తుల వ్యాపార చట్టం 2020 <a href="https://egazette.nic.in/WriteReadData/2020/222039.pdf" target="_blank">చూడండి</a>',
                    '14. పీఎం-ఆషా పథకం <a href="https://pib.gov.in/PressReleasePage.aspx?PRID=1545274" target="_blank">చూడండి</a>',
                ]
            }

        if st.session_state.page == "schemes":
            st.markdown(f"""
            <div class="glass-box">
                <h2>📘 Farmer Schemes & Subsidies - {lang}</h2>
                <ul>
                    {''.join([f'<li>{line}</li>' for line in acts_content[lang]])}
                </ul>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔙 Go Back to Home"):
                st.session_state.page = "home"
    
    
    
    
    
    elif selected == "💬Chatbot":
        st.title("Chatbot")
        st.write("This is a chatbot. You can ask me anything.")
        rop_model = joblib.load("crop_model.pkl")  # Replace with your model

        # Load fertilizer recommendation model
        fertilizer_model = joblib.load("fertilizer_model.pkl")  # Replace with your model

        # Configure Gemini API Key
        GEMINI_API_KEY = "AIzaSyDIEjgkzuP-KUt3J_TQS6_Nqln5IIR3fhM"  # Replace with your API Key
        genai.configure(api_key=GEMINI_API_KEY)

        # Select Gemini model
        model = genai.GenerativeModel("gemini-1.5-pro")

        # Streamlit UI
        st.title("🚜 AI Farming Chatbot")
        st.subheader("Ask about Crops, Fertilizers, and Market Prices!")

        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Function to predict crop recommendation
        def recommend_crop(N, P, K, temperature, humidity, pH, rainfall):
            input_data = np.array([[N, P, K, temperature, humidity, pH, rainfall]])
            crop = crop_model.predict(input_data)[0]
            return f"The best crop for your soil and climate is **{crop}**."

        # Function to predict fertilizer recommendation
        def recommend_fertilizer(soil_type, crop_type, N, P, K):
            input_data = np.array([[soil_type, crop_type, N, P, K]])
            fertilizer = fertilizer_model.predict(input_data)[0]
            return f"The recommended fertilizer for **{crop_type}** on **{soil_type}** soil is **{fertilizer}**."

        # Function to get AI response
        def chat_with_gemini(prompt):
            try:
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                return f"⚠️ Error: {e}"

        # Display previous messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # User input
        user_input = st.chat_input("Ask me about farming...")

        # Handle user input
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            # Check for crop recommendation query
            if "recommend a crop" in user_input.lower():
                st.write("🌱 Please enter soil details:")
                N = st.number_input("Nitrogen (N)", min_value=0, max_value=200)
                P = st.number_input("Phosphorous (P)", min_value=0, max_value=200)
                K = st.number_input("Potassium (K)", min_value=0, max_value=200)
                temperature = st.number_input("Temperature (°C)")
                humidity = st.number_input("Humidity (%)")
                pH = st.number_input("Soil pH")
                rainfall = st.number_input("Rainfall (mm)")

                if st.button("Get Crop Recommendation"):
                    crop_response = recommend_crop(N, P, K, temperature, humidity, pH, rainfall)
                    st.session_state.messages.append({"role": "assistant", "content": crop_response})
                    with st.chat_message("assistant"):
                        st.markdown(crop_response)

            # Check for fertilizer recommendation query
            elif "recommend a fertilizer" in user_input.lower():
                st.write("🌾 Please enter crop and soil details:")
                soil_type = st.selectbox("Select Soil Type", ["Sandy", "Loamy", "Clayey"])
                crop_type = st.text_input("Enter Crop Name")
                N = st.number_input("Nitrogen (N)", min_value=0, max_value=200)
                P = st.number_input("Phosphorous (P)", min_value=0, max_value=200)
                K = st.number_input("Potassium (K)", min_value=0, max_value=200)

                if st.button("Get Fertilizer Recommendation"):
                    fertilizer_response = recommend_fertilizer(soil_type, crop_type, N, P, K)
                    st.session_state.messages.append({"role": "assistant", "content": fertilizer_response})
                    with st.chat_message("assistant"):
                        st.markdown(fertilizer_response)

            # Default AI response for general questions
            else:
                ai_response = chat_with_gemini(user_input)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                with st.chat_message("assistant"):
                    st.markdown(ai_response)




