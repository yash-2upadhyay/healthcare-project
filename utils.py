from pymongo import MongoClient
from cryptography.fernet import Fernet
from datetime import datetime
import streamlit as st

# Setup MongoDB client and cipher - reuse your secrets from Streamlit
client = MongoClient(st.secrets["mongodb"]["uri"])
db = client["diabetes_app"]
queries_col = db["user_data"]

key = st.secrets["encryption"]["key"].encode()
cipher = Fernet(key)

def store_user_query(username, query):
    encrypted_query = cipher.encrypt(query.encode())
    queries_col.insert_one({
        "user": username,
        "timestamp": datetime.utcnow(),
        "query": encrypted_query
    })

def get_user_queries(username):
    docs = queries_col.find({"user": username})
    decrypted_queries = []
    for doc in docs:
        decrypted_query = cipher.decrypt(doc["query"]).decode()
        decrypted_queries.append((doc["timestamp"], decrypted_query))
    return decrypted_queries
