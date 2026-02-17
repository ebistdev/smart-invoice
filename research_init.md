# Smart Invoice Generator - Market Research & Technical Analysis
> Generated: 2026-02-16

## Executive Summary
Building an AI-powered invoice generator with a unique workflow:
- Contractor describes work verbally/text ("Bill for 4 hours drywall, 2 hours painting")
- AI generates professional invoice with **predetermined rates**
- **Financial guarantee** - rates are locked, no AI hallucination on prices
- Beautiful, itemized output

**Key Differentiator:** Voice/text → Invoice with guaranteed correct pricing

---

## Competitive Landscape

### Free Invoice Generators

#### Invoice Generator (invoice-generator.com)
- 4+ million users
- Simple template-based
- No AI, purely manual input
- **Weakness:** Manual everything, no intelligence

#### Zoho Invoice
- Free for small businesses
- Template-based invoicing
- Payment reminders
- **Weakness:** Requires full form input, no AI

#### Wave
- Free accounting + invoicing
- Good for small business
- **Weakness:** No AI, complex for simple contractor use

### Paid Solutions

| Product | Price | AI Features |
|---------|-------|-------------|
| FreshBooks | $8.50/mo+ | None - manual |
| QuickBooks | $15/mo+ | Smart categorization |
| Stripe Invoicing | 0.4% + 25¢ | Basic templates |
| Square Invoices | 2.9% + 30¢ | Template-based |
| PayPal Invoicing | Free + fees | No AI |

### AI Invoice Tools (Emerging)

| Product | Approach |
|---------|----------|
| Clockify | Time tracking → invoice |
| Harvest | Time/expense → invoice |
| AND.CO (Fiverr) | Proposal → invoice flow |

**Gap in Market:** No tool does "describe work → AI generates correct invoice with preset rates"

---

## Our Unique Value Proposition

### The "Talk to Bill" Workflow

```
Contractor: "Bill Johnson Electric for 3 hours
            troubleshooting, replaced a 30-amp breaker,
            and 45 minutes travel"

AI Output:
┌────────────────────────────────────────────┐
│ INVOICE #2026-0217                         │
│ Bill To: Johnson Electric                  │
├────────────────────────────────────────────┤
│ Troubleshooting        3.0 hrs @ $85   $255│
│ 30-amp Breaker         1 ea  @ $45    $45 │
│ Travel Time            0.75 hrs @ $50  $37.50│
├────────────────────────────────────────────┤
│ Subtotal                              $337.50│
│ GST (5%)                              $16.88│
│ TOTAL                                $354.38│
└────────────────────────────────────────────┘
```

### Key Features

1. **Predetermined Rate Card**
   - User sets their rates ONCE
   - "Troubleshooting: $85/hr"
   - "Travel: $50/hr"
   - "Materials: cost + 20%"
   
2. **Financial Guarantee**
   - AI CANNOT hallucinate prices
   - Rates come from user's locked rate card
   - Quantities parsed from description
   - No made-up numbers

3. **Smart Parsing**
   - "4 hours" → 4.0 hrs
   - "half day" → 4.0 hrs
   - "replaced a breaker" → matches "30-amp breaker" from parts catalog

4. **Review Before Send**
   - AI generates draft
   - User confirms/adjusts
   - Then sends

---

## Technical Architecture

```
┌──────────────────────────────────────────────────┐
│                   Web/Mobile UI                   │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
│  │   Voice    │  │   Text     │  │   Quick    │  │
│  │   Input    │  │   Input    │  │   Items    │  │
│  └────────────┘  └────────────┘  └────────────┘  │
├──────────────────────────────────────────────────┤
│                   FastAPI Backend                 │
├──────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────┐  │
│  │           AI Parsing Engine (LLM)          │  │
│  │  - Extract items, quantities, descriptions │  │
│  │  - Match to rate card                      │  │
│  │  - NO price generation (safety)            │  │
│  └────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌────────────┐  ┌──────────┐  │
│  │  Rate Card   │  │  Clients   │  │  Invoice │  │
│  │  (locked $)  │  │  Database  │  │  History │  │
│  └──────────────┘  └────────────┘  └──────────┘  │
├──────────────────────────────────────────────────┤
│              PostgreSQL + Redis                   │
└──────────────────────────────────────────────────┘
```

---

## Safety Architecture (Financial Guarantee)

### Principle: AI extracts, Rate Card prices

```python
# User's Rate Card (locked, user-managed)
rate_card = {
    "labor": {
        "troubleshooting": {"rate": 85.00, "unit": "hour"},
        "installation": {"rate": 95.00, "unit": "hour"},
        "travel": {"rate": 50.00, "unit": "hour"},
    },
    "materials": {
        "30-amp breaker": {"rate": 45.00, "unit": "each"},
        "outlet": {"rate": 8.50, "unit": "each"},
    }
}

# AI Output (ONLY quantities and item matches)
ai_parsed = {
    "line_items": [
        {"item_key": "labor.troubleshooting", "quantity": 3.0},
        {"item_key": "materials.30-amp breaker", "quantity": 1},
        {"item_key": "labor.travel", "quantity": 0.75},
    ],
    "client_hint": "Johnson Electric"
}

# Final pricing computed SERVER-SIDE from rate_card
# AI never suggests prices
```

### Why This Matters
- No "AI charged $500 for a $50 job" errors
- Contractor's rates are their rates
- Auditable, defensible invoices
- Trust-building for adoption

---

## MVP Features (v0.1)

### Core Flow
1. **Onboarding**
   - Set up business info (name, logo, address)
   - Create rate card (services + prices)
   - Add tax settings (GST/PST)

2. **Quick Invoice**
   - Text box: describe the work
   - AI parses → shows draft
   - Edit if needed → confirm

3. **Output**
   - PDF download
   - Email to client
   - Copy payment link

### Nice-to-Have (v0.2)
- Voice input (Whisper)
- Client database
- Recurring invoices
- Payment tracking
- QuickBooks/Wave export

---

## Tech Stack

| Component | Choice |
|-----------|--------|
| Backend | FastAPI (Python 3.11+) |
| LLM | Claude 3.5 Sonnet / GPT-4o mini |
| Voice | Whisper (optional) |
| Frontend | SvelteKit |
| Database | PostgreSQL |
| PDF | WeasyPrint / Puppeteer |
| Auth | Supabase / Clerk |
| Payments | Stripe |

---

## LLM Prompt Strategy

### Structured Output Prompt
```
You are an invoice line-item extractor. Given a work description 
and a rate card, extract line items.

RATE CARD:
{rate_card_json}

WORK DESCRIPTION:
"{user_input}"

OUTPUT FORMAT (JSON only):
{
  "line_items": [
    {"item_key": "...", "quantity": X, "notes": "..."}
  ],
  "client_name": "...",
  "work_date": "..."
}

RULES:
- ONLY use item_key values from the rate card
- NEVER invent prices - prices come from rate card
- Quantity must be a number
- If unsure, use "unknown" for item_key (user will fix)
```

---

## Revenue Model

### Target: $3K MRR in 6 months

- **Free:** 5 invoices/month, basic templates
- **Pro ($12/mo):** Unlimited invoices, custom branding, voice input
- **Business ($29/mo):** Client portal, payment tracking, team

### Customer Segments
1. **Solo contractors** (electricians, plumbers, handymen)
2. **Freelancers** (designers, consultants)
3. **Small service businesses** (cleaning, landscaping)

---

## Marketing Angles

1. **"Your prices, your way"** - No AI surprises
2. **"Bill in seconds"** - Say it, send it
3. **"Professional invoices without the paperwork"**
4. **Trade-specific landing pages** (electrician, plumber, etc.)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| AI misparses work | Review step before send |
| Unknown items | "Unknown" flag, user fixes |
| Voice accuracy | Text fallback, confirmation |
| Rate card setup friction | Templates by trade |

---

## Development Phases

### Phase 1: MVP (2 weeks)
- Basic rate card management
- Text input → AI parse → Invoice
- PDF generation
- Simple web UI

### Phase 2: Enhancement (2 weeks)
- Client database
- Invoice history
- Email sending
- Voice input (optional)

### Phase 3: Polish (1 week)
- Custom branding
- Multiple templates
- Stripe subscriptions
- Landing page

---

## Next Steps

1. [x] Research complete
2. [ ] Initialize project structure
3. [ ] Build rate card data model
4. [ ] Implement AI parsing (safe, no price generation)
5. [ ] PDF template
6. [ ] Deploy MVP
7. [ ] Get first contractor user feedback
