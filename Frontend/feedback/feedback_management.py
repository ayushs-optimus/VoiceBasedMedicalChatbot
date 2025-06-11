import streamlit as st
import pandas as pd
import requests

def save_feedback_to_backend(user_id, message_id, rating, comment):
    try:
        payload = {
            "user_id": user_id,
            "message_id": message_id,
            "rating": rating,
            "comment": comment
        }
        response = requests.post("http://localhost:8000/api/feedback", json=payload)  # Adjust for your backend URL
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Failed to submit feedback: {e}")
        return False
def get_user_feedback_from_backend(user_name):
    try:
        response = requests.get(f"http://localhost:8000/api/feedback?user_name={user_name}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch feedback: {e}")
        return []
def view_user_feedback():
    st.header("Your Previous Feedback")
    
    feedback_data = get_user_feedback_from_backend(st.session_state.user_name)
    
    if not feedback_data:
        st.info("You haven't provided any feedback yet.")
        return
    
    for feedback in feedback_data:
        rating = feedback["rating"]
        created_at = feedback["created_at"]
        comment = feedback.get("comment", "")
        message_preview = feedback.get("message_content", "General Feedback")
        
        if message_preview and len(message_preview) > 50:
            message_preview = message_preview[:50] + "..."
        
        stars = "⭐" * rating
        
        st.markdown(f"""
        <div class="feedback-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>{stars} ({rating}/5)</div>
                <div style="color: #718096; font-size: 0.8rem;">{created_at}</div>
            </div>
            <div style="margin-top: 8px; font-style: italic; color: #4A5568;">
                "{message_preview}"
            </div>
            <div style="margin-top: 8px;">
                {comment}
            </div>
        </div>
        """, unsafe_allow_html=True)

def provide_feedback():
    
    st.header("We Value Your Feedback")
    st.write("Your feedback helps us improve our medical chatbot experience.")
    
    with st.form(key="feedback_form"):
        rating = st.slider("Rate MediChat AI:", min_value=1, max_value=5, value=5)
        
        col1, col2 = st.columns(2)
        with col1:
            accuracy = st.checkbox("Answer Accuracy")
            relevance = st.checkbox("Response Relevance")
            speed = st.checkbox("Response Speed")
        with col2:
            usability = st.checkbox("Usability/Interface")
            features = st.checkbox("Features")
            other = st.checkbox("Other")
        
        feedback_text = st.text_area("Detailed Feedback:", height=150)
        improvements = st.text_area("Suggestions for Improvement:", height=100)
        submit_button = st.form_submit_button("Submit Feedback", use_container_width=True)
        
        if submit_button:
            if not feedback_text:
                st.error("Please provide some feedback text.")
            else:
                categories = []
                if accuracy: categories.append("Accuracy")
                if relevance: categories.append("Relevance")
                if speed: categories.append("Speed")
                if usability: categories.append("Usability")
                if features: categories.append("Features")
                if other: categories.append("Other")
                
                comment = f"""
                Categories: {', '.join(categories)}
                Feedback: {feedback_text}
                Improvements: {improvements}
                """
                
                success = save_feedback_to_backend(st.session_state.user_id, 0, rating, comment)
                if success:
                    st.success("Thank you for your feedback!")
                    st.balloons()

    """Display user's previous feedback"""
    st.header("Your Previous Feedback")
    
    # Get all feedback from database
    all_feedback = get_all_feedback()
    
    # Filter feedback for current user
    user_feedback = [f for f in all_feedback if f["username"] == st.session_state.user_name]
    
    if not user_feedback:
        st.info("You haven't provided any feedback yet.")
        return
    
    # Display feedback
    for i, feedback in enumerate(user_feedback):
        # Extract data
        rating = feedback["rating"]
        created_at = feedback["created_at"]
        
        # Format comment display
        comment = feedback.get("comment", "")
        message_preview = feedback.get("message_content", "General Feedback")
        if message_preview and len(message_preview) > 50:
            message_preview = message_preview[:50] + "..."
        
        # Create star rating display
        stars = "⭐" * rating
        
        # Create feedback card
        st.markdown(f"""
        <div class="feedback-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>{stars} ({rating}/5)</div>
                <div style="color: #718096; font-size: 0.8rem;">{created_at}</div>
            </div>
            <div style="margin-top: 8px; font-style: italic; color: #4A5568;">
                "{message_preview}"
            </div>
            <div style="margin-top: 8px;">
                {comment}
            </div>
        </div>
        """, unsafe_allow_html=True)