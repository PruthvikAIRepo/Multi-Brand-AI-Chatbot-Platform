# Database Design - Multi-Brand AI Chatbot Platform

> PostgreSQL + pgvector extension
> Every brand-scoped table has `brand_id` FK — no exceptions.
> All tables have `id`, `created_at`, `updated_at` unless noted.

---

## Design Decisions

Before the schema — here's why I made certain choices:

| Decision | Choice | Why |
|----------|--------|-----|
| IDs | UUID (uuid_generate_v4) | Prevents ID enumeration attacks, safe for multi-tenant, no collision risk |
| Timestamps | timestamptz (with timezone) | Always store UTC, let frontend convert |
| Merge small configs into brand_configs? | No — separate tables | Each config section (moderation, lead capture, tone) has different change frequency and access patterns. Separate tables = cleaner cache invalidation. |
| Conversation logs vs messages table? | Messages table IS the log | SRS says "conversation logs" as a feature. The messages table already stores every query + response. No duplicate table needed. |
| Session state storage | JSON column on conversations + Redis for live | Redis for live session (fast read/write during chat). Persist to conversations.session_state JSON when session ends (for admin viewing). |
| Currency | Field on brands table | Per-brand currency. Simple, one place. |
| Product categories | Text field (not enum) | Client might want custom categories per brand. Text is flexible. Enum is rigid. |
| FAQ categories | Text field (not enum) | Same reason as product categories. |
| Brute-force settings | System-wide in app config | Not per-brand — login is system-wide, not brand-scoped. Goes in .env / config.py. |
| Chatbot status (normal/safe_mode/disabled) | Field on brands table | It's a brand-level attribute, not a separate table. |

---

## Enums

```sql
-- Core enums
CREATE TYPE user_role AS ENUM ('super_admin', 'admin');
CREATE TYPE skin_type AS ENUM ('oily', 'dry', 'combination', 'sensitive', 'normal');
CREATE TYPE skin_concern AS ENUM ('acne', 'aging', 'hydration', 'hyperpigmentation', 'sensitivity', 'dullness');
CREATE TYPE channel_type AS ENUM ('website', 'whatsapp', 'instagram');
CREATE TYPE message_role AS ENUM ('user', 'assistant', 'agent');  -- 'agent' = human agent reply

-- Brand config enums
CREATE TYPE response_length AS ENUM ('short', 'medium', 'long');
CREATE TYPE chatbot_status AS ENUM ('normal', 'safe_mode', 'disabled');

-- Tone enums
CREATE TYPE emotional_style AS ENUM ('warm', 'clinical', 'luxurious', 'friendly');
CREATE TYPE communication_style AS ENUM ('formal', 'casual');
CREATE TYPE softness_level AS ENUM ('gentle', 'neutral', 'direct');

-- Image style enums
CREATE TYPE image_style_profile AS ENUM ('soft_luxury', 'clinical_luxury', 'k_beauty_minimal', 'botanical', 'modern_clean', 'custom');
CREATE TYPE card_edges AS ENUM ('rounded', 'sharp');
CREATE TYPE overlay_style AS ENUM ('none', 'gradient', 'shadow');

-- Compliance enums
CREATE TYPE compliance_rule_type AS ENUM ('blocked_phrase', 'allowed_phrase', 'blocked_topic', 'conversation_boundary');

-- Recommendation enums
CREATE TYPE recommendation_rule_type AS ENUM ('exclusion', 'conflict', 'priority', 'suitability');
CREATE TYPE routine_step_name AS ENUM ('cleanse', 'tone', 'serum', 'treat', 'moisturize', 'sunscreen', 'custom');

-- Moderation enums
CREATE TYPE moderation_sensitivity AS ENUM ('low', 'medium', 'high');
CREATE TYPE moderation_response AS ENUM ('silent_drop', 'polite_refusal', 'brand_fallback');
CREATE TYPE moderation_reason AS ENUM ('spam', 'abuse', 'prompt_injection', 'off_topic');

-- Embedding enums
CREATE TYPE entity_type AS ENUM ('product', 'faq', 'routine');
CREATE TYPE embedding_status AS ENUM ('pending', 'completed', 'failed');

-- Secret enums
CREATE TYPE secret_type AS ENUM ('anthropic_api_key', 'embeddings_api_key', 's3_credentials', 'meta_whatsapp_token', 'meta_instagram_token', 'webhook_secret');

-- Lead enums
CREATE TYPE capture_trigger AS ENUM ('on_welcome', 'after_n_messages', 'on_intent', 'manual');

-- Log enums
CREATE TYPE error_type AS ENUM ('ai_api_failure', 'embeddings_api_failure', 'storage_failure', 'timeout', 'webhook_failure');
CREATE TYPE admin_action_type AS ENUM ('created', 'updated', 'deleted', 'published', 'restored', 'overridden', 'enabled', 'disabled', 'invited', 'revoked', 'login', 'failed_login', 'secret_rotated');
CREATE TYPE notification_type AS ENUM ('embedding_failed', 'repeated_abuse', 'ai_api_failure', 'brand_status_change');
CREATE TYPE api_usage_type AS ENUM ('claude', 'embeddings');

-- Human escalation enums
CREATE TYPE escalation_status AS ENUM ('waiting', 'in_progress', 'resolved');
CREATE TYPE conversation_handler AS ENUM ('ai', 'human');

-- Phase 2 enums
CREATE TYPE webhook_event_type AS ENUM ('lead_captured', 'conversation_ended', 'escalation_requested');
CREATE TYPE ab_test_type AS ENUM ('prompt', 'tone', 'recommendation');
CREATE TYPE ab_test_status AS ENUM ('draft', 'running', 'completed');
```

---

## Tables

---

### 1. brands

The root tenant table. Everything branches from here.

```sql
CREATE TABLE brands (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(255) NOT NULL UNIQUE,
    logo_url        TEXT,
    primary_color   VARCHAR(7),          -- hex: #FF5733
    secondary_color VARCHAR(7),
    accent_color    VARCHAR(7),
    description     TEXT,
    currency        VARCHAR(3) DEFAULT 'INR',  -- ISO 4217: INR, USD, EUR
    chatbot_status  chatbot_status DEFAULT 'normal',
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_brands_slug ON brands(slug);
CREATE INDEX idx_brands_is_active ON brands(is_active);
```

---

### 2. users

System-wide. No brand_id.

```sql
CREATE TABLE users (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email                   VARCHAR(255) NOT NULL UNIQUE,
    password_hash           TEXT NOT NULL,
    full_name               VARCHAR(255),
    role                    user_role NOT NULL DEFAULT 'admin',
    is_active               BOOLEAN DEFAULT true,
    must_change_password    BOOLEAN DEFAULT true,
    failed_login_attempts   INTEGER DEFAULT 0,
    locked_until            TIMESTAMPTZ,
    last_login              TIMESTAMPTZ,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_users_email ON users(email);
```

---

### 2b. refresh_tokens

Server-side tracking for JWT refresh tokens. Needed for logout/revocation.

```sql
CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(64) NOT NULL UNIQUE,    -- SHA-256 hash of the token
    expires_at  TIMESTAMPTZ NOT NULL,
    revoked     BOOLEAN DEFAULT false,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_rt_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_rt_token_hash ON refresh_tokens(token_hash);
CREATE INDEX idx_rt_expires_at ON refresh_tokens(expires_at);
```

---

### 2c. password_reset_tokens

For the forgot password → reset password flow.

```sql
CREATE TABLE password_reset_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(64) NOT NULL UNIQUE,    -- SHA-256 hash of the token
    expires_at  TIMESTAMPTZ NOT NULL,
    used        BOOLEAN DEFAULT false,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_prt_token_hash ON password_reset_tokens(token_hash);
CREATE INDEX idx_prt_user_id ON password_reset_tokens(user_id);
```

---

### 3. user_brand_assignments

Which admins can access which brands.

```sql
CREATE TABLE user_brand_assignments (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    brand_id    UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, brand_id)
);

CREATE INDEX idx_uba_user_id ON user_brand_assignments(user_id);
CREATE INDEX idx_uba_brand_id ON user_brand_assignments(brand_id);
```

---

### 4. brand_configs

One config per brand. Core chatbot behavior settings.

```sql
CREATE TABLE brand_configs (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id                    UUID NOT NULL UNIQUE REFERENCES brands(id) ON DELETE CASCADE,

    -- Response settings
    response_length             response_length DEFAULT 'medium',
    max_tokens                  INTEGER DEFAULT 1000,
    rag_similarity_threshold    FLOAT DEFAULT 0.7,
    recommendation_top_n        INTEGER DEFAULT 3,
    session_timeout_minutes     INTEGER DEFAULT 30,

    -- Messages
    greeting_message            TEXT,
    signoff_message             TEXT,
    fallback_message            TEXT DEFAULT 'I am not sure about that. Please reach out to our support team.',
    fallback_tone_profile       TEXT,

    -- Conversation boundaries (toggles from compliance section)
    no_medical_claims           BOOLEAN DEFAULT true,
    no_over_explaining          BOOLEAN DEFAULT true,
    no_aggressive_upselling     BOOLEAN DEFAULT true,
    no_unnecessary_details      BOOLEAN DEFAULT true,
    no_medical_tone             BOOLEAN DEFAULT true,

    -- Rate limiting
    rate_limit_per_user         INTEGER DEFAULT 30,     -- messages per minute

    -- Data retention
    conversation_retention_days INTEGER DEFAULT 90,

    -- Lead capture
    lead_capture_trigger        capture_trigger DEFAULT 'after_n_messages',
    lead_capture_n_messages     INTEGER DEFAULT 3,
    lead_show_phone_field       BOOLEAN DEFAULT false,
    lead_gdpr_consent_text      TEXT DEFAULT 'I agree to the collection and processing of my data.',
    lead_allow_skip             BOOLEAN DEFAULT true,

    created_at                  TIMESTAMPTZ DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ DEFAULT NOW()
);
```

**Why conversation boundaries are here, not in compliance_rules table:** These are boolean toggles that apply globally to the brand. The compliance_rules table stores individual phrase-level rules. Different purpose, different access pattern.

---

### 5. tone_settings

One per brand. Separated because it has many fields and changes independently from brand_configs.

```sql
CREATE TABLE tone_settings (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id                    UUID NOT NULL UNIQUE REFERENCES brands(id) ON DELETE CASCADE,

    -- Core tone
    emotional_style             emotional_style DEFAULT 'warm',
    communication_style         communication_style DEFAULT 'casual',
    emoji_usage                 BOOLEAN DEFAULT false,
    vocabulary_preferred        JSONB DEFAULT '[]',     -- ["radiant", "nourishing"]
    vocabulary_avoided          JSONB DEFAULT '[]',     -- ["cheap", "basic"]

    -- Micro-tone rules
    softness_level              softness_level DEFAULT 'gentle',
    sensory_language_enabled    BOOLEAN DEFAULT true,
    emotional_cues              JSONB DEFAULT '[]',     -- ["calming", "uplifting"]
    restricted_adjectives       JSONB DEFAULT '[]',     -- ["cheap", "harsh"]
    clinical_language_allowed   BOOLEAN DEFAULT false,
    harsh_word_blocking         BOOLEAN DEFAULT true,

    created_at                  TIMESTAMPTZ DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 6. brand_image_styles

One per brand. Visual styling for the chat widget.

```sql
CREATE TABLE brand_image_styles (
    id                              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id                        UUID NOT NULL UNIQUE REFERENCES brands(id) ON DELETE CASCADE,

    image_style_profile             image_style_profile DEFAULT 'modern_clean',

    -- Product card
    product_card_edges              card_edges DEFAULT 'rounded',
    product_card_background_color   VARCHAR(7) DEFAULT '#FFFFFF',
    product_card_overlay_style      overlay_style DEFAULT 'none',

    -- Routine card
    routine_card_edges              card_edges DEFAULT 'rounded',
    routine_card_background_color   VARCHAR(7) DEFAULT '#FFFFFF',
    routine_card_overlay_style      overlay_style DEFAULT 'none',

    -- UI elements
    ui_button_style                 card_edges DEFAULT 'rounded',
    ui_button_color                 VARCHAR(7),
    ui_card_background              VARCHAR(7) DEFAULT '#FFFFFF',

    created_at                      TIMESTAMPTZ DEFAULT NOW(),
    updated_at                      TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 7. moderation_configs

Separate because it has JSON arrays (allow/block lists) that change independently.

```sql
CREATE TABLE moderation_configs (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id                    UUID NOT NULL UNIQUE REFERENCES brands(id) ON DELETE CASCADE,

    sensitivity                 moderation_sensitivity DEFAULT 'medium',
    response_on_block           moderation_response DEFAULT 'brand_fallback',
    allow_list                  JSONB DEFAULT '[]',
    block_list                  JSONB DEFAULT '[]',
    prompt_injection_patterns   JSONB DEFAULT '[]',

    created_at                  TIMESTAMPTZ DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 8. products

```sql
CREATE TABLE products (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id        UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    description     TEXT NOT NULL,
    ingredients     JSONB DEFAULT '[]',     -- ["Vitamin C", "Hyaluronic Acid"]
    price           DECIMAL(10, 2) NOT NULL,
    image_url       TEXT,
    category        VARCHAR(100),           -- text, not enum — brand-configurable
    purchase_url    TEXT,                    -- "Shop Now" button destination
    is_in_stock     BOOLEAN DEFAULT true,
    priority_score  INTEGER DEFAULT 0,
    deleted_at      TIMESTAMPTZ,            -- soft delete: NULL = active, timestamp = deleted
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_products_brand_id ON products(brand_id);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_is_in_stock ON products(is_in_stock);
CREATE INDEX idx_products_deleted_at ON products(deleted_at);
```

---

### 9. product_skin_types

```sql
CREATE TABLE product_skin_types (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id  UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    skin_type   skin_type NOT NULL,

    UNIQUE(product_id, skin_type)
);

CREATE INDEX idx_pst_product_id ON product_skin_types(product_id);
```

---

### 10. product_concerns

```sql
CREATE TABLE product_concerns (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id  UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    concern     skin_concern NOT NULL,

    UNIQUE(product_id, concern)
);

CREATE INDEX idx_pc_product_id ON product_concerns(product_id);
```

---

### 11. faqs

```sql
CREATE TABLE faqs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id    UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    question    TEXT NOT NULL,
    answer      TEXT NOT NULL,
    category    VARCHAR(100),       -- text, not enum — flexible
    deleted_at  TIMESTAMPTZ,        -- soft delete
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_faqs_brand_id ON faqs(brand_id);
CREATE INDEX idx_faqs_category ON faqs(category);
```

---

### 12. routines

```sql
CREATE TABLE routines (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id            UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    target_skin_type    skin_type,
    target_concerns     JSONB DEFAULT '[]',     -- ["acne", "dullness"]
    is_active           BOOLEAN DEFAULT true,
    deleted_at          TIMESTAMPTZ,            -- soft delete
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_routines_brand_id ON routines(brand_id);
CREATE INDEX idx_routines_is_active ON routines(is_active);
```

---

### 13. routine_steps

```sql
CREATE TABLE routine_steps (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    routine_id      UUID NOT NULL REFERENCES routines(id) ON DELETE CASCADE,
    step_number     INTEGER NOT NULL,
    step_name       routine_step_name NOT NULL,
    product_id      UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    instructions    TEXT,

    UNIQUE(routine_id, step_number)
);

CREATE INDEX idx_rs_routine_id ON routine_steps(routine_id);
```

**ON DELETE RESTRICT on product_id** — prevent deleting a product that's used in a routine. Admin must remove from routine first.

---

### 14. compliance_rules

```sql
CREATE TABLE compliance_rules (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id    UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    rule_type   compliance_rule_type NOT NULL,
    value       TEXT NOT NULL,
    is_active   BOOLEAN DEFAULT true,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_cr_brand_id ON compliance_rules(brand_id);
CREATE INDEX idx_cr_rule_type ON compliance_rules(rule_type);
CREATE INDEX idx_cr_is_active ON compliance_rules(is_active);
```

---

### 15. recommendation_rules

```sql
CREATE TABLE recommendation_rules (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id    UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    rule_type   recommendation_rule_type NOT NULL,
    config      JSONB NOT NULL,
    description TEXT,
    is_active   BOOLEAN DEFAULT true,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- config JSON examples:
-- exclusion:   {"product_id": "uuid", "excluded_for_skin_types": ["oily"], "excluded_for_concerns": ["acne"]}
-- conflict:    {"product_a_id": "uuid", "product_b_id": "uuid", "reason": "Retinol and Vitamin C conflict"}
-- priority:    {"product_id": "uuid", "priority_score": 10}
-- suitability: {"product_id": "uuid", "skin_type_scores": {"oily": 9, "dry": 3}, "concern_scores": {"acne": 8}, "routine_step": "serum"}

CREATE INDEX idx_rr_brand_id ON recommendation_rules(brand_id);
CREATE INDEX idx_rr_rule_type ON recommendation_rules(rule_type);
```

---

### 16. conversations

```sql
CREATE TABLE conversations (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id            UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    session_id          VARCHAR(255) NOT NULL UNIQUE,
    channel             channel_type NOT NULL,
    user_identifier     TEXT,               -- IP or device fingerprint, masked in UI
    session_state       JSONB DEFAULT '{}', -- persisted from Redis on session end: {skin_type, concerns, preferences, recommended_product_ids}
    is_flagged          BOOLEAN DEFAULT false,
    flag_reason         TEXT,

    -- Human escalation fields
    current_handler     conversation_handler DEFAULT 'ai',
    is_escalated        BOOLEAN DEFAULT false,
    escalation_status   escalation_status,          -- NULL when not escalated
    escalation_reason   TEXT,                        -- "user-requested" or "AI-confidence-based"
    escalated_at        TIMESTAMPTZ,
    assigned_agent_id   UUID REFERENCES users(id),

    started_at          TIMESTAMPTZ DEFAULT NOW(),
    ended_at            TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conv_brand_id ON conversations(brand_id);
CREATE INDEX idx_conv_session_id ON conversations(session_id);
CREATE INDEX idx_conv_channel ON conversations(channel);
CREATE INDEX idx_conv_is_flagged ON conversations(is_flagged);
CREATE INDEX idx_conv_started_at ON conversations(started_at);
```

---

### 17. messages

```sql
CREATE TABLE messages (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id     UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role                message_role NOT NULL,
    content             TEXT NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_msg_conversation_id ON messages(conversation_id);
CREATE INDEX idx_msg_created_at ON messages(created_at);
```

---

### 18. leads

```sql
CREATE TABLE leads (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id            UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    name                VARCHAR(255) NOT NULL,
    email_encrypted     BYTEA NOT NULL,         -- AES-256 encrypted
    email_hash          VARCHAR(64) NOT NULL,    -- SHA-256 hash for duplicate lookup
    phone_encrypted     BYTEA,                   -- AES-256 encrypted, optional
    channel             channel_type NOT NULL,
    consent             BOOLEAN NOT NULL DEFAULT false,
    consent_text        TEXT,
    conversation_id     UUID REFERENCES conversations(id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Lead email is encrypted. We use email_hash (SHA-256) for duplicate lookup:
-- "Does this email already exist for this brand?" without decrypting.

CREATE INDEX idx_leads_brand_id ON leads(brand_id);
CREATE INDEX idx_leads_email_hash ON leads(email_hash);
CREATE INDEX idx_leads_channel ON leads(channel);
CREATE INDEX idx_leads_created_at ON leads(created_at);
CREATE UNIQUE INDEX idx_leads_brand_email ON leads(brand_id, email_hash);
```

**Why email_hash?** Email is encrypted (can't search encrypted values efficiently). We store a SHA-256 hash for duplicate lookup: "does this email already exist for this brand?" Hash matches → update existing lead, don't create duplicate.

---

### 19. secrets

```sql
CREATE TABLE secrets (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id        UUID REFERENCES brands(id) ON DELETE CASCADE,   -- NULL = system default
    secret_type     secret_type NOT NULL,
    encrypted_value BYTEA NOT NULL,             -- AES-256 encrypted
    last_four_chars VARCHAR(4),                 -- for masked display
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(brand_id, secret_type)               -- one secret per type per brand
);

CREATE INDEX idx_secrets_brand_id ON secrets(brand_id);
CREATE INDEX idx_secrets_type ON secrets(secret_type);
```

---

### 20. prompt_versions

```sql
CREATE TABLE prompt_versions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id        UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    version_number  INTEGER NOT NULL,
    content         TEXT NOT NULL,
    annotation      TEXT,                       -- "Tweaked tone for Diwali campaign"
    is_live         BOOLEAN DEFAULT false,
    is_draft        BOOLEAN DEFAULT false,
    created_by      UUID NOT NULL REFERENCES users(id),
    published_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(brand_id, version_number)
);

CREATE INDEX idx_pv_brand_id ON prompt_versions(brand_id);
CREATE INDEX idx_pv_is_live ON prompt_versions(is_live);
```

**Constraint:** Only one row per brand should have `is_live = true`. Enforced in application logic (swap on publish).

---

### 21. embedding_sync_status

```sql
CREATE TABLE embedding_sync_status (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id        UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    entity_type     entity_type NOT NULL,
    entity_id       UUID NOT NULL,
    status          embedding_status DEFAULT 'pending',
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(entity_type, entity_id)
);

CREATE INDEX idx_ess_brand_id ON embedding_sync_status(brand_id);
CREATE INDEX idx_ess_status ON embedding_sync_status(status);
```

---

### 22. embeddings (pgvector)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE embeddings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id        UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    entity_type     entity_type NOT NULL,
    entity_id       UUID NOT NULL,
    content         TEXT,                           -- source text (for debugging)
    embedding       vector(1024),                   -- adjust dimension per model
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_emb_brand_id ON embeddings(brand_id);
CREATE INDEX idx_emb_entity ON embeddings(entity_type, entity_id);

-- Vector similarity search index (HNSW is faster than IVFFlat for our scale)
CREATE INDEX idx_emb_vector ON embeddings USING hnsw (embedding vector_cosine_ops);
```

**All vector searches MUST include `WHERE brand_id = ?`** for brand isolation.

---

## Log Tables

Append-only. No `updated_at` — logs are immutable.

---

### 23. admin_activity_logs

```sql
CREATE TABLE admin_activity_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id),
    brand_id        UUID REFERENCES brands(id),         -- NULL for system-wide actions
    action_type     admin_action_type NOT NULL,
    entity_type     VARCHAR(100),                       -- "product", "brand", "tone_settings"
    entity_id       UUID,
    entity_name     VARCHAR(255),
    ip_address      VARCHAR(45),                        -- supports IPv6
    before_state    JSONB,
    after_state     JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_aal_user_id ON admin_activity_logs(user_id);
CREATE INDEX idx_aal_brand_id ON admin_activity_logs(brand_id);
CREATE INDEX idx_aal_action_type ON admin_activity_logs(action_type);
CREATE INDEX idx_aal_created_at ON admin_activity_logs(created_at);
```

---

### 24. error_logs

```sql
CREATE TABLE error_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id        UUID REFERENCES brands(id),         -- NULL for system-wide
    channel         channel_type,
    error_type      error_type NOT NULL,
    description     TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_el_brand_id ON error_logs(brand_id);
CREATE INDEX idx_el_error_type ON error_logs(error_type);
CREATE INDEX idx_el_created_at ON error_logs(created_at);
```

---

### 25. compliance_logs

```sql
CREATE TABLE compliance_logs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id            UUID NOT NULL REFERENCES brands(id),
    conversation_id     UUID REFERENCES conversations(id) ON DELETE SET NULL,
    message_id          UUID REFERENCES messages(id) ON DELETE SET NULL,
    original_response   TEXT NOT NULL,
    replacement         TEXT NOT NULL,
    reason              TEXT NOT NULL,
    rule_triggered_id   UUID REFERENCES compliance_rules(id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_cl_brand_id ON compliance_logs(brand_id);
CREATE INDEX idx_cl_created_at ON compliance_logs(created_at);
```

---

### 26. moderation_logs

```sql
CREATE TABLE moderation_logs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id            UUID NOT NULL REFERENCES brands(id),
    user_identifier     TEXT,
    blocked_input       TEXT NOT NULL,
    reason              moderation_reason NOT NULL,
    action_taken        moderation_response NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ml_brand_id ON moderation_logs(brand_id);
CREATE INDEX idx_ml_reason ON moderation_logs(reason);
CREATE INDEX idx_ml_user_id ON moderation_logs(user_identifier);
CREATE INDEX idx_ml_created_at ON moderation_logs(created_at);
```

---

### 27. rag_retrieval_logs

```sql
CREATE TABLE rag_retrieval_logs (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id                UUID NOT NULL REFERENCES brands(id),
    conversation_id         UUID REFERENCES conversations(id) ON DELETE SET NULL,
    message_id              UUID REFERENCES messages(id) ON DELETE SET NULL,
    user_query              TEXT NOT NULL,
    chunks_retrieved        JSONB DEFAULT '[]',     -- [{entity_type, entity_id, entity_name, score, excerpt}]
    chunks_retrieved_count  INTEGER DEFAULT 0,
    top_similarity_score    FLOAT,
    hit_threshold           BOOLEAN DEFAULT false,  -- did any chunk meet the threshold?
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_rrl_brand_id ON rag_retrieval_logs(brand_id);
CREATE INDEX idx_rrl_hit_threshold ON rag_retrieval_logs(hit_threshold);
CREATE INDEX idx_rrl_created_at ON rag_retrieval_logs(created_at);
```

---

### 28. recommendation_rule_logs

```sql
CREATE TABLE recommendation_rule_logs (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id                UUID NOT NULL REFERENCES brands(id),
    conversation_id         UUID REFERENCES conversations(id) ON DELETE SET NULL,
    user_input_summary      TEXT,
    skin_type               skin_type,
    concerns                JSONB DEFAULT '[]',
    matched_products        JSONB DEFAULT '[]',     -- [{product_id, score}]
    matched_count           INTEGER DEFAULT 0,
    excluded_products       JSONB DEFAULT '[]',     -- [{product_id, reason, rule_id}]
    excluded_count          INTEGER DEFAULT 0,
    applied_filters         JSONB DEFAULT '{}',
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_rlg_brand_id ON recommendation_rule_logs(brand_id);
CREATE INDEX idx_rlg_created_at ON recommendation_rule_logs(created_at);
```

---

### 29. api_usage_logs

```sql
CREATE TABLE api_usage_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id        UUID NOT NULL REFERENCES brands(id),
    api_type        api_usage_type NOT NULL,
    tokens_in       INTEGER,            -- Claude calls
    tokens_out      INTEGER,            -- Claude calls
    chunks_count    INTEGER,            -- Embedding calls
    model           VARCHAR(100),
    latency_ms      INTEGER,            -- response time in milliseconds
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_aul_brand_id ON api_usage_logs(brand_id);
CREATE INDEX idx_aul_api_type ON api_usage_logs(api_type);
CREATE INDEX idx_aul_created_at ON api_usage_logs(created_at);
```

---

## Bot Protection Tables

---

### 30. ip_block_list

```sql
CREATE TABLE ip_block_list (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ip_address      VARCHAR(45) NOT NULL,       -- supports IPv6
    brand_id        UUID REFERENCES brands(id), -- NULL = system-wide block
    blocked_by      UUID REFERENCES users(id),
    reason          TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(ip_address, brand_id)
);

CREATE INDEX idx_ibl_ip ON ip_block_list(ip_address);
```

---

### 31. user_block_list

```sql
CREATE TABLE user_block_list (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_identifier     TEXT NOT NULL,
    brand_id            UUID REFERENCES brands(id),
    blocked_by          UUID REFERENCES users(id),
    reason              TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_identifier, brand_id)
);

CREATE INDEX idx_ubl_user_id ON user_block_list(user_identifier);
```

---

### 32. notifications

```sql
CREATE TABLE notifications (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID REFERENCES users(id),     -- NULL = broadcast to all admins
    brand_id            UUID REFERENCES brands(id),
    notification_type   notification_type NOT NULL,
    title               VARCHAR(255) NOT NULL,
    message             TEXT NOT NULL,
    is_read             BOOLEAN DEFAULT false,
    action_url          TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notif_user_id ON notifications(user_id);
CREATE INDEX idx_notif_is_read ON notifications(is_read);
CREATE INDEX idx_notif_created_at ON notifications(created_at);
```

---

## Widget Analytics

---

### 33. widget_events

Tracks user interactions inside the chat widget — needed for click-through rate, funnel analysis, and conversion tracking in analytics.

```sql
CREATE TABLE widget_events (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id            UUID NOT NULL REFERENCES brands(id),
    conversation_id     UUID REFERENCES conversations(id),
    session_id          VARCHAR(255),
    event_type          VARCHAR(50) NOT NULL,   -- product_card_click, purchase_link_click, quiz_start, quiz_complete, routine_view, lead_form_shown, lead_form_submitted, lead_form_skipped
    event_data          JSONB DEFAULT '{}',     -- {product_id, product_name, step, etc.}
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_we_brand_id ON widget_events(brand_id);
CREATE INDEX idx_we_event_type ON widget_events(event_type);
CREATE INDEX idx_we_created_at ON widget_events(created_at);
```

---

## Phase 2 Tables

These tables are designed now but implemented when Phase 2 begins. The architecture supports them without rework.

---

### P1. channel_configs

WhatsApp and Instagram connection settings per brand.

```sql
CREATE TABLE channel_configs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id        UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    channel         channel_type NOT NULL,
    is_connected    BOOLEAN DEFAULT false,
    phone_number    VARCHAR(20),            -- WhatsApp
    page_name       VARCHAR(255),           -- Instagram
    webhook_url     TEXT,                   -- system-generated, read-only
    config          JSONB DEFAULT '{}',     -- flexible per-channel settings
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(brand_id, channel)
);
```

---

### P2. whatsapp_template_messages

Approved outbound WhatsApp message templates per brand.

```sql
CREATE TABLE whatsapp_template_messages (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id            UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    template_name       VARCHAR(255) NOT NULL,
    template_body       TEXT NOT NULL,
    approval_status     VARCHAR(50) DEFAULT 'pending',  -- pending, approved, rejected
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_wtm_brand_id ON whatsapp_template_messages(brand_id);
```

---

### P3. agent_brand_configs

Human agent availability settings per brand.

```sql
CREATE TABLE agent_brand_configs (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id                UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    agent_user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    availability_start      TIME,
    availability_end        TIME,
    availability_timezone   VARCHAR(50) DEFAULT 'UTC',
    outside_hours_message   TEXT,
    is_available            BOOLEAN DEFAULT true,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(brand_id, agent_user_id)
);

CREATE INDEX idx_abc_brand_id ON agent_brand_configs(brand_id);
```

---

### P4. webhook_configs

Outbound webhook URLs per event per brand.

```sql
CREATE TABLE webhook_configs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id        UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    event_type      webhook_event_type NOT NULL,
    url             TEXT NOT NULL,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(brand_id, event_type)
);

CREATE INDEX idx_wc_brand_id ON webhook_configs(brand_id);
```

---

### P5. crm_integrations

CRM connection and export settings per brand.

```sql
CREATE TABLE crm_integrations (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id            UUID NOT NULL UNIQUE REFERENCES brands(id) ON DELETE CASCADE,
    crm_type            VARCHAR(50),        -- shopify, hubspot, klaviyo, mailchimp
    config              JSONB DEFAULT '{}', -- connection details
    is_connected        BOOLEAN DEFAULT false,
    export_schedule     VARCHAR(20) DEFAULT 'manual',   -- manual, daily, weekly
    export_format       VARCHAR(10) DEFAULT 'csv',      -- csv, json
    last_sync_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);
```

---

### P6. ab_tests

A/B test definitions.

```sql
CREATE TABLE ab_tests (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id            UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    name                VARCHAR(255) NOT NULL,
    test_type           ab_test_type NOT NULL,
    status              ab_test_status DEFAULT 'draft',
    traffic_split_pct   INTEGER DEFAULT 50,
    winner_variant_id   UUID,
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_abt_brand_id ON ab_tests(brand_id);
CREATE INDEX idx_abt_status ON ab_tests(status);
```

---

### P7. ab_test_variants

Variants within an A/B test with their metrics.

```sql
CREATE TABLE ab_test_variants (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ab_test_id      UUID NOT NULL REFERENCES ab_tests(id) ON DELETE CASCADE,
    variant_name    VARCHAR(10) NOT NULL,   -- 'A', 'B'
    config          JSONB NOT NULL,         -- the variant's prompt/tone/rules config
    impressions     INTEGER DEFAULT 0,
    conversions     INTEGER DEFAULT 0,
    engagement_score FLOAT,
    fallback_rate   FLOAT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_abtv_test_id ON ab_test_variants(ab_test_id);
```

---

### P8. seo_configs

SEO and public FAQ settings per brand.

```sql
CREATE TABLE seo_configs (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id                UUID NOT NULL UNIQUE REFERENCES brands(id) ON DELETE CASCADE,
    public_faq_enabled      BOOLEAN DEFAULT false,
    url_structure           VARCHAR(20) DEFAULT 'path',     -- subdomain, path
    sitemap_url             TEXT,
    allow_indexing           BOOLEAN DEFAULT false,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);
```

---

### P9. entity_versions

Full versioning and rollback for all entities (brand configs, products, FAQs, routines, compliance rules, image styles).

```sql
CREATE TABLE entity_versions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id        UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    entity_type     VARCHAR(50) NOT NULL,   -- brand_config, product, faq, routine, compliance_rule, image_style
    entity_id       UUID NOT NULL,
    version_number  INTEGER NOT NULL,
    data            JSONB NOT NULL,         -- full entity snapshot
    reason          TEXT,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(entity_type, entity_id, version_number)
);

CREATE INDEX idx_ev_brand_id ON entity_versions(brand_id);
CREATE INDEX idx_ev_entity ON entity_versions(entity_type, entity_id);
```

---

## Relationship Map

```
brands (root)
├── brand_configs             (1:1)
├── tone_settings             (1:1)
├── brand_image_styles        (1:1)
├── moderation_configs        (1:1)
├── products                  (1:many)
│   ├── product_skin_types        (1:many)
│   └── product_concerns          (1:many)
├── faqs                      (1:many)
├── routines                  (1:many)
│   └── routine_steps             (1:many) → references products
├── compliance_rules          (1:many)
├── recommendation_rules      (1:many)
├── conversations             (1:many)
│   └── messages                  (1:many)
├── leads                     (1:many) → references conversations
├── prompt_versions           (1:many) → references users
├── embedding_sync_status     (1:many)
├── embeddings                (1:many)
├── secrets                   (1:many, nullable brand_id for system defaults)
├── widget_events             (1:many)
├── All log tables            (1:many)
├── ip_block_list             (1:many)
├── user_block_list           (1:many)
├── notifications             (1:many)
│
│  Phase 2:
├── channel_configs           (1:many, one per channel)
├── whatsapp_template_messages(1:many)
├── agent_brand_configs       (1:many) → references users
├── webhook_configs           (1:many)
├── crm_integrations          (1:1)
├── ab_tests                  (1:many)
│   └── ab_test_variants          (1:many)
├── seo_configs               (1:1)
└── entity_versions           (1:many)

users (system-wide)
├── refresh_tokens         (1:many)
├── password_reset_tokens  (1:many)
├── user_brand_assignments (many:many with brands)
├── prompt_versions        (created_by)
├── admin_activity_logs    (user_id)
├── secrets                (access: super_admin only)
├── notifications          (user_id)
├── conversations          (assigned_agent_id, Phase 2)
├── agent_brand_configs    (Phase 2)
└── ip/user_block_list     (blocked_by)
```

---

## Encrypted Fields Summary

| Table | Field | Method | Purpose |
|-------|-------|--------|---------|
| leads | email_encrypted | AES-256 | PII protection |
| leads | email_hash | SHA-256 | Duplicate lookup without decrypting |
| leads | phone_encrypted | AES-256 | PII protection |
| secrets | encrypted_value | AES-256 | API keys, tokens |

---

## Table Count

| Category | Tables | Count |
|----------|--------|-------|
| Core | brands, users, user_brand_assignments | 3 |
| Auth | refresh_tokens, password_reset_tokens | 2 |
| Brand config | brand_configs, tone_settings, brand_image_styles, moderation_configs | 4 |
| Content | products, product_skin_types, product_concerns, faqs, routines, routine_steps | 6 |
| Rules | compliance_rules, recommendation_rules | 2 |
| Chat | conversations, messages | 2 |
| Leads | leads | 1 |
| Secrets | secrets | 1 |
| Prompts | prompt_versions | 1 |
| Embeddings | embedding_sync_status, embeddings | 2 |
| Logs | admin_activity, error, compliance, moderation, rag_retrieval, recommendation_rule, api_usage | 7 |
| Widget analytics | widget_events | 1 |
| Bot protection | ip_block_list, user_block_list | 2 |
| Notifications | notifications | 1 |
| **Phase 1 Total** | | **35** |
| | | |
| Phase 2: Channels | channel_configs, whatsapp_template_messages | 2 |
| Phase 2: Human escalation | agent_brand_configs | 1 |
| Phase 2: CRM & Webhooks | webhook_configs, crm_integrations | 2 |
| Phase 2: A/B Testing | ab_tests, ab_test_variants | 2 |
| Phase 2: SEO | seo_configs | 1 |
| Phase 2: Versioning | entity_versions | 1 |
| **Phase 2 Total** | | **9** |
| | | |
| **Grand Total** | | **44** |

---

## Production Safeguards

| Safeguard | How It's Handled |
|-----------|-----------------|
| GDPR conversation deletion | Log tables use `ON DELETE SET NULL` on conversation_id/message_id FKs — logs survive (for analytics) but personal data is gone |
| GDPR lead deletion | Direct delete from leads table. admin_activity_logs records who deleted and when |
| Soft delete | Products, FAQs, routines have `deleted_at` field — NULL means active, timestamp means soft-deleted. All queries must filter `WHERE deleted_at IS NULL` |
| Cascade delete brand | Deleting a brand CASCADE deletes all its content, configs, conversations, logs. This is intentional — brand deletion is total. |
| Routine → Product dependency | `routine_steps.product_id` uses `ON DELETE RESTRICT` — can't delete a product that's used in a routine. Must remove from routine first. |
| Encrypted fields | Leads email/phone and secrets use AES-256. Email lookup uses SHA-256 hash (email_hash). |
| Refresh token revocation | Tokens stored server-side with `revoked` flag. Logout = revoke. Password change = revoke all user tokens. |

---

## Pending Client Decisions That May Add Tables

These depend on client answers from Issue #2. If the client says yes, we add these tables:

| Client Question | If Answer Is | Table to Add |
|----------------|-------------|-------------|
| Q6: Custom categories per brand? | B) Yes | `product_categories` — id, brand_id, name, display_order |
| Q7: Custom skin quiz per brand? | B or C) Yes | `skin_quiz_questions` — id, brand_id, question_text, answer_options (JSONB), display_order |
| Q8: Product variants? | B) Yes | `product_variants` — id, product_id, variant_name (e.g., "50ml"), variant_value, price_override, is_in_stock |

We designed the current schema so these tables can be added without breaking anything — they're additive, not structural changes.
