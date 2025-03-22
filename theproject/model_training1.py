import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib

# Load the dataset
df = pd.read_csv("crop_recommendation_dataset.csv")

# Encode the categorical "Season" and "Crop_Label"
le_season = LabelEncoder()
df['Season'] = le_season.fit_transform(df['Season'])

le_crop = LabelEncoder()
df['Crop_Label'] = le_crop.fit_transform(df['Crop_Label'])

# Split dataset into features and target
X = df.drop(columns=['Crop_Label'])
y = df['Crop_Label']

# Split into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train a RandomForest model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save the model and encoders
joblib.dump(model, "crop_model.pkl")
joblib.dump(le_season, "season_encoder.pkl")
joblib.dump(le_crop, "crop_encoder.pkl")

print("Model training complete. Saved as crop_model.pkl")


