from typing import Dict, Any
import streamlit as st
import json
import re

REQUIRED_FIELDS = ["name", "email", "phone", "booking_type", "date", "time"]

ENTITY_PROMPT = """
Extract booking details from the message.

Return ONLY valid JSON.
Keys:
name, email, phone, booking_type, date, time

Rules:
- Use null if missing
- booking_type must be one word (hotel, doctor, spa, salon, restaurant)
- Do not explain anything

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
    return re.match(r"^\d{10}$", text)

def is_date(text: str):
    return re.match(r"^\d{2}-\d{2}-\d{4}$", text)

def is_time(text: str):
    return re.match(r"^\d{1,2}:\d{2}$", text)

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

    if text_lower in ["hi", "hello", "hey", "start", "help"] and not booking_info["greeted"]:
        booking_info["greeted"] = True
        return "Hello! To book, type something like 'Book hotel on 12-12-2023 at 9:00' or ask PDF questions like 'What is the hotel price?'"

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
        if any(word in text_lower for word in ["price", "cost", "available", "service", "policy", "room", "appointment", "hours", "location"]):
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
    elif not booking_info["name"] and text.replace(" ", "").isalpha():
        booking_info["name"] = text

    missing = [f for f in REQUIRED_FIELDS if not booking_info.get(f)]

    if missing:
        hints = []
        for f in missing:
            if f == "email":
                hints.append("email (e.g., user@email.com)")
            elif f == "phone":
                hints.append("phone (10 digits)")
            elif f == "date":
                hints.append("date (DD-MM-YYYY)")
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
