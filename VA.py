import streamlit as st
import speech_recognition as sr
import pyttsx3
import sqlite3
import google.generativeai as genai

API_KEY = "AIzaSyAEezurOxJEOkzbbdgPpPUXZvZADfrZoZU"
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-pro')
chat = model.start_chat(history=[])

instruction = "In this chat, respond as if you're explaining things to a five-year-old child."

# Initialize database
def init_db():
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            speaker TEXT,
            message TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Save chat message to database
def save_message(speaker, message):
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('INSERT INTO chat (speaker, message) VALUES (?, ?)', (speaker, message))
    conn.commit()
    conn.close()

# Load chat history from database
def load_history():
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('SELECT speaker, message FROM chat')
    history = c.fetchall()
    conn.close()
    return history

init_db()

def send_message(question):
    if question.strip() == '':
        return "Please ask something."

    response = chat.send_message(instruction + question)
    return response.text

def exit_conversation():
    chat.history = []
    st.session_state['conversation_ended'] = True
    st.session_state['conversation'] = []
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('DELETE FROM chat')
    conn.commit()
    conn.close()

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        st.write("Listening...")
        audio = recognizer.listen(source)

    try:
        question = recognizer.recognize_google(audio)
        st.session_state['question'] = question
        st.session_state['conversation'].append(("You", question))
        save_message("You", question)
        
        # Display the user's question immediately
        st.experimental_rerun()

    except sr.UnknownValueError:
        st.error("Could not understand audio")
    except sr.RequestError as e:
        st.error(f"Could not request results; {e}")

st.title("Voice Assistant")

if 'conversation_ended' not in st.session_state:
    st.session_state['conversation_ended'] = False

if 'conversation' not in st.session_state:
    st.session_state['conversation'] = load_history()

if 'question' not in st.session_state:
    st.session_state['question'] = ''

if 'response' not in st.session_state:
    st.session_state['response'] = ''

# Process bot response if a new question was added
if st.session_state['question'] and (len(st.session_state['conversation']) % 2 != 0):
    response = send_message(st.session_state['question'])
    st.session_state['response'] = response
    st.session_state['conversation'].append(("Bot", response))
    save_message("Bot", response)
    st.session_state['question'] = ''  # Reset question to indicate processing is done

    engine = pyttsx3.init()

# Display conversation history with styling
    st.write("### Conversation")
    for speaker, text in st.session_state['conversation']:
        if speaker == "You":
            st.markdown(f"""
            <div style='text-align: left; background-color: #dcf8c6;color: black; padding: 8px; border-radius: 10px; margin: 5px;'>
                <b>You:</b> {text}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='text-align: left; background-color: #f1f0f0;color: black; padding: 8px; border-radius: 10px; margin: 5px;'>
                <b>Bot:</b> {text}
            </div>
            """, unsafe_allow_html=True)
    engine.say(response)
    engine.runAndWait()


# Button layout
col1, col3 = st.columns(2)

with col1:
    if st.button("Listen"):
        if not st.session_state['conversation_ended']:
            listen()
        else:
            st.write("Conversation has ended. Please refresh the page to start a new conversation.")

with col3:
    if not st.session_state['conversation_ended']:
        if st.button("Exit Conversation"):
            exit_conversation()
            st.write("Conversation terminated. Say 'Listen' to start again.")