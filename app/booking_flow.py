from typing import Dict, Any
import streamlit as st
import json
import re
from datetime import datetime

REQUIRED_FIELDS = ["name", "email", "phone", "booking_type", "date", "time"]
GREETINGS = {
    "hi", "hello", "hey", "hii", "yo",
    "start", "help", "please",
    "good morning", "good evening", "good afternoon"
}



ENTITY_PROMPT = """
Extract booking details from the message.

Return ONLY valid JSON.
Keys:
name, email, phone, booking_type, date, time

Rules:
- Use null if missing
- booking_type must be one word (hotel, doctor, spa, salon, restaurant,service)
- Do not explain anything
- Ensure date is in YYYY-MM-DD format
- Ensure time is in HH:MM 24-hour format
- Ensure email is valid format

Message:
"{text}"
"""

def initialize_booking_state(session_state: Dict[str, Any]):
    if "booking_info" not in session_state:
        session_state.booking_info = {k: None for k in REQUIRED_FIELDS}
        session_state.booking_info["greeted"] = False

def is_email(text: str):
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", text)

def is_phone(text: str):
    return re.match(r"^\+?\d{10,15}$", text)

def is_date(text: str):
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            return False

        d = datetime.strptime(text, "%Y-%m-%d").date()
        today = datetime.now().date()

        if d < today:
            return False

        if d.year > today.year + 2:
            return False

        return True
    except ValueError:
        return False

def is_time(text: str):
    return re.match(r"^([01]?\d|2[0-3]):[0-5]\d$", text)

def extract_entities(llm, text: str) -> Dict[str, Any]:
    res = llm.invoke(ENTITY_PROMPT.format(text=text))
    content = res.content.strip()
    if content.startswith("```"):
        content = content.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(content)
    except:
        return {}

def process_message(user_input: str, session_state: Dict[str, Any]) -> str:
    initialize_booking_state(session_state)
    booking_info = session_state.booking_info
    text = user_input.strip()
    text_lower = text.lower()

    if not text:
        return "Please type something."
    
    email_match = re.search(r"\S+@\S+", text)
    phone_match = re.search(r"\+?\d{10,15}", text)
    date_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
    time_match = re.search(r"\b\d{1,2}:\d{2}\b", text)

    
    if email_match and not is_email(email_match.group()):
        return "Invalid email. Enter a valid email (e.g., user@email.com)."
    if phone_match and not is_phone(phone_match.group()):
        return "Invalid phone. Enter exactly 10-15 digits."
    if date_match and not is_date(date_match.group()):
        return "Invalid date. Enter a valid future date in YYYY-MM-DD format (within 2 years)."
    if time_match and not is_time(time_match.group()):
        return "Invalid time. Enter time in 24-hour HH:MM format."

    if (
    not booking_info["greeted"]
    and any(greet in text_lower for greet in GREETINGS)):
        booking_info["greeted"] = True
        return (
        "Hello! Please provide your full name and then enter your booking details.\n"
        "Example: Book a hotel on 2026-12-12 at 09:00\n"
        "You can also ask PDF questions like: What is the hotel price?")


    if text_lower in ["cancel", "no"]:
        session_state.booking_info = {k: None for k in REQUIRED_FIELDS}
        session_state.booking_info["greeted"] = True
        return "Booking cancelled. Start again anytime."

    if "rag_pipeline" in session_state:
        llm = session_state.rag_pipeline.llm
        extracted = extract_entities(llm, text)
        for k, v in extracted.items():
            if v:
                booking_info[k] = v

    if "rag_pipeline" in session_state:
        if any(word in text_lower for word in ["price", "cost", "available", "service", "policy", "room", "appointment", "hours", "location", "contact" ,"cancellation policy"]):
            vs = session_state.rag_pipeline.vector_store
            if vs:
                return session_state.rag_pipeline.query(text)
            else:
                return "Upload and process PDFs first to answer PDF questions."

    if is_email(text):
        booking_info["email"] = text
    elif is_phone(text):
        booking_info["phone"] = text
    elif is_date(text):
        booking_info["date"] = text
    elif is_time(text):
        booking_info["time"] = text
    elif not booking_info["name"]:
        if len(text.split()) < 2 or not all(word.isalpha() for word in text.split()):
            return "Please enter your full name (e.g., Hansraj Singh)."
        booking_info["name"] = text
    elif not booking_info["booking_type"]:
        booking_info["booking_type"] = text_lower

    missing = [f for f in REQUIRED_FIELDS if not booking_info.get(f)]

    if missing:
        hints = []
        for f in missing:
            if f == "email":
                hints.append("email (e.g., user@email.com)")
            elif f == "phone":
                hints.append("phone (10-15 digits)")
            elif f == "date":
                hints.append("date (YYYY-MM-DD)")
            elif f == "time":
                hints.append("time (HH:MM)")
            elif f == "name":
                hints.append("your full name")
            else:
                hints.append(f)
        return f"Please provide: {', '.join(hints[:3])}"

    if text_lower in ["yes", "confirm"]:
        try:
            from database import insert_customer, insert_booking
            from send_email import send_professional_email

            customer_id = insert_customer(
                booking_info["name"],
                booking_info["email"],
                booking_info["phone"]
            )
            booking_id = insert_booking(
                customer_id,
                booking_info["booking_type"],
                booking_info["date"],
                booking_info["time"]
            )

            send_professional_email(
                booking_info["email"],
                booking_info["name"],
                booking_info["booking_type"],
                booking_info["date"],
                booking_info["time"],
                booking_id or "DEMO-123"
            )

            session_state.booking_info = {k: None for k in REQUIRED_FIELDS}
            session_state.booking_info["greeted"] = True
            return f"Booking confirmed! Booking ID: {booking_id or 'DEMO-123'}"
        except:
            session_state.booking_info = {k: None for k in REQUIRED_FIELDS}
            session_state.booking_info["greeted"] = True
            return "Demo booking confirmed."

    return f"""
            Review details:
            Name: {booking_info['name']}
            Email: {booking_info['email']}
            Phone: {booking_info['phone']}
            Service: {booking_info['booking_type']}
            Date: {booking_info['date']}
            Time: {booking_info['time']}
            Type "yes" to confirm or "cancel" to stop
            """
