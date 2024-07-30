import os
import streamlit as st
from googleapiclient.discovery import build
import requests
from dotenv import load_dotenv
import google.generativeai as genai
from transformers import pipeline
import speech_recognition as sr
from datetime import datetime, timedelta
import smtplib
import pyttsx3
import sqlite3
from email.mime.text import MIMEText
import matplotlib.pyplot as plt
import pandas as pd
import PyPDF2
from io import BytesIO# Load environment variables
load_dotenv()

# Configure API keys
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
GENAI_API_KEY = os.getenv("GOOGLE_API_KEY")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")

# Configure Google Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

# Utility functions
def fetch_youtube_videos(query, api_key, max_results=5):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.search().list(
            q=query,
            part='snippet',
            type='video',
            maxResults=max_results,
            order='viewCount'
        )
        response = request.execute()
        return response['items']
    except Exception as e:
        return f"An error occurred: {e}"

def fetch_serper_results(query, num_results=5):
    try:
        headers = {'X-API-KEY': SERPER_API_KEY}
        params = {'q': query, 'num': num_results, 'gl': 'us', 'hl': 'en'}
        response = requests.get('https://google.serper.dev/search', headers=headers, params=params)
        if response.status_code == 200:
            results = response.json()
            return results.get('organic', [])
        else:
            return f"An error occurred: {response.status_code} - {response.text}"
    except Exception as e:
        return f"An error occurred: {e}"

def get_gemini_response(question):
    response = chat.send_message(question, stream=True)
    return response


def send_test_email(from_email, to_email, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(from_email, "your-email-password")
            server.send_message(msg)
        print("Test email sent successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")
        
def generate_quiz_questions(topic, grade):
    query = f"Generate 10 quiz questions for {grade} students on the topic {topic} with 4 options and correct answer"
    response = get_gemini_response(query)
    content = "".join([chunk.text for chunk in response])
    questions = content.split("\n\n")  # assuming each question is separated by two newlines
    quiz = []
    for question in questions:
        parts = question.split("\n")  # split question and options
        if len(parts) >= 6:
            q = parts[0]
            options = parts[1:5]
            correct_answer = parts[5].replace("Correct answer: ", "").strip()
            quiz.append({"question": q, "options": options, "correct_answer": correct_answer})
    return quiz

def process_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfFileReader(BytesIO(pdf_file.read()))
    num_pages = pdf_reader.numPages
    text = ""
    for page in range(num_pages):
        text += pdf_reader.getPage(page).extract_text()
    return text

def plot_chart(data, title):
    fig, ax = plt.subplots()
    ax.bar(data['Question'], range(len(data)), color='skyblue')
    ax.set_xlabel('Questions')
    ax.set_ylabel('Answer Scores')
    ax.set_title(title)
    plt.xticks(rotation=90)
    st.pyplot(fig)

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

def display_large_sidebar_section(title):
    st.sidebar.markdown(f"""
    <div style="font-size:20px; font-weight:bold; margin-bottom:20px;">
        {title}
    </div>
    """, unsafe_allow_html=True)


# Initialize Streamlit app
st.set_page_config(page_title="AI-Powered Adaptive Learning Platform", layout="wide")

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 12px;
        font-size: 16px;
        padding: 10px 24px;
        margin: 10px 0px;
    }
    .stTextInput>div>div>input {
        border: 2px solid #4CAF50;
        border-radius: 12px;
    }
    .stTextArea>div>div>textarea {
        border: 2px solid #4CAF50;
        border-radius: 12px;
    }
    .stSlider>div>div>div>div {
        color: #4CAF50;
    }
    .header {
        text-align: center;
        padding: 20px;
        background: url('https://source.unsplash.com/1600x900/?education,learning') no-repeat center center;
        background-size: cover;
        color: white;
        border-radius: 12px;
    }
    .section-header {
        margin-top: 20px;
        padding: 10px;
        background-color: #4CAF50;
        color: white;
        border-radius: 12px;
        text-align: center;
    }
    .sidebar .sidebar-content {
        background-color: #4CAF50;
        color: white;
        border-radius: 12px;
        padding: 20px;
    }
    </style>
    """, unsafe_allow_html=True)


st.title(" 👨🏻‍💻 AI-Powered Adaptive Learning Platform")



# Sidebar for navigation
st.sidebar.title("Features")
sections = ["Home","Educational Content Finder", "Meeting Reminder", "Lecture Enhancement", "Automated Feedback System", "Language Learning Companion", "AI-BOT","Lets Try Quizzz","Automated Assignment Generator", "Voice Assistant"]

section = st.sidebar.radio("Use", sections)

if section == "Home":
    
    st.image("E:\Adarsh\AI\AI_Learning\Random Input Vector (5).png", use_column_width=True, caption="AI-Powered Adaptive Learning Platform")



elif section == "Educational Content Finder":
    st.header("📚 Educational Content Finder")

    query = st.text_input("Enter your query:")
    grade = st.selectbox("Select your grade level:", [
        "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5",
        "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10",
        "Grade 11", "Grade 12"
    ])

    if st.button("Search"):
        if query:
            search_query = f"{query} for {grade}"
            st.write(f"### Searching YouTube for: {search_query}")
            videos = fetch_youtube_videos(search_query, YOUTUBE_API_KEY)
            if isinstance(videos, str):
                st.error(videos)
            else:
                st.write("### YouTube Videos:")
                for video in videos:
                    title = video['snippet']['title']
                    video_id = video['id']['videoId']
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    thumbnail_url = video['snippet']['thumbnails']['high']['url']
                    description = video['snippet'].get('description', 'No description available')

                    st.markdown(f"""
                        <a href="{video_url}" target="_blank">
                            <img src="{thumbnail_url}" alt="{title}" style="width:120px; height:90px; object-fit:cover;"/>
                        </a>
                        Title: <strong>{title}</strong><br>
                        Description: <strong><span style="font-size:14px;">{description[:150]}...</span> <!-- Truncate description if too long --></strong><br>

                    """, unsafe_allow_html=True)
                    st.write("---")
                    #st.write(f"**Title:** {title}")
                    #st.write(f"**Link:** [Watch Video]({video_url})")
                    #st.write("---")
            
            st.write(f"### Resource Results: {search_query}")
            google_results = fetch_serper_results(search_query)
            if isinstance(google_results, str):
                st.error(google_results)
            else:
                st.write("### Resource Results:")
                for result in google_results:
                    title = result.get('title', 'No title available')
                    link = result.get('link', 'No link available')
                    snippet = result.get('snippet', 'No description available')
            
                    st.write(f"**Title:** {title}")
                    st.write(f"**Link:** [View Resource]({link})")
                    st.write(f"**Description:** {snippet}")
                    st.write("---")
        else:
            st.error("Please enter a query.")

elif section == "Meeting Reminder":
    st.header("📅 Meeting Reminder")
    st.write("Set a reminder for your meeting.")
    name = st.text_input("Enter your name:")
    email = st.text_input("Enter your email:")
    meeting_description = st.text_area("Enter meeting description:")
    meeting_time = st.time_input("Choose a time for your meeting:")
    reminder_time = st.slider("Set reminder minutes before the meeting:", 5, 60, 15)

    if st.button("Set Reminder"):
        if name and email and meeting_description:
            meeting_datetime = datetime.combine(datetime.today(), meeting_time)
            reminder_datetime = meeting_datetime - timedelta(minutes=reminder_time)
        
            subject = "Meeting Reminder"
            body = (f"Hi {name},\n\nThis is a reminder for your meeting.\n\n"
                    f"Meeting Time: {meeting_time}\n"
                    f"Description: {meeting_description}\n\n"
                    f"You'll receive this reminder {reminder_time} minutes before the meeting.\n\n"
                    f"Best regards,\nYour Reminder Service")
        
            send_test_email(
                from_email="adarshprvt@gmail.com",
                to_email="adarsh.arvr@gmail.com",
                subject="Test Email",
                body="This is a test email."
            ) 
            st.success(f"Reminder set for {name} at {meeting_time}. You'll receive an email reminder {reminder_time} minutes before.")
        else:
            st.error("Please enter your name, email, and meeting description.")

elif section == "Lecture Enhancement":
    st.header("📝 Lecture Enhancement")
    st.write("Summarize your lecture notes.")
    lecture_notes = st.text_area("Enter lecture notes:")
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    if st.button("Summarize"):
        if lecture_notes:
            summary = summarizer(lecture_notes, max_length=150, min_length=30, do_sample=False)[0]['summary_text']
            st.write("Summary:", summary)
        else:
            st.error("Please enter lecture notes to summarize.")

elif section == "Automated Feedback System":
    st.header("📝 Automated Feedback System")
    st.write("Get feedback on your assignment.")
    assignment = st.text_area("Enter assignment text:")
    if st.button("Get Feedback"):
        if assignment:
            feedback = "Great job! Consider expanding your analysis in the third paragraph."
            st.write("Feedback:", feedback)
        else:
            st.error("Please enter assignment text to get feedback.")

elif section == "Language Learning Companion":
    st.header("🌐 Language Learning Companion")
    st.write("Translate your practice sentence.")
    translator_en_to_fr = pipeline("translation_en_to_fr", model="t5-small")
    translator_en_to_hi = pipeline("translation_en_to_hi", model="Helsinki-NLP/opus-mt-en-hi")
    translator_en_to_ml = pipeline("translation_en_to_ml", model="Helsinki-NLP/opus-mt-en-ml")
    language_input = st.text_input("Practice a sentence:")
    language = st.selectbox("Select language for translation:", ["French", "Hindi", "Malayalam"])

    if st.button("Get Translation"):
        if language_input:
            if language == "French":
                translation = translator_en_to_fr(language_input, max_length=400)[0]['translation_text']
            elif language == "Hindi":
                translation = translator_en_to_hi(language_input, max_length=400)[0]['translation_text']
            elif language == "Malayalam":
                translation = translator_en_to_ml(language_input, max_length=400)[0]['translation_text']
            st.write(f"Translation ({language}):", translation)
        else:
            st.error("Please enter a sentence to translate.")

elif section == "AI-BOT":
    st.header("💬 AI-BOT")

    # Initialize chat history if it doesn't exist
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []

    input_text = st.text_input("Input: ", key="input")
    submit = st.button("Ask the question")

    if submit and input_text:
        response = get_gemini_response(input_text)  # Ensure this function is correct
        st.session_state['chat_history'].append(("You", input_text))

        st.subheader("The Response is")
        for chunk in response:
            st.write(chunk.text)
            st.session_state['chat_history'].append(("AI-BOT", chunk.text))

    # Display the chat history
    for role, text in st.session_state['chat_history']:
        st.write(f"{role}: {text}")

elif section == "Lets Try Quizzz":
    st.header("Lets Try Quizzz")
    st.write("Generate assignments based on the topic and grade.")
    topic = st.text_input("Enter the topic:")
    grade = st.selectbox("Select the grade level:", [
        "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5",
        "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10",
        "Grade 11", "Grade 12"
    ])

    if st.button("Generate Assignments"):
        if topic and grade:
            quiz = generate_quiz_questions(topic, grade)
            if 'quiz_data' not in st.session_state:
                st.session_state['quiz_data'] = {'questions': quiz, 'user_answers': [""]*10}
            st.write("### Quiz Questions:")
            with st.form("quiz_form"):
                for i, q in enumerate(st.session_state['quiz_data']['questions']):
                    st.write(f"Q{i+1}: {q['question']}")
                    st.session_state['quiz_data']['user_answers'][i] = st.radio(f"Options for Q{i+1}", options=q['options'], key=f"question_{i}_option")
                submit_quiz = st.form_submit_button("Submit Quiz")
            
            if submit_quiz:
                correct_answers = 0
                total_questions = len(st.session_state['quiz_data']['questions'])
                performance_data = []
                
                for i, q in enumerate(st.session_state['quiz_data']['questions']):
                    user_answer = st.session_state['quiz_data']['user_answers'][i]
                    correct = user_answer == q['correct_answer']
                    if correct:
                        correct_answers += 1
                    performance_data.append({
                        'Question': f'Q{i+1}',
                        'Your Answer': user_answer,
                        'Correct Answer': q['correct_answer'],
                        'Correct': correct
                    })
                
                score = (correct_answers / total_questions) * 100
                st.write(f"Your score is: {score}%")
                
                # Display chat-like performance report
                st.write("### Performance Report:")
                for item in performance_data:
                    class_name = "correct" if item['Correct'] else "incorrect"
                    st.markdown(f"""
                        <div class="chat-bubble {class_name}">
                            <strong>{item['Question']}</strong><br>
                            Your Answer: {item['Your Answer']}<br>
                            Correct Answer: {item['Correct Answer']}
                        </div>
                    """, unsafe_allow_html=True)
                
                # Plot Performance Chart
                df = pd.DataFrame(performance_data)
                fig, ax = plt.subplots()
                colors = ['#4CAF50' if correct else '#f44336' for correct in df['Correct']]
                ax.bar(df['Question'], df['Correct'], color=colors)
                ax.set_ylabel('Correct (1) / Incorrect (0)')
                ax.set_title('Quiz Performance')
                st.pyplot(fig)


elif section == "Automated Assignment Generator":
    st.header("📝 Automated Assignment Generator")
    st.write("Generate multiple questions based on a topic.")
    topic = st.text_input("Enter the topic:")
    grade = st.selectbox("Select the grade level:", [
        "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5",
        "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10",
        "Grade 11", "Grade 12"
    ])

    if st.button("Generate Questions"):
        if topic and grade:
            quiz = generate_quiz_questions(topic, grade)
            st.session_state['quiz_data'] = {'questions': quiz}
            st.write("### Quiz Questions:")
            for i, q in enumerate(quiz):
                st.write(f"Q{i+1}: {q['question']}")
                st.session_state['quiz_data']['user_answers'] = ["" for _ in quiz]
        else:
            st.error("Please enter both topic and grade.")

    if 'quiz_data' in st.session_state:
        st.write("### Your Answers:")
        with st.form("answers_form"):
            for i, q in enumerate(st.session_state['quiz_data']['questions']):
                st.write(f"Q{i+1}: {q['question']}")
                st.session_state['quiz_data']['user_answers'][i] = st.text_area(f"Your Answer for Q{i+1}", key=f"answer_{i}")
            
            submit_answers = st.form_submit_button("Submit Answers")
            
            if submit_answers:
                # Option to either type answers or upload PDF
                option = st.radio("Select answer submission method:", ["Type Answers", "Upload PDF"])
                
                if option == "Type Answers":
                    # Generate a report for typed answers
                    st.write("### Typed Answer Report:")
                    answers_df = pd.DataFrame({
                        'Question': [q['question'] for q in st.session_state['quiz_data']['questions']],
                        'Student Answer': st.session_state['quiz_data']['user_answers'],
                        'Feedback': ["Pending"] * len(st.session_state['quiz_data']['user_answers'])
                    })
                    
                    # Generate a chart
                    plot_chart(answers_df, "Student Typed Answer Report")
                
                elif option == "Upload PDF":
                    st.write("Upload your PDF answers:")
                    pdf_file = st.file_uploader("Choose a PDF file", type="pdf")
                    
                    if pdf_file is not None:
                        # Process the PDF file
                        text = process_pdf(pdf_file)
                        st.session_state['uploaded_pdf_text'] = text
                        st.success("PDF uploaded and processed successfully.")
                        
                        # Get feedback from LLM
                        query = f"Check the following answers and provide feedback: {text}"
                        response = get_gemini_response(query)
                        feedback = "".join([chunk.text for chunk in response])
                        
                        st.write("### Feedback:")
                        st.write(feedback)
                        
                        # Generate report
                        st.write("### Answer Report:")
                        answers_df = pd.DataFrame({
                            'Question': [q['question'] for q in st.session_state['quiz_data']['questions']],
                            'Student Answer': [text] * len(st.session_state['quiz_data']['questions']),
                            'Feedback': [feedback] * len(st.session_state['quiz_data']['questions'])
                        })
                        
                        # Generate a chart
                        plot_chart(answers_df, "Student PDF Answer Report")


elif section == " Voice Assistant":
    st.title("🎤 Voice Assistant")

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
        engine.say(response)
        engine.runAndWait()

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


                        
else:
    st.write("Select a section from the sidebar.")

