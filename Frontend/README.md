# MediChat AI: Medical Information Chatbot

A Streamlit-based medical chatbot application with authentication, chat functionality, admin panel, and feedback management.

## Features

- **User Authentication**: Secure sign-up and login system
- **Medical Chatbot**: Query the AI assistant for medical information
- **Chat History**: Review past conversations and continue where you left off
- **Admin Panel**: Manage users, view system statistics, and analyze feedback
- **Feedback System**: Collect and manage user feedback
- **LLM Thinking Process**: View the AI's reasoning behind responses

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd medichat-ai
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the root directory
   - Add your API keys and configuration (see `.env.example`)

4. Run the application:
   ```
   streamlit run app.py
   ```

## Project Structure

```
.
├── app.py                      # Main application entry point
├── auth/                       # Authentication functionality
│   └── authentication.py       # Login and signup handling
├── chat/                       # Chat functionality
│   ├── chat_interface.py       # Main chat UI and logic
│   └── history.py              # Chat history display
├── admin/                      # Admin panel
│   └── admin_panel.py          # User management and statistics
├── feedback/                   # Feedback system
│   └── feedback_management.py  # Feedback collection and display
├── utils/                      # Utility functions
│   ├── database.py             # Database operations
│   ├── session.py              # Session state management
│   └── styles.py               # Custom styling
├── requirements.txt            # Project dependencies
└── .env                        # Environment variables
```

## Usage

### Regular Users
1. Create an account or log in
2. Use the chat interface to ask medical questions
3. View your chat history
4. Provide feedback on responses

### Admin Users
1. Log in with admin credentials
2. Manage user roles and permissions
3. View system statistics
4. Analyze user feedback

## Default Admin Account
- Username: admin
- Password: admin123

## Dependencies

- streamlit
- streamlit-extras
- streamlit-option-menu
- streamlit-chat
- bcrypt
- pandas
- openai
- plotly
- python-dotenv

## License

This project is licensed under the MIT License - see the LICENSE file for details.