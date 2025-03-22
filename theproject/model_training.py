import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier

# Load dataset
df = pd.read_csv("large_fertilizer_recommendation_dataset.csv")

# Encode categorical variables
label_encoders = {}
for col in ["soiltype", "cropname", "recommended_fertilizer"]:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
    label_encoders[col] = le

# Define features and target
X = df.drop(columns=["recommended_fertilizer"])
y = df["recommended_fertilizer"]

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Train the model
model = RandomForestClassifier(n_estimators=300, max_depth=20, random_state=42)
model.fit(X_train, y_train)

# Save model and encoders
joblib.dump(model, "fertilizer_model.pkl")
joblib.dump(label_encoders, "label_encoders.pkl")

print("✅ Model training complete! The model and encoders are saved.")
