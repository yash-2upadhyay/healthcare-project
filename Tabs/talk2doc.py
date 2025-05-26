import streamlit as st
import google.generativeai as genai
from utils import store_user_query  # import your utils here

GEMINI_API_KEY = st.secrets["gemini"]["api_key"]


if not GEMINI_API_KEY:
    st.error("API key is missing! Add it to Streamlit secrets.")
    st.stop()

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def ask_gemini(query):
    prompt = f"""
You are a medical chatbot specialized in diabetes and its health implications. 
Answer only diabetes-related queries with medically accurate information. 
If a question is unrelated to diabetes, politely inform the user that you can only answer diabetes-related questions.

**User's Question:** {query}

Provide a clear, concise, and accurate medical response.
"""
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text

def app():
    st.title("🩺 Diabetes Medical Chatbot")
    st.image('./images/capsule.png')
    st.success("Please ask your queries related to diabetes and its health implications.")

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_query = st.text_input("Ask your question about diabetes:")

    if st.button("Get Answer") and user_query.strip():
        username = st.session_state.get("username")
        if username:
            # Store user query securely in DB (encrypted)
            store_user_query(username, user_query)

        response = ask_gemini(user_query)

        st.session_state.chat_history.append(("You", user_query))
        st.session_state.chat_history.append(("Chatbot", response))

    if st.session_state.chat_history:
        st.subheader("Chat History:")
        for role, message in st.session_state.chat_history:
            icon = "🧑‍⚕️" if role == "You" else "🤖"
            st.markdown(f"**{icon} {role}:** {message}")




