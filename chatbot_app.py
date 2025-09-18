import sqlite3
import os
import datetime
import re
from flask import Flask, render_template_string, request, jsonify

# --- Project Configuration ---
# This is a self-contained application. The HTML template is defined as a string below.
# The database will be created in the same directory as this script.
DATABASE = 'chatbot_logs.db'

# --- HTML/CSS Template for the Chat Interface ---
# This is an all-in-one template to keep the project in a single file.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-Powered Chatbot</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f3f4f6;
        }
        .chat-container {
            max-height: 80vh;
            overflow-y: auto;
            display: flex;
            flex-direction: column-reverse; /* To show new messages at the bottom */
        }
        .message {
            max-width: 80%;
            padding: 1rem;
            border-radius: 1.5rem;
            margin-bottom: 0.75rem;
            line-height: 1.5;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
            animation: slideInFromTop 0.3s ease-out forwards;
        }
        .user-message {
            background-color: #3b82f6;
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 0.5rem;
        }
        .bot-message {
            background-color: #ffffff;
            color: #1f2937;
            align-self: flex-start;
            border-bottom-left-radius: 0.5rem;
        }
        @keyframes slideInFromTop {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    </style>
</head>
<body class="bg-gray-100 flex items-center justify-center min-h-screen p-4">
    <div class="bg-white rounded-3xl shadow-xl w-full max-w-2xl flex flex-col h-[90vh]">
        <div class="p-6 bg-blue-600 text-white rounded-t-3xl shadow-lg">
            <h1 class="text-2xl font-bold">AI-Powered Chatbot (Multilingual)</h1>
            <p class="text-sm opacity-80 mt-1">Ask me anything! (मला काहीही विचारा!)</p>
        </div>
        <div id="chat-box" class="flex-grow p-6 space-y-4 chat-container">
            <!-- Messages will be injected here by JavaScript -->
        </div>
        <form id="chat-form" class="p-6 border-t border-gray-200 bg-white rounded-b-3xl">
            <div class="flex items-center space-x-4">
                <input type="text" id="user-input" placeholder="Type your message... (तुमचा संदेश टाइप करा...)" class="flex-grow p-4 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200">
                <button type="submit" class="bg-blue-600 text-white p-4 rounded-full shadow-lg hover:bg-blue-700 transition-all duration-200">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5l7 7-7 7" />
                    </svg>
                </button>
            </div>
        </form>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const chatForm = document.getElementById('chat-form');
            const userInput = document.getElementById('user-input');
            const chatBox = document.getElementById('chat-box');

            // Function to add a message to the chat interface
            function addMessage(sender, message) {
                const messageElement = document.createElement('div');
                messageElement.classList.add('message');
                if (sender === 'user') {
                    messageElement.classList.add('user-message', 'self-end');
                } else {
                    messageElement.classList.add('bot-message', 'self-start');
                }
                messageElement.textContent = message;
                chatBox.prepend(messageElement); // Use prepend to add messages at the top
            }

            // Function to handle form submission
            chatForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const message = userInput.value.trim();
                if (message === '') {
                    return;
                }

                addMessage('user', message);
                userInput.value = ''; // Clear input field

                // Send message to the backend
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ message: message }),
                    });

                    const data = await response.json();
                    addMessage('bot', data.response);
                } catch (error) {
                    console.error('Error:', error);
                    addMessage('bot', 'Sorry, something went wrong. Please try again.');
                }
            });
        });
    </script>
</body>
</html>
"""

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Database Setup ---
def init_db():
    """Initializes the SQLite database and creates the logs table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# --- Chatbot Logic (Advanced) ---
def get_bot_response(user_message):
    """
    This is an improved chatbot logic using more robust keyword matching.
    
    For a truly advanced version, you would replace this entire function with
    code that integrates with an NLP library or a pre-trained model.
    
    Example with an NLP library (uncomment and install libraries to use):
    # from transformers import pipeline
    # nlp_model = pipeline("text-generation", model="gpt2")
    # You would then process the user message with this model to get a response.
    # return nlp_model(user_message)[0]['generated_text']
    """
    user_message = user_message.lower()

    # Define a dictionary of keywords and their corresponding responses
    RESPONSES = {
        ("hello", "hi", "नमस्कार", "कसा आहेस"): "Hello there! How can I assist you today? (नमस्कार! मी तुम्हाला कशी मदत करू शकतो?)",
        ("how are you", "कसा आहेस"): "I'm a bot, so I'm doing great! Thanks for asking. (मी ठीक आहे, विचारल्याबद्दल धन्यवाद!)",
        ("help", "मदत"): "I can help with basic inquiries. Try asking about my purpose or capabilities. (मी तुम्हाला काही मूलभूत प्रश्नांची उत्तरे देऊ शकतो. माझ्या उद्देश किंवा क्षमतेबद्दल विचारून पहा.)",
        ("purpose", "capabilities", "work", "उद्देश", "क्षमता"): "I am a simple chatbot designed to demonstrate a basic web application with a Flask backend and SQLite logging. (मी एक साधा चॅटबॉट आहे जो फ्लास्क बॅकएंड आणि SQLite लॉगिंगसह एक वेब ॲप्लिकेशन दर्शविण्यासाठी डिझाइन केला आहे.)",
        ("goodbye", "bye", "पुन्हा भेटू"): "Goodbye! Feel free to return if you have more questions. (पुन्हा भेटू! तुम्हाला आणखी काही प्रश्न असल्यास, नक्की परत या.)",
        ("name", "what's your name", "what is your name", "नाव", "तुमचं नाव काय आहे"): "I don't have a name, but you can call me Chatbot. (माझे काही नाव नाही, पण तुम्ही मला चॅटबॉट म्हणू शकता.)",
        ("date", "today's date", "आजची तारीख", "तारीख"): f"Today's date is: {datetime.date.today().strftime('%B %d, %Y')}. (आजची तारीख आहे: {datetime.date.today().strftime('%B %d, %Y')})",
        
    }
    
    # Use regular expressions to check for keywords, allowing for more flexible matching
    if re.search(r'\b(work|do)\b.*\b(you)\b', user_message) or re.search(r'काय काम करतो', user_message):
        return "I am a simple chatbot designed to demonstrate a basic web application with a Flask backend and SQLite logging. (मी एक साधा चॅटबॉट आहे जो फ्लास्क बॅकएंड आणि SQLite लॉगिंगसह एक वेब ॲप्लिकेशन दर्शविण्यासाठी डिझाइन केला आहे.)"
    
    # Check for keywords in the user's message
    for keywords, response in RESPONSES.items():
        if any(keyword in user_message for keyword in keywords):
            return response
    
    return "I'm sorry, I don't understand that. Can you please rephrase? (माफ करा, मला समजले नाही. कृपया पुन्हा सांगा.)"

# --- Flask Routes ---
@app.route('/')
def index():
    """Serves the main HTML page for the chatbot."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    """Handles chat messages, gets a response, and logs the interaction."""
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    bot_response = get_bot_response(user_message)

    # Log the interaction to the database
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO conversations (user_message, bot_response) VALUES (?, ?)',
        (user_message, bot_response)
    )
    conn.commit()
    conn.close()

    return jsonify({"response": bot_response})

if __name__ == '__main__':
    # Initialize the database on startup
    init_db()
    # Run the Flask application
    app.run(debug=True)
