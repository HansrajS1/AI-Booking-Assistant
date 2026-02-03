# AI Booking Assistant 
AI-powered conversational booking system that handles Hotels, Doctor appointments, Restaurant tables, Spa, Salon, Events & Classes through natural language chat.
6-step flow → Supabase DB + SendGrid emails + optional PDF RAG.

live link : https://ai-booking-assistant.streamlit.app/

Installation

```bash
git clone https://github.com/HansrajS1/AI-Booking-Assistant
cd AI-Booking-Assistant

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

python -m streamlit run app/main.py
```

.env required

GROQ_API_KEY=GROQ_API_KEY

SUPABASE_URL=SUPABASE_URL

SUPABASE_KEY=SUPABASE_KEY

SENDGRID_API_KEY=SENDGRID_API_KEY

FROM_EMAIL=FROM_EMAIL







