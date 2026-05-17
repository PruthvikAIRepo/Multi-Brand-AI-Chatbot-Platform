# Scope of Work - Multi-Brand AI Chatbot Platform

> Based on: SRS Complete Final (Sections 1-28, 31 pages)
> Client: Skincare Brand Owner (Multi-Brand)
> Developer: Keshav Infotech
> Date: May 2026

---

## 1. Project Summary

A multi-brand AI chatbot platform where one admin dashboard manages independent chatbot instances per skincare brand. Each brand is fully isolated — own tone, knowledge base, compliance rules, product catalog, and visual identity. The AI engine uses Claude API with RAG (Retrieval-Augmented Generation) to deliver brand-accurate, compliant, personalized responses across Website, WhatsApp, and Instagram channels.

---

## 2. Phase Breakdown

### Phase 1 — Core Production Chatbot Engine
- AI backend + RAG pipeline
- Admin panel (React)
- Website chat widget (React embeddable)
- Compliance engine
- All core modules listed below

### Phase 2 — Channel, Growth, and Advanced Features
- WhatsApp Business API integration
- Instagram DM integration
- Live agent / human escalation
- SEO integration & FAQ schema
- Advanced analytics & conversion tracking
- CRM integration / webhook export
- Full versioning & rollback system
- Advanced admin permissions & roles
- A/B testing support
- Advanced prompt versioning

---

## 3. Backend Scope (Python / FastAPI)

### 3.1 Multi-Tenant Brand Architecture
| Item | Details |
|------|---------|
| Brand isolation | Separate DB namespaces, vector DB collections, S3 bucket paths per brand |
| Brand config loader | Load brand profile, tone, compliance, system prompt on every request |
| Brand config preloading | Frequently used configs preloaded into memory at startup |
| Scalability target | 5-10 brands initially, extensible via infra upgrades |
| Zero-code brand setup | New brands added entirely from admin panel |

### 3.2 AI Conversation Engine
| Item | Details |
|------|---------|
| LLM provider | Claude API (Sonnet) via Anthropic SDK |
| RAG pipeline | User query -> Vector search (brand namespace) -> Context injection -> LLM response |
| Brand system prompt | Unique per brand — tone, vocabulary, personality, compliance rules injected |
| Conversation memory | Session-based context window for multi-turn conversations |
| Hallucination control | Responses strictly grounded to brand knowledge base |
| Timeout handling | 8-second threshold — fallback message if exceeded |
| Retry logic | 1 automatic retry on Claude API failure before fallback |
| Response time target | 3-6 seconds (90th percentile) |

### 3.3 RAG & Embedding Pipeline
| Item | Details |
|------|---------|
| Vector database | pgvector (PostgreSQL extension), brand-isolated namespaces |
| Embeddings provider | Voyage AI or OpenAI Embeddings API |
| Auto-embedding | Products/FAQs auto-chunked and embedded on create/update |
| Re-embedding on update | Old embeddings deleted, new ones generated on content change |
| Similarity threshold | Configurable minimum score (e.g., 0.7) — below threshold = discard |
| Embedding status tracking | Pending / completed / failed status per update, visible in admin |
| Embedding failure handling | Data saved to PostgreSQL, embedding job queued for retry, admin notified |
| Vector search target | < 500ms per query |

### 3.4 Tone & Personality Engine
| Item | Details |
|------|---------|
| Vocabulary rules | Preferred and avoided words/phrases per brand |
| Emotional style | Warm, clinical, luxurious, friendly — configurable |
| Communication style | Formal vs casual, emoji usage, response length |
| Response length modes | Short (1-2 sentences), Medium (2-4 sentences), Long (detailed) |
| Greeting & sign-off | Custom per brand |
| Micro-tone rules | Softness level, sensory language toggle, emotional cues, restricted adjectives, clinical language control, harsh word blocking |

### 3.5 Compliance & Safety Engine
| Item | Details |
|------|---------|
| No medical claims | System prompt + post-processing filter |
| Blocked phrases | Admin-defined, checked against every response before sending |
| Safe ingredients | Only brand-approved ingredient info |
| Fallback handling | Predefined safe fallback message per brand |
| Brand-specific fallback tone | Separate fallback tone profile per brand |
| No over-explaining | Enforce brand's defined response length |
| No aggressive upselling | Natural recommendations, not salesy |
| Real-time override | All compliance rules take effect immediately, no restart needed |

### 3.6 Recommendation Rules Engine
| Item | Details |
|------|---------|
| Skin type mapping | Products tagged with suitable skin types |
| Concern mapping | Products tagged with concerns they address |
| Priority score | Per-brand weighting, higher score surfaces first |
| Exclusion rules | "Do not recommend X for Y skin type" |
| Conflict rules | "Do not recommend X and Y together" (e.g., retinol + vitamin C) |
| Suitability matrix | Multi-axis scoring: skin type, concern, sensitivity, routine step |
| Stock status | Out-of-stock excluded (manual flag in Phase 1) |
| Execution flow | User input -> Skin profile -> Rules engine filters -> Priority sort -> AI generates response -> Compliance filter -> Deliver |
| Fallback | No matching product = brand fallback, no invented recommendations |
| Rule editor UI | Admin can define/edit/delete rules without developer |
| Rule testing | Simulate inputs, preview output before publishing |
| Bulk import | CSV upload for large rule sets |

### 3.7 Input Moderation & Prompt Injection Protection
| Item | Details |
|------|---------|
| Pre-filter | Length validation, empty input rejection, rapid-fire detection |
| Pattern matcher | Regex detection of prompt injection patterns |
| Spam detector | Repeated messages, gibberish detection, frequency anomalies |
| Abuse filter | Profanity/harassment detection, configurable per brand |
| Off-topic classifier | Lightweight LLM-based, flags irrelevant inputs |
| Role lock | System prompt ignores user-side role redefinition |
| Instruction sandboxing | User input wrapped in delimiters, treated as data not instructions |
| System prompt protection | AI never reveals/summarizes/modifies system prompt |
| Per-brand sensitivity | Low / Medium / High moderation configurable |
| Response on block | Silent drop / polite refusal / brand fallback (configurable) |

### 3.8 Authentication & RBAC
| Item | Details |
|------|---------|
| Roles (Phase 1) | Super Admin (full access) + Admin (brand-scoped) |
| Login | Email + password, bcrypt hashed |
| Session | JWT-based, configurable expiry, refresh token support |
| Password reset | Email-based, time-limited tokens |
| Brute-force protection | Account lockout after configurable failed attempts |
| First login | Forced password change on invitation |
| API permission middleware | Every admin route enforced; brand-scoped DB filtering |
| Audit trail | Every privileged action logged: user ID, timestamp, IP, action, before/after state |

### 3.9 Lead Capture & Bot Protection
| Item | Details |
|------|---------|
| Capture trigger | Configurable per brand: on welcome, after N messages, on intent, manual |
| Form fields | Name (required), Email (required), Phone (optional) |
| GDPR consent | Editable consent text per brand |
| Duplicate handling | Match by email, update not duplicate |
| reCAPTCHA v3 | Invisible verification on widget init and form submit |
| Per-IP rate limit | Distinct from per-user, blocks IP flooding |
| Suspicious activity detection | Bot-like patterns trigger CAPTCHA or temp block |
| Honeypot fields | Hidden fields auto-submitted by bots = silent rejection |
| CSV export | Per brand with filtering |

### 3.10 Secret Management
| Item | Details |
|------|---------|
| Scope | Per-brand API keys (Anthropic, Embeddings) or system-default fallback |
| Encryption | AES-256 at rest |
| Storage | Dedicated secrets table or cloud-native secret manager |
| Access | Super Admin only |
| Display | Never plaintext — last-four-chars or set/not-set only |
| Key rotation | Manual, zero-downtime (test before replace), brief rollback window |
| Audit | Every access/update/deletion logged |

### 3.11 Multi-Channel Integration
| Channel | Method | Phase |
|---------|--------|-------|
| Website Chat | WebSocket API | Phase 1 |
| WhatsApp | WhatsApp Business API (Meta Cloud API), webhook-based | Phase 2 |
| Instagram DM | Meta Graph API | Phase 2 |

Channel router handles message format conversion per platform:
- Website: Rich HTML, product cards, routine cards, quick-action buttons
- WhatsApp: Plain text, media messages, interactive buttons
- Instagram: Plain text, media messages, quick replies, emoji-friendly

### 3.12 Task Queue & Background Jobs
| Item | Details |
|------|---------|
| Stack | Celery + Redis |
| Jobs | Async webhook processing, embedding generation, data retention purge, embedding retry on failure |

### 3.13 File Storage
| Item | Details |
|------|---------|
| Provider | AWS S3 or equivalent |
| Content | Product images, brand assets (logos, theme files) |
| Flow | Upload -> S3 returns URL -> URL stored in PostgreSQL -> Served via channel API |

### 3.14 Logging & Observability
| Log Type | Content |
|----------|---------|
| Conversation logs | Full query + response per message, per brand, per channel |
| RAG retrieval logs | Retrieved chunks, similarity scores per query |
| Error logs | API failures, timeouts, webhook failures |
| Compliance logs | Blocked/replaced responses with reason |
| Admin activity logs | What changed, when, by whom, before/after state |
| Moderation logs | Blocked inputs with specific reason |

### 3.15 Cost & Usage Control
| Item | Details |
|------|---------|
| Max tokens per response | Configurable per brand |
| Rate limiting | Per-user message limit (e.g., 30/min) |
| Per-brand API tracking | Track Claude + embedding API consumption per brand |

### 3.16 Data Retention & Privacy
| Item | Details |
|------|---------|
| Conversation retention | Configurable period (e.g., 90 days), auto-purge older |
| User data deletion | Delete specific user data on request |
| Data masking | Sensitive data masked in logs/analytics |
| Privacy compliance | Basic GDPR/CCPA support |

### 3.17 Backup & Recovery
| Item | Details |
|------|---------|
| PostgreSQL | Automated daily backups, configurable retention |
| Vector embeddings | Re-generable from PostgreSQL source data |
| S3 | Built-in redundancy, optional cross-region replication |
| Recovery | Documented procedure to restore full system |

### 3.18 Performance Optimizations
| Item | Details |
|------|---------|
| Brand config preloading | Loaded into memory at startup |
| Connection pooling | DB + Redis connections pooled |
| Common query caching | Frequently asked questions cached |

---

## 4. Frontend Scope (React.js + Tailwind CSS)

### 4.1 Admin Panel — Screens & Functionality

| Screen | Functionality |
|--------|---------------|
| **Dashboard** | Overview: all brands, total conversations, active users, channel stats |
| **Brand Manager** | Add/edit/delete brands; name, logo, colors, description |
| **Tone Settings** | Vocabulary, emotional style, communication style, micro-tone rules, response length, greetings per brand |
| **Product Manager** | Add/edit products: name, description, ingredients, images, price; auto-embed to vector DB |
| **FAQ Manager** | Add/edit FAQ entries per brand; auto-embed on save |
| **Routine Builder** | Create multi-step routines; map products to steps; set skin-type conditions |
| **Compliance Rules** | Manage allowed/disallowed phrases, blocked topics, conversation boundaries per brand |
| **Image-Style Rules** | Define visual aesthetic per brand: product cards, routine cards, UI elements |
| **Channel Config** | Connect WhatsApp numbers, Instagram pages per brand (Phase 2 integration) |
| **Conversation Logs** | View chat history per brand/channel; flag and review conversations |
| **Analytics** | Message volume, popular questions, response quality, channel breakdown |
| **User Management** | Invite admins, assign brands, revoke access (Super Admin) |
| **Lead Management** | Leads list per brand, sortable, searchable, filterable, CSV export |
| **Secret Management** | Add/update/delete API keys per brand, test connection, masked display (Super Admin) |
| **Prompt Editor** | Direct editing, composed view, live preview, syntax validation |
| **Prompt Versioning** | 20-version history, restore, diff view, annotations, draft/publish workflow |

### 4.2 Admin Panel — Override Controls
| Control | Behavior |
|---------|----------|
| Tone Override | Override tone/personality for any brand, instant effect |
| Vocabulary Override | Update preferred/avoided words instantly |
| Compliance Override | Modify compliance rules in real-time |
| Routine Override | Update/reorder/replace routine logic and product mappings |
| Emergency Override | Instantly disable chatbot or switch to safe-mode fallback |

All overrides take effect immediately — no restart or redeployment required.

### 4.3 Chat Widget (React Embeddable Component)

| Screen/Flow | Description |
|-------------|-------------|
| **Welcome Screen** | Brand-specific greeting, logo, intro message, quick-action buttons (Browse Products, Skin Quiz, FAQ) |
| **Chat Interface** | Message bubbles, typing indicator, product cards with images, routine step cards |
| **Skin Quiz Flow** | Guided questions: skin type -> concerns -> preferences -> personalized routine |
| **Product Card** | Inline card: product image, name, price, short description, purchase link |
| **Routine Display** | Step-by-step routine with product images |
| **Fallback Message** | Brand-specific fallback in brand's fallback tone |

Widget Features:
- Embeddable via `<script>` tag on any website
- Fully branded per brand (colors, fonts, card styles, image styles)
- WebSocket-based real-time communication
- reCAPTCHA v3 integration
- Lead capture form with GDPR consent
- Responsive design

---

## 5. Database Scope (PostgreSQL + pgvector)

### 5.1 Core Tables

| Table | Purpose |
|-------|---------|
| `brands` | Brand profiles: name, logo URL, theme colors, metadata, status |
| `brand_configs` | Per-brand configuration: tone settings, response length, greeting, sign-off |
| `brand_micro_tone_rules` | Softness level, sensory language, emotional cues, restricted adjectives per brand |
| `brand_image_styles` | Image-style rules per brand: product card style, routine card style, UI elements |
| `users` | Admin users: email, password hash, role, status |
| `user_brand_assignments` | Many-to-many: which admins can access which brands |
| `products` | Product catalog: name, description, ingredients, price, image URL, brand_id, stock status |
| `product_skin_types` | Skin type tags per product |
| `product_concerns` | Concern tags per product |
| `faqs` | FAQ entries per brand |
| `routines` | Routine definitions per brand: name, description, conditions |
| `routine_steps` | Steps within a routine: order, step name, product_id |
| `compliance_rules` | Blocked phrases, allowed phrases, conversation boundaries per brand |
| `recommendation_rules` | Exclusion rules, conflict rules, priority scores, suitability matrix per brand |
| `conversations` | Conversation sessions: brand_id, channel, user identifier, started_at |
| `messages` | Individual messages: conversation_id, role (user/assistant), content, timestamp |
| `leads` | Captured leads: name, email (encrypted), phone (encrypted), brand_id, channel, consent, created_at |
| `secrets` | Encrypted API keys/tokens per brand: key_type, encrypted_value, brand_id |
| `prompt_versions` | System prompt versions per brand: version number, content, annotation, is_live, created_by |
| `embedding_sync_status` | Track embedding status per entity: entity_type, entity_id, status (pending/completed/failed) |

### 5.2 Logging Tables

| Table | Purpose |
|-------|---------|
| `conversation_logs` | Full query + response, brand, channel |
| `rag_retrieval_logs` | Retrieved chunks, similarity scores per query |
| `error_logs` | API failures, timeouts, webhook failures |
| `compliance_logs` | Blocked/replaced responses with reason |
| `admin_activity_logs` | Who changed what, when, before/after state, IP address |
| `moderation_logs` | Blocked inputs with reason, user identifier |

### 5.3 pgvector Collections

| Collection | Purpose |
|------------|---------|
| `brand_{id}_products` | Product text embeddings per brand namespace |
| `brand_{id}_faqs` | FAQ embeddings per brand namespace |
| `brand_{id}_routines` | Routine description embeddings per brand namespace |

Each brand gets its own isolated vector namespace — zero cross-contamination.

### 5.4 Key Database Decisions
- **pgvector** as PostgreSQL extension (not a separate vector DB) — simplifies ops, single DB engine
- **Brand isolation** via brand_id foreign keys + row-level filtering on every query
- **Encryption at rest** for secrets table (AES-256) and lead PII fields
- **Automated daily backups** with configurable retention
- **Data retention purge** via scheduled Celery job

---

## 6. Technology Stack Summary

| Layer | Technology |
|-------|-----------|
| Backend API | Python / FastAPI |
| AI / LLM | Claude API (Sonnet) via Anthropic SDK |
| Vector Database | pgvector (PostgreSQL extension) |
| Relational Database | PostgreSQL |
| Task Queue | Celery + Redis |
| File Storage | AWS S3 |
| Admin Panel | React.js + Tailwind CSS |
| Chat Widget | React embeddable + WebSocket |
| WhatsApp | WhatsApp Business API (Phase 2) |
| Instagram DM | Meta Graph API (Phase 2) |
| Embeddings | Voyage AI / OpenAI Embeddings API |
| Hosting | AWS / GCP (Cloud Run / ECS) |
| Authentication | JWT + bcrypt |
| Bot Protection | reCAPTCHA v3 |

---

## 7. Delivery Scope

### 7.1 Phase 1 Deliverables (28 items confirmed in SRS Section 27.1)
1. Multi-brand AI chatbot platform
2. Brand isolation architecture
3. Admin panel (full React dashboard)
4. Website chat widget (embeddable)
5. RAG knowledge base system
6. Product management
7. FAQ management
8. Routine / skin quiz logic
9. Basic product recommendation rules engine
10. Compliance and safe fallback logic
11. Tone and personality engine
12. Session memory and personalization
13. Conversation logs
14. RAG retrieval logs
15. Error logs and retry logic
16. Rate limiting and abuse prevention
17. Input moderation (spam, abuse, prompt injection)
18. Prompt management from admin panel
19. Basic RBAC (Super Admin + Admin)
20. Lead capture (name, email)
21. Backup and recovery process
22. Data retention and privacy controls
23. Knowledge base auto re-embedding
24. Deployment and setup support
25. Full source code ownership
26. Admin activity logging
27. Secure per-brand API key & secret management
28. reCAPTCHA / bot protection

### 7.2 Phase 2 Deliverables (10 items confirmed in SRS Section 27.2)
1. WhatsApp Business integration
2. Instagram DM integration
3. Live agent / human escalation
4. SEO integration & FAQ schema support
5. Advanced analytics & conversion tracking
6. CRM integration / webhook export
7. Full versioning & rollback system
8. Advanced admin permissions & roles
9. A/B testing support
10. Advanced prompt versioning

### 7.3 Explicitly Out of Scope (SRS Section 28.2)
- Mobile native apps (iOS, Android)
- Voice-based chatbot
- Multi-language support (English-first in Phase 1)
- E-commerce checkout integration (bot links out only)
- Custom domain SSL beyond standard config
- Marketing campaign management
- Email/SMS marketing automation
- Content writing for FAQs/products/tone (client provides)
- Product photography and brand asset creation
- Brand identity design
- Custom integrations beyond Phase 2 list

---

## 8. QA Acceptance Criteria (SRS Section 18.2)

| # | Test Area |
|---|-----------|
| 1 | Brand isolation — no cross-brand data leakage |
| 2 | Tone accuracy per brand — responses match configured tone and length |
| 3 | Compliance-safe responses — no blocked phrases, no medical claims, no hallucination |
| 4 | Product recommendation accuracy — correct products for correct skin types |
| 5 | Skin quiz logic — correct routine generated based on user answers |
| 6 | Website chat widget — functional, branded, responsive |
| 7 | WhatsApp integration — webhook receives and responds (Phase 2) |
| 8 | Instagram DM integration — webhook receives and responds (Phase 2) |
| 9 | Admin panel — all CRUD, tone settings, compliance rules, overrides functional |
| 10 | Error handling and fallback behavior — graceful degradation on API failures |

---

## 9. Post-Launch Support (SRS Section 18.3)

| Term | Details |
|------|---------|
| Bug-fix period | 30 days post-launch, no additional cost |
| Critical bug response | Within 24 hours |
| Non-critical response | Within 48-72 hours |
| Scope | Bug fixes only; new features quoted separately |
| API/Hosting costs | Paid by client |
| Ongoing maintenance | Optional paid engagement |
