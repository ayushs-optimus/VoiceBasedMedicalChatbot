import streamlit as st

def apply_custom_styles():
    """Apply custom CSS styles to the application with dark/light mode support."""
    
    st.markdown("""
    <style>
        /* CSS Variables for Light and Dark Mode */
        :root {
            --primary-color: #1565C0;
            --secondary-color: #26A69A;
            --accent-color: #FF8A65;
            --success-color: #4CAF50;
            --warning-color: #FFC107;
            --error-color: #E53935;
        }
        
        /* Light mode variables */
        [data-theme="light"] {
            --background-color: #F5F7F9;
            --card-background: #FFFFFF;
            --text-color: #333333;
            --muted-text: #718096;
            --input-background: #FFFFFF;
            --input-border: #e0e0e0;
            --chat-user-bg: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --chat-ai-bg: #f8f9fa;
            --chat-ai-border: #e9ecef;
            --chat-ai-text: #333333;
            --sidebar-bg: #f8f9fa;
            --shadow-light: rgba(0, 0, 0, 0.05);
            --shadow-medium: rgba(0, 0, 0, 0.1);
        }
        
        /* Dark mode variables */
        [data-theme="dark"] {
            --background-color: #0E1117;
            --card-background: #1E1E1E;
            --text-color: #FAFAFA;
            --muted-text: #A0A0A0;
            --input-background: #2D2D2D;
            --input-border: #555555;
            --chat-user-bg: linear-gradient(135deg, #4455aa 0%, #5522aa 100%);
            --chat-ai-bg: #2a2a2a;
            --chat-ai-border: #404040;
            --chat-ai-text: #f1f1f1;
            --sidebar-bg: #1E1E1E;
            --shadow-light: rgba(255, 255, 255, 0.05);
            --shadow-medium: rgba(255, 255, 255, 0.1);
        }
        
        /* Auto-detect system theme */
        @media (prefers-color-scheme: dark) {
            :root {
                --background-color: #0E1117;
                --card-background: #1E1E1E;
                --text-color: #FAFAFA;
                --muted-text: #A0A0A0;
                --input-background: #2D2D2D;
                --input-border: #555555;
                --chat-user-bg: linear-gradient(135deg, #4455aa 0%, #5522aa 100%);
                --chat-ai-bg: #2a2a2a;
                --chat-ai-border: #404040;
                --chat-ai-text: #f1f1f1;
                --sidebar-bg: #1E1E1E;
                --shadow-light: rgba(255, 255, 255, 0.05);
                --shadow-medium: rgba(255, 255, 255, 0.1);
            }
        }
        
        @media (prefers-color-scheme: light) {
            :root {
                --background-color: #F5F7F9;
                --card-background: #FFFFFF;
                --text-color: #333333;
                --muted-text: #718096;
                --input-background: #FFFFFF;
                --input-border: #e0e0e0;
                --chat-user-bg: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                --chat-ai-bg: #f8f9fa;
                --chat-ai-border: #e9ecef;
                --chat-ai-text: #333333;
                --sidebar-bg: #f8f9fa;
                --shadow-light: rgba(0, 0, 0, 0.05);
                --shadow-medium: rgba(0, 0, 0, 0.1);
            }
        }
        
        /* Global Application Styles */
        .stApp > div {
            padding-top: 2rem;
        }
        
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-color);
            font-weight: 600;
            letter-spacing: -0.02em;
        }
        
        /* User Avatar Styling */
        .circular-image {
            border-radius: 50%;
            width: 150px;
            height: 150px;
            object-fit: cover;
            border: 3px solid var(--primary-color);
            box-shadow: 0 4px 12px var(--shadow-medium);
            transition: all 0.3s ease;
            display: block;
            margin: 0 auto 1rem auto;
        }
        
        .circular-image:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 20px var(--shadow-medium);
        }
        
        /* Card Styles */
        .stCard {
            border-radius: 12px;
            box-shadow: 0 4px 6px var(--shadow-light);
            padding: 1.5rem;
            background-color: var(--card-background);
            margin-bottom: 1rem;
            border: 1px solid var(--input-border);
            transition: all 0.2s ease;
        }
        
        .stCard:hover {
            box-shadow: 0 8px 15px var(--shadow-medium);
            transform: translateY(-2px);
        }
        
        /* Button Styles */
        .stButton button {
            border-radius: 10px;
            font-weight: 500;
            transition: all 0.2s ease;
            border: none;
            color: white;
            height: 42px;
        }
        
        .stButton button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px var(--shadow-medium);
        }
        
        /* Primary buttons */
        .stButton button[kind="primary"] {
            background: var(--chat-user-bg);
        }
        
        /* Input Styles */
        .stTextInput > div > div > input {
            border-radius: 10px;
            border: 2px solid var(--input-border);
            padding: 10px 15px;
            font-size: 16px;
            background-color: var(--input-background);
            color: var(--text-color);
            transition: all 0.2s ease;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 2px rgba(21, 101, 192, 0.2);
        }
        
        /* Chat Message Styles */
        .chat-container {
            height: 65vh;
            overflow-y: auto;
            padding: 1rem;
            padding-bottom: 6rem; /* space for input box */
            border-radius: 10px;
            background-color: var(--background-color);
        }

        
        .user-message {
            display: flex;
            justify-content: flex-end;
            margin-bottom: 1rem;
        }
        
        .user-message > div {
            background: var(--chat-user-bg);
            color: white;
            padding: 12px 16px;
            border-radius: 18px 18px 4px 18px;
            max-width: 70%;
            word-wrap: break-word;
            box-shadow: 0 2px 8px var(--shadow-medium);
            animation: fadeIn 0.3s ease;
        }
        
        .ai-message {
            display: flex;
            justify-content: flex-start;
            margin-bottom: 1rem;
        }
        
        .ai-message > div {
            background-color: var(--chat-ai-bg);
            color: var(--chat-ai-text);
            border: 1px solid var(--chat-ai-border);
            padding: 12px 16px;
            border-radius: 18px 18px 18px 4px;
            max-width: 70%;
            word-wrap: break-word;
            box-shadow: 0 2px 8px var(--shadow-light);
            animation: fadeIn 0.3s ease;
        }
        
        /* Typing Indicator */
        .typing {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            border-radius: 18px 18px 18px 4px;
            background-color: var(--chat-ai-bg);
            border: 1px solid var(--chat-ai-border);
            max-width: 70%;
            color: var(--muted-text);
            font-style: italic;
            animation: fadeIn 0.3s ease;
        }

        .typing span {
            height: 8px;
            width: 8px;
            margin-right: 5px;
            background-color: var(--muted-text);
            border-radius: 50%;
            display: inline-block;
            animation: blink 1.4s infinite;
        }

        .typing span:nth-child(2) {
            animation-delay: 0.2s;
        }

        .typing span:nth-child(3) {
            animation-delay: 0.4s;
        }

        @keyframes blink {
            0%, 100% { opacity: 0.2; }
            50% { opacity: 1; }
        }

        
        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Admin Panel Styles */
        .metric-card {
            background-color: var(--card-background);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px var(--shadow-light);
            text-align: center;
            border-left: 4px solid var(--primary-color);
            transition: all 0.2s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 15px var(--shadow-medium);
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-color);
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: var(--muted-text);
            margin-top: 0.5rem;
        }
        
        /* Feedback Styles */
        .feedback-card {
            border-left: 4px solid var(--secondary-color);
            padding: 1.5rem;
            margin-bottom: 1rem;
            background-color: var(--card-background);
            border-radius: 8px;
            box-shadow: 0 4px 6px var(--shadow-light);
            transition: all 0.2s ease;
        }
        
        .feedback-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 12px var(--shadow-medium);
        }
        
        /* Sidebar Styles */
        .css-1d391kg {
            background-color: var(--sidebar-bg);
        }
        
        /* Fixed input area */
        .input-container {
            position: sticky;
            bottom: 0;
            background-color: var(--background-color);
            padding: 1rem 0;
            border-top: 1px solid var(--input-border);
            z-index: 100;
        }
        
        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 6px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--background-color);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--muted-text);
            border-radius: 3px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--primary-color);
        }
        
        /* Mobile Responsiveness */
        @media (max-width: 768px) {
            .main .block-container {
                padding-top: 1rem;
                padding-bottom: 1rem;
            }
            
            .user-message > div,
            .ai-message > div {
                max-width: 90%;
            }
            
            .circular-image {
                width: 100px;
                height: 100px;
            }
            
            .chat-container {
                height: 50vh;
            }
        }
        
        /* Remove bottom margin for last element */
        .element-container:last-child {
            margin-bottom: 100px;
        }
        
        /* Welcome message styling */
        .welcome-message {
            text-align: center;
            color: var(--muted-text);
            margin: 2rem 0;
            padding: 2rem;
            background-color: var(--card-background);
            border-radius: 12px;
            border: 1px solid var(--input-border);
        }
        .fixed-input {
            position: fixed;
            bottom: 0;
            left: 16rem; /* offset for sidebar */
            right: 1rem;
            background-color: var(--card-background);
            padding: 10px 20px;
            border-top: 1px solid var(--input-border);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 10px;
            border-radius: 1rem;
            box-shadow: 0 -2px 6px var(--shadow-light);
        }

        .stTextInput input {
            background-color: var(--input-background);
            color: var(--text-color);
            padding: 10px 16px;
            border-radius: 999px;
            border: 2px solid var(--input-border);
            width: 100%;
        }

    </style>
    """, unsafe_allow_html=True)