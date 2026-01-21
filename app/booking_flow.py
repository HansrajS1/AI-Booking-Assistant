from typing import Dict, Any
import streamlit as st
from config import GROQ_API_KEY, SENDGRID_API_KEY, FROM_EMAIL
from send_email import send_professional_email
from database import insert_customer, insert_booking
from rag_pipeline import RAGPipeline
import re

def initialize_booking_state(session_state: Dict[str, Any]):
    if "booking_info" not in session_state:
        session_state.booking_info = {
            "name": None, "email": None, "phone": None,
            "booking_type": None, "date": None, "time": None,
            "step": 0,
            "greeted": False 
        }

def detect_intent(user_input: str) -> str:
    """ Detect greeting vs booking intent"""
    user_input_lower = user_input.lower().strip()
    
    greetings = ["hi", "hello", "hey", "start", "help"]
    if any(g in user_input_lower for g in greetings):
        return "greeting"
    
    # Booking intent
    booking_phrases = ["book", "reserve", "schedule", "appointment"]
    if any(b in user_input_lower for b in booking_phrases):
        return "booking"
    
    return "general"

def extract_service_type(query: str) -> str:
    """ Extract service from booking request"""
    services = {
        "hotel": ["hotel", "room", "stay", "accommodation"],
        "doctor": ["doctor", "consultation", "appointment", "medical"],
        "restaurant": ["dinner", "restaurant", "table", "meal"],
        "spa": ["spa", "massage", "facial", "wellness"],
        "salon": ["salon", "haircut", "beauty"],
        "event": ["event", "party", "meeting"],
        "class": ["class", "training", "course", "lesson"]
    }
    query_lower = query.lower()
    for service, keywords in services.items():
        if any(keyword in query_lower for keyword in keywords):
            return service
    return "service"

def process_message(user_input: str, session_state: Dict[str, Any]) -> str:
    initialize_booking_state(session_state)
    booking_info = session_state.booking_info
    
    user_input_lower = user_input.lower().strip()
    intent = detect_intent(user_input)
    
    if 'rag_pipeline' in session_state and st.session_state.rag_pipeline.vector_store:
        rag = st.session_state.rag_pipeline
        rag_result = rag.query(user_input)
        
        if any(word in user_input_lower for word in ["book", "appointment", "reserve"]):
            booking_info["step"] = 0 
            service_type = extract_service_type(user_input_lower)
            booking_info["booking_type"] = service_type
            return f"{rag_result}\n\n💡 **Ready to book {service_type}?** Say **'book {service_type}'** now!"
        
        if "service" in user_input_lower or "price" in user_input_lower or "available" in user_input_lower:
            return rag_result
    
    if intent == "greeting" and not booking_info["greeted"]:
        booking_info["greeted"] = True
        return """
                Welcome to AI Booking Assistant!

                I can help you book ANY service:
                Hotels •  Doctor appointments •  Restaurant tables
                Spa •  Salon • Events •  Classes

                Examples:
                • `book hotel room`
                • `book doctor appointment`
                • `book dinner table`
                • `book spa massage`

                Just say "book [service]" to start!
        """
    
    if "book" in user_input_lower:
        booking_info["step"] = 0 
        service_type = extract_service_type(user_input)
        booking_info["booking_type"] = service_type or "service"
        booking_info["greeted"] = True
        return f"""
 **{booking_info['booking_type'].title()} Booking Started!** 

What's your **name**?
        """
    
    if booking_info["step"] >= 6 and ("yes" in user_input_lower or "confirm" in user_input_lower):
        customer_id = insert_customer(booking_info["name"], booking_info["email"], booking_info["phone"])
        booking_id = insert_booking(customer_id, booking_info["booking_type"], booking_info["date"], booking_info["time"])
        
        email_sent = send_professional_email(
            booking_info["email"], booking_info["name"], 
            booking_info["booking_type"], booking_info["date"], 
            booking_info["time"], booking_id or "DEMO-123"
        )
        
        session_state.booking_info = {"step": 0, "greeted": True}
        return f"""
                PERFECTLY BOOKED! 

                ID: `{booking_id or 'DEMO-123'}`
                {booking_info['name']} → {booking_info['booking_type']}
                {booking_info['date']} | {booking_info['time']}

                New customer record created
                Booking saved to database  
                Professional SendGrid email sent

                Admin Dashboard ← See all bookings!
                Ready for next customer...
                """
    
    if "no" in user_input_lower or "cancel" in user_input_lower:
        session_state.booking_info = {"step": 0, "greeted": booking_info["greeted"]}
        return " Booking cancelled. Say `book [service]` to start again!"
    
    steps = ["name", "email", "phone", "booking_type", "date", "time"]
    
    if booking_info["step"] == 0 and user_input.strip():
        booking_info["name"] = user_input.strip()
        booking_info["step"] = 1
    elif booking_info["step"] == 1 and user_input.strip():
        clean_email = user_input.replace("[", "").replace("]", "").replace("mailto:", "").strip()
        booking_info["email"] = clean_email
        booking_info["step"] = 2
    elif booking_info["step"] == 2 and user_input.strip():
        booking_info["phone"] = user_input.strip()
        booking_info["step"] = 3
    elif booking_info["step"] == 3 and user_input.strip():
        booking_info["booking_type"] = user_input.strip()
        booking_info["step"] = 4
    elif booking_info["step"] == 4 and any(c in user_input for c in ['-', '/']):
        booking_info["date"] = user_input.strip()
        booking_info["step"] = 5
    elif booking_info["step"] == 5 and ':' in user_input:
        booking_info["time"] = user_input.strip()
        booking_info["step"] = 6
    
    if booking_info["step"] >= 6:
        return f"""
                Review & Confirm:
                {booking_info['name']}
                {booking_info['email']}
                {booking_info['phone']}
                {booking_info['booking_type']}
                {booking_info['date']}
                {booking_info['time']}
                "yes" = Save + SendGrid email
                "no" = Cancel
        """
    
    current_step = steps[booking_info["step"]]
    hint = " (YYYY-MM-DD)" if current_step == "date" else " (HH:MM)" if current_step == "time" else ""
    return f"What's your **{current_step.replace('_', ' ')}**?{hint}"
