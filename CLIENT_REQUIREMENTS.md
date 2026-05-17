# Client Requirements - What We Need From You

> This document lists everything required from the client's side to proceed with development, testing, and launch.

---

## Phase 1 — Required Before Development Starts

### 1. Brand Content (Per Brand)
You must provide the following for **each brand** you want to launch:

| Item | Format | Notes |
|------|--------|-------|
| Brand name | Text | Official brand name |
| Brand logo | PNG/SVG, high-res | Transparent background preferred |
| Brand colors | Hex codes | Primary, secondary, accent colors |
| Brand description | Text | 2-3 sentence brand identity statement |
| Product catalog | Spreadsheet (CSV/Excel) | Each product: name, description, ingredients list, price, category |
| Product images | JPG/PNG, min 800x800px | One primary image per product; clean, branded product shots |
| FAQ list | Spreadsheet (CSV/Excel) | Question + Answer pairs, organized by category |
| Tone guidelines | Document | How the brand should "sound": formal/casual, warm/clinical, emoji usage, vocabulary preferences |
| Avoided words/phrases | List | Words/phrases the brand must NEVER use |
| Preferred words/phrases | List | Words/phrases the brand prefers to use |
| Skincare routines | Structured document | Step-by-step routines: which products map to which steps, for which skin types |
| Compliance rules | List | Any specific claims that must not be made, blocked topics |
| Image-style preferences | Reference images or description | Product card style: rounded/sharp edges, background color, overall aesthetic (e.g., soft-luxury, clinical, K-beauty minimal) |
| Fallback message | Text | What the chatbot says when it cannot answer safely |

### 2. API Accounts & Keys
You must set up these accounts and provide us access/keys:

| Account | What You Need To Do | Cost Model |
|---------|---------------------|------------|
| **Anthropic (Claude API)** | Create account at anthropic.com, enable billing, generate API key | Usage-based (per token) |
| **Embeddings API** | Create account at Voyage AI or OpenAI, enable billing, generate API key | Usage-based (per token) |
| **AWS S3** (or equivalent) | Create AWS account, set up S3 bucket, provide access credentials (IAM) | Usage-based (storage + transfer) |

### 3. Hosting & Infrastructure
| Item | Options |
|------|---------|
| **Cloud hosting** | Provide AWS/GCP account, or we set up on your behalf |
| **Domain** | If you want admin panel on a custom domain, provide domain access |

### 4. Decision Points
Before development begins, you need to confirm:

| Decision | Options |
|----------|---------|
| Number of brands for Phase 1 launch | Up to 10 supported |
| Embeddings provider preference | Voyage AI or OpenAI |
| Hosting provider preference | AWS or GCP |
| Lead capture trigger per brand | On welcome / After N messages / On intent / Manual |
| Response length preference per brand | Short / Medium / Long |

---

## Phase 2 — Required Before Channel Integration

### 5. Meta / WhatsApp Requirements
| Item | What You Need To Do |
|------|---------------------|
| **Meta Business Account** | Set up verified Meta Business account |
| **WhatsApp Business API** | Apply for WhatsApp Business API access per brand |
| **Phone numbers** | Dedicated phone number per brand for WhatsApp |
| **Meta verification** | Complete Meta business verification process |
| **Message template approvals** | Submit and get approval for outbound message templates |

### 6. Instagram Requirements
| Item | What You Need To Do |
|------|---------------------|
| **Instagram Business pages** | Each brand must have an Instagram Business account |
| **Admin access** | Provide admin access to each brand's Instagram Business account |
| **Meta Graph API access** | Connected through Meta Business account |

---

## Ongoing Responsibilities (Post-Launch)

| Responsibility | Details |
|----------------|---------|
| API billing | Claude API, Embeddings API — usage-based, paid by you |
| Hosting costs | AWS/GCP compute, storage, networking — paid by you |
| S3 storage costs | Product images, brand assets — paid by you |
| Content updates | You update products, FAQs, routines via admin panel (no developer needed) |
| Feedback cycles | 48-72 hour turnaround during active development sprints |

---

## Content Delivery Format Recommendations

For fastest onboarding, provide brand content in these formats:

### Product Catalog CSV Format
```
name,description,ingredients,price,category,skin_types,concerns,image_filename
"Glow Serum","A lightweight vitamin C serum...","Vitamin C, Hyaluronic Acid, Niacinamide",45.00,"Serums","oily,combination,normal","dullness,hyperpigmentation","glow-serum.jpg"
```

### FAQ CSV Format
```
question,answer,category
"What skin type is this for?","Our Glow Serum works best for oily, combination, and normal skin types.","Product Info"
```

### Routine Definition Format
```
routine_name,skin_type,step_number,step_name,product_name
"Morning Glow Routine","oily",1,"Cleanse","Gentle Foam Cleanser"
"Morning Glow Routine","oily",2,"Tone","Balancing Toner"
"Morning Glow Routine","oily",3,"Serum","Glow Serum"
"Morning Glow Routine","oily",4,"Moisturize","Oil-Free Moisturizer"
```

---

## Single Point of Contact

As per SRS Section 28.3: **One founder or designated person** must serve as the primary decision-maker for approvals and feedback throughout the project. Please confirm who this is before kickoff.
