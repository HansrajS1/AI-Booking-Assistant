import streamlit as st
import pandas as pd
from database import fetch_all_bookings

def show_dashboard():
    st.title(" Admin Dashboard")
    
    bookings = fetch_all_bookings()
    
    if not bookings:
        st.info(" No bookings")
        return
    
    data = []
    for booking in bookings:
        customer_name = "N/A"
        customer_email = "N/A"
        
        if booking.get("customers"):
            customers = booking["customers"]
            if isinstance(customers, dict):
                customer_name = customers.get("name", "N/A")
                customer_email = customers.get("email", "N/A")
        
        row = {
            "ID": booking.get("id", "N/A"),
            "Type": booking.get("booking_type", "N/A"),
            "Date": booking.get("date", "N/A"),
            "Time": booking.get("time", "N/A"),
            "Status": booking.get("status", "CONFIRMED"),
            "Customer": customer_name,
            "Email": customer_email
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    col1, col2 = st.columns(2)
    with col1:
        st.metric(" Total", len(df))
    with col2:
        st.metric(" Confirmed", len(df[df['Status'] == 'CONFIRMED']))
    
    st.dataframe(df, use_container_width=True)
