from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from config import SENDGRID_API_KEY, FROM_EMAIL
import streamlit as st

def send_professional_email(email: str, name: str, booking_type: str, date: str, time: str, booking_id: str):
    """Beautiful SendGrid booking confirmation"""
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=email,
        subject=f" {booking_type.title()} Confirmed | Booking #{booking_id}",
        html_content=f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <div style="background: white; border-radius: 20px; padding: 40px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #28a745; font-size: 2.5em; margin: 0;"> Confirmed!</h1>
                        <p style="color: #666; font-size: 1.1em;">Your booking has been secured</p>
                    </div>
                    
                    <div style="background: #f8f9ff; padding: 25px; border-radius: 12px; border-left: 5px solid #007bff; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #333;"> Booking Details</h3>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div><strong>Name:</strong> <span style="color: #007bff;">{name}</span></div>
                            <div><strong>Type:</strong> {booking_type}</div>
                            <div><strong>Date:</strong> {date}</div>
                            <div><strong>Time:</strong> {time}</div>
                            <div style="grid-column: span 2;"><strong>ID:</strong> <code style="background: #e9ecef; padding: 4px 8px; border-radius: 4px; font-family: monospace;">{booking_id}</code></div>
                        </div>
                    </div>
                    
                    <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 12px; margin: 30px 0;">
                        <p style="margin: 0 0 10px 0; color: #666;">Thank you for choosing us! </p>
                        <p style="margin: 0; font-size: 0.9em; color: #999;">We'll send you a reminder 24 hours before</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    )
    try:
        response = sg.send(message)
        return response.status_code == 202
    except:
        return False
