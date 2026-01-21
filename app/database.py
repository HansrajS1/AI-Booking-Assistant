from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import streamlit as st
import uuid

supabase = None
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    st.success(" Supabase connected!")
except:
    st.warning(" Demo mode - no database")
    supabase = None

def insert_customer(name: str, email: str, phone: str = None):
    if not supabase:
        customer_id = str(uuid.uuid4())
        st.success(f" Demo customer {customer_id} created")
        return customer_id
    
    data = {
        "name": name,
        "email": email,
        "phone": phone
    }
    try:
        response = supabase.table("customers").insert(data).execute()
        customer_id = response.data[0]["customer_id"]
        st.success(f" Customer {customer_id} created!")
        return customer_id
    except Exception as e:
        st.error(f"Customer creation failed: {e}")
        return str(uuid.uuid4())

def insert_booking(customer_id: str, booking_type: str, date: str, time: str):
    if not supabase:
        booking_id = str(uuid.uuid4())
        st.success(f" Demo booking {booking_id} created")
        return booking_id
    
    data = {
        "customer_id": customer_id,
        "booking_type": booking_type,
        "date": date,
        "time": time,
        "status": "CONFIRMED"
    }
    try:
        response = supabase.table("bookings").insert(data).execute()
        booking_id = response.data[0]["id"]
        st.success(f" Booking {booking_id} saved!")
        return booking_id
    except Exception as e:
        st.error(f"Booking save failed: {e}")
        return str(uuid.uuid4())

def fetch_all_bookings():    
    try:
        response = supabase.table("bookings").select("""
            id, booking_type, date, time, status, created_at,
            customers(name, email)
        """).execute()
        return response.data or []
    except:
        return []
