import joblib
import pandas as pd
import numpy as np

# -------------------------
# Load Dataset
# -------------------------
def load_data():
    df = pd.read_csv("diabetes.csv")  # Make sure this file exists in the same folder
    X = df.drop(columns=["Outcome"])
    y = df["Outcome"]
    return df, X, y

# -------------------------
# Load Trained Pipeline
# -------------------------
pipeline = joblib.load("diabetes_pipeline.pkl")  # Corrected path

# -------------------------
# Prediction Function
# -------------------------
def predict(X, y, input_features):
    input_array = np.array(input_features).reshape(1, -1)
    
    # Scale input using pipeline's scaler
    scaled_input = pipeline["scaler"].transform(input_array)
    
    # Predict using model
   
    prediction = pipeline["model"].predict(scaled_input)[0]
    confidence = pipeline["model"].predict_proba(scaled_input)[0][int(prediction)]

    
    return prediction, confidence





