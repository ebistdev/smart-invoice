# Smart Invoice 🧾✨

Describe your work, get a professional invoice. Powered by AI with guaranteed correct pricing.

## The Magic

```
You say: "Bill Johnson Electric for 3 hours troubleshooting, 
         replaced a 30-amp breaker, and 45 minutes travel"

You get: A beautiful, itemized invoice with YOUR preset rates
```

## Why Smart Invoice?

- 🔒 **Guaranteed Pricing**: Your rates, always. AI extracts quantities, not prices.
- 🎤 **Voice or Text**: Describe work naturally
- ⚡ **Seconds, Not Minutes**: Skip the forms
- 📱 **Mobile-Ready**: Invoice from the job site

## Quick Start

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## How It Works

1. **Set up your rate card** (one time): services, hourly rates, materials
2. **Describe your work**: voice or text
3. **Review the draft**: AI parses, you confirm
4. **Send**: PDF, email, or payment link

## Tech Stack

- **Backend**: FastAPI + Claude/GPT
- **Frontend**: SvelteKit
- **Database**: PostgreSQL
- **PDF**: WeasyPrint

## License

MIT
