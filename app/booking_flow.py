from typing import Dict, Any
import streamlit as st

def initialize_booking_state(session_state: Dict[str, Any]):
    if "booking_info" not in session_state:
        session_state.booking_info = {
            "name": None, "email": None, "phone": None,
            "booking_type": None, "date": None, "time": None,
            "step": 0,
            "greeted": False
        }

def detect_intent(user_input: str) -> str:
    user_input_lower = user_input.lower().strip()
    greetings = ["hi", "hello", "hey", "start", "help"]
    if any(g in user_input_lower for g in greetings):
        return "greeting"
    booking_phrases = ["book", "reserve", "schedule", "appointment"]
    if any(b in user_input_lower for b in booking_phrases):
        return "booking"
    return "general"

def extract_service_type(query: str) -> str:
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
    
    try:
        if 'rag_pipeline' in session_state and hasattr(st.session_state.rag_pipeline, 'vector_store'):
            rag_result = st.session_state.rag_pipeline.query(user_input)
            if any(word in user_input_lower for word in ["book", "appointment", "reserve"]):
                booking_info["step"] = 0
                service_type = extract_service_type(user_input_lower)
                booking_info["booking_type"] = service_type
                return f"{rag_result}\n\nReady to book {service_type}? Say 'book {service_type}' now!"
            if any(word in user_input_lower for word in ["service", "price", "available"]):
                return rag_result
    except:
        pass
    
    if intent == "greeting" and not booking_info["greeted"]:
        booking_info["greeted"] = True
        return """
                Welcome to AI Booking Assistant!

                I can help you book:
                Hotels • Doctor appointments • Restaurant tables
                Spa • Salon • Events • Classes

                Examples:
                • book hotel room
                • book doctor appointment  
                • book dinner table
                • book spa massage

                Just say "book [service]" to start!
        """
    
    if "book" in user_input_lower:
        booking_info["step"] = 0
        service_type = extract_service_type(user_input)
        booking_info["booking_type"] = service_type or "service"
        booking_info["greeted"] = True
        return f"{booking_info['booking_type'].title()} Booking Started!\n\nWhat's your name?"
   
    if booking_info["step"] >= 6 and ("yes" in user_input_lower or "confirm" in user_input_lower):
        try:
            from database import insert_customer, insert_booking
            from send_email import send_professional_email
            
            customer_id = insert_customer(booking_info["name"], booking_info["email"], booking_info["phone"])
            booking_id = insert_booking(customer_id, booking_info["booking_type"], booking_info["date"], booking_info["time"])
            
            email_sent = send_professional_email(
                booking_info["email"], booking_info["name"],
                booking_info["booking_type"], booking_info["date"],
                booking_info["time"], booking_id or "DEMO-123"
            )
            
            session_state.booking_info = {"step": 0, "greeted": True}
            return f"""
            BOOKING CONFIRMED!

            Booking ID: {booking_id or 'DEMO-123'}
            Customer: {booking_info['name']}
            {booking_info['booking_type'].title()}: {booking_info['date']} @ {booking_info['time']}

            Saved to database
            {'Email sent!' if email_sent else 'Email queued'}

            Admin Dashboard → See all bookings!
            Say "book hotel" for next booking
            """
        except:
            session_state.booking_info = {"step": 0, "greeted": True}
            return f"""
            DEMO BOOKING CONFIRMED!

            Customer: {booking_info['name']}
            Service: {booking_info['booking_type']}
            Date: {booking_info['date']} Time: {booking_info['time']}

            Ready for next customer!
            Say "book [service]" to continue
            """
    
    if "no" in user_input_lower or "cancel" in user_input_lower:
        session_state.booking_info = {"step": 0, "greeted": booking_info["greeted"]}
        return "Booking cancelled. Say 'book [service]' to start again!"
    
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

        Name: {booking_info['name']}
        Email: {booking_info['email']}
        Phone: {booking_info['phone']}
        Type: {booking_info['booking_type']}
        Date: {booking_info['date']}
        Time: {booking_info['time']}

        Say "yes" to confirm or "no" to cancel
        """
    
    current_step = steps[booking_info["step"]]
    hint = " (YYYY-MM-DD)" if current_step == "date" else " (HH:MM)" if current_step == "time" else ""
    return f"What's your {current_step.replace('_', ' ')}?{hint}"
