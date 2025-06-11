import streamlit as st

def apply_custom_styles():

    print("Applying custom styles to the application")
    """Apply custom CSS styles to the application."""
    
    # Custom CSS for the application
    st.markdown("""
    <style>
        /* Main theme colors */
        :root {
            --primary-color: #1565C0;
            --secondary-color: #26A69A;
            --accent-color: #FF8A65;
            --background-color: #F5F7F9;
            --card-background: #FFFFFF;
            --text-color: #333333;
            --muted-text: #718096;
            --success-color: #4CAF50;
            --warning-color: #FFC107;
            --error-color: #E53935;
        }
        
        /* Global styles */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-color);
            font-weight: 600;
            letter-spacing: -0.02em;
        }
        
        /* Card styles */
        .stCard {
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            padding: 1.5rem;
            background-color: var(--card-background);
            margin-bottom: 1rem;
            border: 1px solid rgba(0, 0, 0, 0.05);
            transition: all 0.2s ease;
        }
        
        .stCard:hover {
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.08);
            transform: translateY(-2px);
        }
        
        /* Button styles */
        .stButton button {
            border-radius: 4px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .stButton button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        
        /* Chat message styles */
        .user-message {
            background-color: var(--primary-color);
            color: white;
            border-radius: 18px 18px 4px 18px;
            padding: 10px 16px;
            margin: 8px 0;
            max-width: 80%;
            align-self: flex-end;
            animation: fadeIn 0.3s ease;
        }
        
        .ai-message {
            background-color: #f0f2f5;
            color: var(--text-color);
            border-radius: 18px 18px 18px 4px;
            padding: 10px 16px;
            margin: 8px 0;
            max-width: 80%;
            align-self: flex-start;
            animation: fadeIn 0.3s ease;
        }
        
        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Admin panel styles */
        .metric-card {
            background-color: var(--card-background);
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            text-align: center;
            border-left: 4px solid var(--primary-color);
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
        
        /* Feedback styles */
        .feedback-card {
            border-left: 4px solid var(--secondary-color);
            padding: 1rem;
            margin-bottom: 1rem;
            background-color: var(--card-background);
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        
        /* Mobile responsiveness */
        @media (max-width: 768px) {
            .main .block-container {
                padding-top: 1rem;
                padding-bottom: 1rem;
            }
            
            .user-message, .ai-message {
                max-width: 90%;
            }
        }
    </style>
    """, unsafe_allow_html=True)