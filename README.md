# AI-Powered Adaptive Learning Platform

## Description

The AI-Powered Adaptive Learning Platform is a comprehensive tool designed to enhance educational experiences using advanced AI technologies. It integrates multiple features such as educational content search, meeting reminders, lecture enhancements, automated feedback, language translation, and quiz generation.

## Features

- **Educational Content Finder**: Search for YouTube videos and Google resources based on grade level and query.
- **Meeting Reminder**: Schedule and receive email reminders for meetings.
- **Lecture Enhancement**: Summarize lecture notes using state-of-the-art summarization models.
- **Automated Feedback System**: Get feedback on your assignments.
- **Language Learning Companion**: Translate sentences into French, Hindi, and Malayalam.
- **AI-BOT**: Interact with a chatbot using Google Gemini for real-time responses.
- **Automated Assignment Generator**: Generate quiz questions and assess performance.

## Installation

To set up the project locally, follow these steps:

1. **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/your-repository.git
    cd your-repository
    ```

2. **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    ```

3. **Activate the Virtual Environment:**
    - On Windows:
        ```bash
        venv\Scripts\activate
        ```
    - On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

4. **Install Required Packages:**
    ```bash
    pip install -r requirements.txt
    ```

5. **Set Up Environment Variables:**

    Create a `.env` file in the root directory and add your API keys and email credentials:
    ```ini
    YOUTUBE_API_KEY=your_youtube_api_key
    SERPER_API_KEY=your_serper_api_key
    GOOGLE_API_KEY=your_google_api_key
    EMAIL_PASSWORD=your_email_password
    EMAIL_ADDRESS=your_email_address
    ```

6. **Run the Application:**
    ```bash
    streamlit run app.py
    ```

## Usage

Navigate to the Streamlit app running in your browser to interact with the various features of the platform. You can:

- Search for educational content using the provided input fields.
- Set reminders for meetings and receive email notifications.
- Summarize lecture notes and receive automated feedback on assignments.
- Translate sentences into different languages.
- Interact with the AI-BOT for answers to your questions.
- Generate and assess quiz questions for different topics and grades.

## Contributing

Contributions are welcome! If you have suggestions or improvements, please fork the repository and submit a pull request. 

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Special thanks to the developers of the various libraries and APIs used in this project.

