# UI Screens Specification - Multi-Brand AI Chatbot Platform

> Source: SRS Complete Final (Sections 1-28, 31 pages) - Every screen, feature, and element extracted from the approved SRS.
> Purpose: Handoff to UI/Figma designer. Covers ALL screens for Phase 1 + Phase 2.
> Two products to design: (1) Admin Panel (web app) and (2) Chat Widget (embeddable component)
> Two roles in Phase 1: Super Admin and Admin. Phase 2 adds custom roles.

---

## PART 1: ADMIN PANEL (React Web App)

The admin panel is a full web dashboard for managing all brands, products, rules, and chatbot configurations. It serves two roles in Phase 1:

- **Super Admin**: Full system access across all brands. Can create/delete brands, manage users, manage secrets, view system-wide analytics.
- **Admin**: Scoped to assigned brands only. Can manage products, FAQs, routines, tone, compliance for assigned brands. Cannot create/delete brands or manage users.

> SRS Section 21.3: UI Layer uses role-based menu rendering and action button hiding. Admins only see menu items and actions they have permission for.

---

### Screen 1: Login

**Visible to**: Everyone (unauthenticated)
**SRS Reference**: Section 21.2

| Element | Details |
|---------|---------|
| Email field | Required, email validation |
| Password field | Required, masked input |
| "Login" button | Submits credentials |
| "Forgot Password?" link | Navigates to password reset flow |
| Error states | "Invalid email or password", "Account locked — try again in X minutes" |
| Brute-force lockout message | After N failed attempts (configurable), show lockout duration |

---

### Screen 2: Forgot Password

**Visible to**: Everyone (unauthenticated)
**SRS Reference**: Section 21.2

| Element | Details |
|---------|---------|
| Email field | Enter registered email |
| "Send Reset Link" button | Triggers email with time-limited reset token |
| Success message | "If this email is registered, a reset link has been sent" |
| Back to Login link | Return to login screen |

---

### Screen 3: Reset Password

**Visible to**: Users who clicked reset link in email
**SRS Reference**: Section 21.2

| Element | Details |
|---------|---------|
| New password field | With strength requirements |
| Confirm password field | Must match |
| "Reset Password" button | Saves new password |
| Expired token message | "This reset link has expired. Please request a new one." |

---

### Screen 4: Force Password Change (First Login)

**Visible to**: Newly invited users on their first login
**SRS Reference**: Section 21.2

| Element | Details |
|---------|---------|
| Message | "Welcome! Please set a new password to continue." |
| New password field | With strength requirements |
| Confirm password field | Must match |
| "Set Password & Continue" button | After which user enters the dashboard |

---

### Screen 5: Dashboard (Home)

**Visible to**: Super Admin — sees all brands. Admin — sees only assigned brands.
**SRS Reference**: Section 2.8, Section 13

| Element | Details |
|---------|---------|
| Welcome banner | "Welcome, {user name}" |
| Brand summary cards | One card per brand: brand logo, name, conversation count, active status |
| Total conversations stat | Count across all visible brands |
| Active users stat | Currently active chat sessions |
| Channel stats | Breakdown: Website / WhatsApp / Instagram message counts |
| Quick navigation | Links to frequently used sections |

**Phase 2 additions (Section 26.3):**
| Element | Details |
|---------|---------|
| Fallback rate | % of queries triggering fallback per brand |
| Cross-brand comparison | Side-by-side brand performance |

---

### Screen 6: Brand Manager — List View

**Visible to**: Super Admin — full CRUD. Admin — read-only view of assigned brands.
**SRS Reference**: Section 2.1, 2.8

| Element | Details |
|---------|---------|
| Brand list/cards | Each showing: logo, name, status (active/inactive), number of products, creation date |
| "Add New Brand" button | Super Admin only |
| Search/filter bar | Search by brand name |
| Brand status indicator | Green = active, Red = inactive |
| Per-brand actions | Edit / Delete (Super Admin only) |
| Emergency Override indicator | Shows if brand is in safe-mode or disabled |

---

### Screen 7: Brand Manager — Add/Edit Brand

**Visible to**: Super Admin only (create/delete). Admin can edit assigned brand's basic info.
**SRS Reference**: Section 2.1, 2.8

| Element | Details |
|---------|---------|
| Brand name | Text input, required |
| Brand slug | Auto-generated from name, editable. Used in URLs and widget embed code |
| Brand logo | Image upload (PNG/SVG), preview thumbnail |
| Primary color | Color picker + hex input |
| Secondary color | Color picker + hex input |
| Accent color | Color picker + hex input |
| Brand description | Textarea, 2-3 sentences describing brand identity |
| Active/Inactive toggle | Enable or disable the brand |
| "Save" / "Create" button | |
| "Delete Brand" button | Super Admin only. Confirmation dialog required: "This will permanently delete all brand data including products, FAQs, routines, conversations, and leads." |

---

### Screen 8: Brand Configuration

**Visible to**: Super Admin — all brands. Admin — assigned brands only.
**SRS Reference**: Section 2.4, 2.5, 11.2, 12

| Element | Details |
|---------|---------|
| **Response Settings** | |
| Response length | Dropdown: Short / Medium / Long |
| Max tokens per response | Number input (e.g., 500, 1000) |
| **Messages** | |
| Greeting message | Textarea — brand's welcome message to users |
| Sign-off message | Textarea — brand's closing message |
| Fallback message | Textarea — shown when AI cannot answer safely |
| Fallback tone profile | Textarea — tone instructions for fallback responses |
| **Moderation Settings** (SRS Section 20.3) | |
| Moderation sensitivity | Dropdown: Low / Medium / High |
| Response on block | Dropdown: Silent drop / Polite refusal / Brand fallback message |
| **Lead Capture Settings** (SRS Section 22.1) | |
| Capture trigger | Dropdown: On welcome / After N messages / On intent detection / Manual prompt |
| N messages threshold | Number input (only shown if "After N messages" selected) |
| Phone field enabled | Toggle — whether phone field appears in lead form |
| GDPR consent text | Textarea — editable consent checkbox text per brand |
| Skip option enabled | Toggle — whether users can skip the lead form |
| **Rate Limiting** (SRS Section 12) | |
| Per-user message limit | Number input (e.g., 30 per minute) |
| **Emergency Override** (SRS Section 2.8) | |
| "Disable Chatbot" button | Instantly disables this brand's chatbot. Confirmation dialog. |
| "Switch to Safe Mode" button | Chatbot only serves fallback messages. Confirmation dialog. |
| "Resume Normal Mode" button | Restores chatbot to normal operation |
| Current status indicator | Normal / Safe Mode / Disabled |

---

### Screen 9: Tone & Personality Settings

**Visible to**: Super Admin — all brands. Admin — assigned brands only.
**SRS Reference**: Section 2.4

**Section A: Core Tone Settings**
| Element | Details |
|---------|---------|
| Emotional style | Dropdown or multi-select: Warm / Clinical / Luxurious / Friendly (configurable) |
| Communication style | Dropdown: Formal / Casual |
| Emoji usage | Toggle: Allow / Disallow |
| Preferred vocabulary | Tag input — add/remove preferred words/phrases. Example: "radiant", "nourishing" |
| Avoided vocabulary | Tag input — add/remove avoided words/phrases. Example: "cheap", "basic" |

**Section B: Micro-Tone Rules** (SRS Section 2.4)
| Element | Details |
|---------|---------|
| Softness level | Dropdown: Gentle / Neutral / Direct |
| Sensory language | Toggle: Enable / Restrict. When enabled, allows words like "silky", "velvety", "luminous" |
| Emotional cues | Multi-select checkboxes: Calming / Uplifting / Nurturing / Confident |
| Restricted adjectives | Tag input — list of adjectives that must NOT be used. Example: "cheap", "basic", "harsh" |
| Clinical language control | Toggle: Allow clinical/medical terms / Block by default |
| Harsh word blocking | Toggle: Enable / Disable. Blocks words that feel aggressive, blunt, or non-premium |

**Section C: Override Controls**
| Element | Details |
|---------|---------|
| "Override Tone Now" button | Applies all tone changes immediately without restart. Shows confirmation: "Changes are live immediately." |
| "Override Vocabulary Now" button | Applies vocabulary changes immediately |

---

### Screen 10: Product Manager — List View

**Visible to**: Super Admin — all brands. Admin — assigned brands only.
**SRS Reference**: Section 2.3, 2.8, Section 17

| Element | Details |
|---------|---------|
| Brand selector | Dropdown to switch between brands (Super Admin sees all, Admin sees assigned) |
| Product list/table | Columns: Image thumbnail, Name, Category, Price, Stock Status, Embedding Status, Actions |
| "Add Product" button | Opens add product form |
| Search bar | Search by product name |
| Filters | Filter by: category, skin type, concern, stock status, embedding status |
| Pagination | Page controls with configurable items per page |
| Embedding status badge | Per product: Green "Synced" / Yellow "Pending" / Red "Failed" with retry button |
| Bulk actions | Select multiple → Delete / Update stock status |

---

### Screen 11: Product Manager — Add/Edit Product

**Visible to**: Super Admin — all brands. Admin — assigned brands only.
**SRS Reference**: Section 2.3, 2.8, Section 24.1

| Element | Details |
|---------|---------|
| Product name | Text input, required |
| Description | Rich textarea, required |
| Ingredients | Tag input or textarea — list of ingredients |
| Price | Number input with currency |
| Category | Dropdown (e.g., Cleansers, Toners, Serums, Moisturizers, Masks, Sunscreen) |
| Product image | Image upload with preview. Uploads to S3, stores URL. |
| **Skin type tags** | Multi-select checkboxes: Oily / Dry / Combination / Sensitive / Normal |
| **Concern tags** | Multi-select checkboxes: Acne / Aging / Hydration / Hyperpigmentation / Sensitivity / Dullness |
| Stock status | Toggle: In Stock / Out of Stock. Out-of-stock products are excluded from recommendations. |
| Priority score | Number input — higher score = surfaces first in recommendations for matching users |
| "Save" button | Saves to PostgreSQL. Triggers async embedding to vector DB. |
| Embedding status | Shows current sync status after save |

**Note (SRS Section 17):** When product is saved, the system automatically chunks text and embeds into the brand's vector DB namespace. Admin sees embedding status update (pending → completed/failed).

---

### Screen 12: FAQ Manager

**Visible to**: Super Admin — all brands. Admin — assigned brands only.
**SRS Reference**: Section 2.3, 2.8, Section 17

| Element | Details |
|---------|---------|
| Brand selector | Dropdown to switch brands |
| FAQ list | Columns: Question (truncated), Category, Embedding Status, Actions |
| "Add FAQ" button | Opens add form |
| Search bar | Search by question text |
| Filter by category | Dropdown |
| **Add/Edit FAQ form:** | |
| Question | Text input, required |
| Answer | Rich textarea, required |
| Category | Dropdown or text input (e.g., Ingredients, Shipping, Returns, Usage, General) |
| "Save" button | Saves to DB, triggers async embedding |
| Embedding status badge | Synced / Pending / Failed |

---

### Screen 13: Routine Builder — List View

**Visible to**: Super Admin — all brands. Admin — assigned brands only.
**SRS Reference**: Section 2.6, 2.8

| Element | Details |
|---------|---------|
| Brand selector | Dropdown to switch brands |
| Routine list | Columns: Routine Name, Target Skin Type, Number of Steps, Active Status, Actions |
| "Create Routine" button | Opens routine creation form |
| Active/Inactive toggle | Per routine |

---

### Screen 14: Routine Builder — Create/Edit Routine

**Visible to**: Super Admin — all brands. Admin — assigned brands only.
**SRS Reference**: Section 2.6, Section 24

| Element | Details |
|---------|---------|
| Routine name | Text input. Example: "Morning Glow Routine" |
| Description | Textarea |
| Target skin type | Dropdown: Oily / Dry / Combination / Sensitive / Normal |
| Target concerns | Multi-select: Acne / Aging / Hydration / Hyperpigmentation / Sensitivity / Dullness |
| Active toggle | Enable/disable this routine |
| **Steps section** | |
| Step list | Drag-and-drop reorderable list |
| Each step: Step number | Auto-assigned based on order |
| Each step: Step name | Dropdown: Cleanse / Tone / Serum / Treat / Moisturize / Sunscreen / Custom |
| Each step: Product | Dropdown — select from brand's product catalog. Shows product name + image thumbnail |
| "Add Step" button | Adds a new step to the end |
| "Remove Step" button | Per step, with confirmation |
| "Save Routine" button | |
| **Override Control** | |
| "Override Routines Now" button | Updates take effect immediately |

---

### Screen 15: Compliance & Safety Rules

**Visible to**: Super Admin — all brands. Admin — assigned brands only.
**SRS Reference**: Section 2.5, 2.8

**Section A: Rule List**
| Element | Details |
|---------|---------|
| Brand selector | Dropdown |
| Rule table | Columns: Rule Type, Value/Phrase, Active Status, Actions |
| Filter by rule type | Dropdown: Blocked Phrase / Allowed Phrase / Blocked Topic / Conversation Boundary |
| "Add Rule" button | Opens add form |

**Section B: Add/Edit Rule**
| Element | Details |
|---------|---------|
| Rule type | Dropdown: Blocked Phrase / Allowed Phrase / Blocked Topic / Conversation Boundary |
| Value | Text input — the phrase, topic, or boundary description |
| Active toggle | Enable/disable this rule |
| "Save" button | |

**Section C: Conversation Boundaries** (SRS Section 2.5)
| Element | Details |
|---------|---------|
| No medical claims | Toggle (always recommended ON) |
| No over-explaining | Toggle |
| No aggressive upselling | Toggle |
| No unnecessary details | Toggle |
| No medical tone | Toggle (unless clinical language explicitly allowed in tone settings) |

**Section D: Override Control**
| Element | Details |
|---------|---------|
| "Override Compliance Now" button | All changes take effect immediately |

**Section E: Moderation Allow/Block Lists** (SRS Section 20.3)
| Element | Details |
|---------|---------|
| Allow list | Tag input — phrases/patterns always allowed through moderation |
| Block list | Tag input — phrases/patterns always blocked by moderation |
| Prompt injection patterns | Expandable list of detected patterns; admin can add new patterns |

---

### Screen 16: Recommendation Rules

**Visible to**: Super Admin — all brands. Admin — assigned brands only.
**SRS Reference**: Section 24

**Section A: Rule List**
| Element | Details |
|---------|---------|
| Brand selector | Dropdown |
| Rule table | Columns: Rule Type, Description, Active Status, Actions |
| Filter by rule type | Dropdown: Skin Type Mapping / Concern Mapping / Priority / Exclusion / Conflict / Suitability |
| "Add Rule" button | Opens add form |

**Section B: Add/Edit Rule**
| Element | Details |
|---------|---------|
| Rule type dropdown | Skin Type Mapping / Concern Mapping / Priority / Exclusion / Conflict / Suitability Matrix |
| **For Exclusion Rule:** | |
| Product selector | Dropdown — select product to exclude |
| Condition | "Do not recommend for:" + skin type or concern selector |
| **For Conflict Rule:** | |
| Product A selector | Dropdown |
| Product B selector | Dropdown |
| Reason | Text input. Example: "Retinol and Vitamin C should not be used together" |
| **For Priority Rule:** | |
| Product selector | Dropdown |
| Priority score | Number input |
| Active toggle | |

**Section C: Rule Testing** (SRS Section 24.4)
| Element | Details |
|---------|---------|
| "Test Rules" button / panel | |
| Simulated skin type | Dropdown |
| Simulated concerns | Multi-select |
| Simulated preferences | Text input or multi-select |
| "Run Test" button | Executes rules engine with simulated input |
| Result display | Shows: matched products (ranked), applied filters, excluded products with reasons |

**Section D: Bulk Import** (SRS Section 24.4)
| Element | Details |
|---------|---------|
| CSV upload | File upload for bulk rule import |
| Template download | "Download CSV Template" link |
| Import result | Shows: X rules imported, Y errors with details |

---

### Screen 17: Image-Style Rules

**Visible to**: Super Admin — all brands. Admin — assigned brands only.
**SRS Reference**: Section 2.3

| Element | Details |
|---------|---------|
| Brand selector | Dropdown |
| **Image style profile** | Dropdown or radio: Soft-Luxury / Clinical-Luxury / K-Beauty Minimal / Botanical / Modern-Clean / Custom |
| **Product card styling** | |
| Card edges | Radio: Rounded / Sharp |
| Background color | Color picker |
| Overlay style | Dropdown options (none, gradient, shadow) |
| **Routine card styling** | |
| Same options as product cards | |
| **UI element styling** | |
| Button style | Rounded/sharp, color |
| Card background | Color picker |
| Overall aesthetic | Description or reference image upload |
| Preview panel | Live preview showing how product cards and UI elements will look with current settings |

---

### Screen 18: Prompt Editor

**Visible to**: Super Admin — all brands. Admin — assigned brands only.
**SRS Reference**: Section 25

**Section A: Editor**
| Element | Details |
|---------|---------|
| Brand selector | Dropdown |
| **Direct editing view** | Full-text editor showing the complete assembled system prompt |
| **Composed view** | Visual breakdown showing labeled sections: [Brand Identity], [Tone Rules], [Vocabulary], [Compliance], [Fallback Instructions]. Each section highlighted/collapsible |
| Status indicator | "Draft (unsaved)" / "Draft (saved)" / "Live" |
| "Save Draft" button | Saves without affecting live prompt |
| "Publish" button | Pushes draft to live. Confirmation: "This will replace the current live prompt immediately." |
| Syntax validation | Warns if prompt appears malformed before publish |

**Section B: Live Preview** (SRS Section 25.1)
| Element | Details |
|---------|---------|
| Sample user input | Text input for test message |
| "Test Prompt" button | Sends test message against the current draft prompt |
| AI response preview | Shows what the AI would respond |
| Context panel | Shows what RAG context was retrieved for the test |

**Section C: Version History** (SRS Section 25.2)
| Element | Details |
|---------|---------|
| Version list | Table: Version #, Published By, Date/Time, Annotation, "Live" badge on current |
| Retention | Last 20 versions shown (Phase 1) |
| "Restore" button | Per version. Confirmation: "This will make version X the live prompt." |
| "View" button | Opens read-only view of that version |
| Annotation field | Optional comment per version. Example: "Tweaked tone for Diwali campaign" |

**Section D: Diff View** (SRS Section 25.2)
| Element | Details |
|---------|---------|
| Version A selector | Dropdown |
| Version B selector | Dropdown |
| Side-by-side diff | Added text highlighted green, removed text highlighted red |

---

### Screen 19: Channel Configuration

**Visible to**: Super Admin — all brands. Admin — assigned brands only.
**SRS Reference**: Section 2.7, 2.8

**Section A: Website Chat Widget** (Phase 1)
| Element | Details |
|---------|---------|
| Embed code display | Read-only code block: `<script src="..."></script>` with brand_slug |
| "Copy Embed Code" button | Copies to clipboard |
| Widget preview | Shows how the widget will look with brand's colors/logo |

**Section B: WhatsApp Integration** (Phase 2)
| Element | Details |
|---------|---------|
| Status | Connected / Not Connected |
| Phone number | Display connected number per brand |
| Webhook URL | Read-only, for client to configure in Meta dashboard |
| "Connect" / "Disconnect" button | |
| Template messages list | Approved outbound templates |

**Section C: Instagram Integration** (Phase 2)
| Element | Details |
|---------|---------|
| Status | Connected / Not Connected |
| Instagram page | Display connected page name |
| "Connect" / "Disconnect" button | |

---

### Screen 20: Conversation Logs

**Visible to**: Super Admin — all brands. Admin — assigned brands only.
**SRS Reference**: Section 13, Section 2.8

**Section A: Conversation List**
| Element | Details |
|---------|---------|
| Brand selector | Dropdown |
| Conversation table | Columns: Session ID (truncated), Channel (Website/WhatsApp/Instagram), Start Time, Message Count, Flagged Status, Actions |
| Filters | Channel dropdown, Date range picker, Flagged only toggle |
| Search | Search within conversation content |
| Pagination | |

**Section B: Conversation Detail**
| Element | Details |
|---------|---------|
| Conversation header | Session ID, Channel, Brand, Start/End time, User identifier (masked if lead) |
| Message thread | Chronological list of messages: user messages (left-aligned), AI responses (right-aligned), timestamps per message |
| "Flag for Review" button | Flags conversation for admin review |
| "Unflag" button | Removes flag |
| Flag reason | Optional text field when flagging |
| **Linked information:** | |
| RAG retrieval log | Expandable: shows which chunks were retrieved for each AI response, with similarity scores |
| Compliance log | Expandable: shows if any response was blocked/replaced and why |
| Moderation log | Expandable: shows if any user input was blocked and why |

---

### Screen 21: Analytics

**Visible to**: Super Admin — system-wide + per-brand. Admin — assigned brands only.
**SRS Reference**: Section 13, Section 12

**Section A: Overview** (per brand or system-wide)
| Element | Details |
|---------|---------|
| Total conversations | Count + trend chart |
| Total messages | Count + trend chart |
| Active sessions | Current count |
| Average messages per conversation | |

**Section B: Message Volume**
| Element | Details |
|---------|---------|
| Time-series chart | Messages over time (daily/weekly/monthly toggle) |
| Channel breakdown | Bar/pie chart: Website vs WhatsApp vs Instagram |

**Section C: Popular Questions**
| Element | Details |
|---------|---------|
| Top questions list | Ranked list of most frequently asked questions with count |

**Section D: Response Quality**
| Element | Details |
|---------|---------|
| Fallback rate (Phase 1 basic) | Count of responses that used fallback message |
| Compliance block count | Responses blocked by compliance filter |
| Average response time | Chart showing response latency |

**Section E: API Usage** (SRS Section 12)
| Element | Details |
|---------|---------|
| Claude API calls | Count per brand, with token usage (input + output tokens) |
| Embedding API calls | Count per brand |
| Cost estimate | Approximate cost based on token usage (if token pricing is configured) |
| Time period selector | Last 7 days / 30 days / 90 days / Custom range |

**Phase 2 additions (Section 26.3):**
| Element | Details |
|---------|---------|
| Routine completion rate | % of users completing skin quiz |
| Click-through rate | Clicks on product cards/purchase links |
| Drop-off analysis | Funnel chart showing where users leave |
| Conversion tracking | Lead-to-purchase (with CRM integration) |
| Cross-brand comparison | Side-by-side brand performance dashboard |
| Cohort analysis | User behavior over time |

---

### Screen 22: Lead Management

**Visible to**: Super Admin — all brands. Admin — assigned brands only.
**SRS Reference**: Section 22

| Element | Details |
|---------|---------|
| Brand selector | Dropdown |
| Lead table | Columns: Name, Email (masked: pr***@example.com), Phone (masked if captured), Channel, Consent Status, Date Captured, Actions |
| Filters | Date range, Channel (Website/WhatsApp/Instagram) |
| Search | Search by name or email |
| Sort | By date, by name |
| Pagination | |
| "Export CSV" button | Exports filtered leads as CSV file |
| Per-lead actions | View details / Delete (GDPR right to delete, confirmation: "This will permanently delete this lead's data") |
| **Lead detail view:** | |
| Full name | Displayed |
| Full email | Displayed (unmasked in detail view for authorized users) |
| Phone | Displayed if captured |
| Channel source | Website / WhatsApp / Instagram |
| Consent given | Yes/No with consent text shown |
| Capture date | |
| Associated conversation link | Link to the conversation where lead was captured |

---

### Screen 23: User Management

**Visible to**: Super Admin ONLY. Admin cannot see this screen.
**SRS Reference**: Section 21

| Element | Details |
|---------|---------|
| User list table | Columns: Email, Role (Super Admin / Admin), Assigned Brands, Status (Active / Locked), Last Login, Actions |
| "Invite New Admin" button | Opens invite form |
| **Invite form:** | |
| Email address | Text input, required |
| Role | Dropdown: Super Admin / Admin |
| Assign brands | Multi-select — which brands this admin can access (only shown if role = Admin) |
| "Send Invitation" button | Sends email invitation with temporary password / setup link |
| **Per-user actions:** | |
| Edit brands | Change assigned brands |
| Revoke access | Deactivate user. Confirmation dialog. |
| Delete user | Permanent removal. Confirmation dialog. |
| View activity log | Opens activity log filtered to this user |
| Unlock account | If user is locked due to brute-force protection |

**Phase 2 additions (Section 26.6):**
| Element | Details |
|---------|---------|
| Custom roles | Create new roles beyond Super Admin / Admin (e.g., Brand Manager, Content Editor, Viewer) |
| Granular permissions | Per-feature permission checkboxes (read-only on logs, edit-only on products, publish rights) |
| Per-brand role assignment | A single user can hold different roles across different brands |
| Permission templates | Pre-defined permission bundles for common use cases |

---

### Screen 24: Secret Management

**Visible to**: Super Admin ONLY. Admin cannot see this screen.
**SRS Reference**: Section 23

| Element | Details |
|---------|---------|
| Secrets table | Columns: Secret Type, Brand (or "System Default"), Status (Set / Not Set), Last 4 Chars (e.g., "****ABCD"), Last Updated, Actions |
| "Add Secret" button | Opens add form |
| **Add Secret form:** | |
| Secret type | Dropdown: Anthropic API Key / Embeddings API Key / Meta WhatsApp Token (Phase 2) / Meta Instagram Token (Phase 2) / Webhook Signing Secret (Phase 2) |
| Brand | Dropdown: System Default / specific brand name |
| Secret value | Password-type input field. **Value is NOT retained after submit.** |
| "Save" button | Encrypts immediately and saves |
| **Per-secret actions:** | |
| Update | Opens replace form — old value is NEVER shown. Only new value input. |
| Delete | Confirmation: "Brand will fall back to system-default key." |
| Test Connection | Button — makes a test API call using this key, shows "Connection successful" / "Connection failed: {error}" |
| View audit log | Opens audit trail for this secret (who accessed/modified/when/IP) |

**Important UI rules (SRS Section 23.2):**
- Secrets are NEVER displayed in plaintext anywhere in the admin panel
- Show only "set/not-set" status or last-four-characters
- The input field for secret value must NOT auto-complete or retain value after submission

---

### Screen 25: Admin Activity Logs

**Visible to**: Super Admin — all activity. Admin — own brand activity only.
**SRS Reference**: Section 13

| Element | Details |
|---------|---------|
| Activity log table | Columns: Timestamp, User (email), Action Type, Entity Type, Entity Name, Brand, IP Address |
| Filters | User dropdown, Action type dropdown, Entity type, Brand, Date range |
| Search | Search by entity name or action |
| Pagination | |
| **Log detail view (expandable row):** | |
| Before state | JSON/formatted view of entity state before the change |
| After state | JSON/formatted view of entity state after the change |
| Full action description | Human-readable description of what was changed |

Action types include: Created, Updated, Deleted, Published, Restored, Overridden, Enabled, Disabled, Invited, Revoked, Login, Failed Login, Secret Rotated

---

### Screen 26: Error Logs

**Visible to**: Super Admin — all. Admin — assigned brands only.
**SRS Reference**: Section 13

| Element | Details |
|---------|---------|
| Error log table | Columns: Timestamp, Error Type, Brand, Channel, Description, Severity |
| Filters | Error type (API Failure / Timeout / Webhook Failure / Embedding Failure), Brand, Date range |
| Error types | Claude API failure, Embeddings API failure, S3 upload failure, Timeout events, Webhook delivery failures |

---

### Screen 27: Compliance Logs

**Visible to**: Super Admin — all. Admin — assigned brands only.
**SRS Reference**: Section 13

| Element | Details |
|---------|---------|
| Compliance log table | Columns: Timestamp, Brand, Original Response (truncated), Replacement, Reason, Rule Triggered |
| Filters | Brand, Reason type, Date range |
| Detail view | Full original response, full replacement response, which compliance rule was triggered |

---

### Screen 28: Moderation Logs

**Visible to**: Super Admin — all. Admin — assigned brands only.
**SRS Reference**: Section 20

| Element | Details |
|---------|---------|
| Moderation log table | Columns: Timestamp, Brand, User Identifier (masked), Blocked Input (truncated), Reason, Action Taken |
| Filters | Brand, Reason (spam/abuse/injection/off-topic), Date range |
| Detail view | Full blocked input, detailed reason, moderation layer that caught it |
| Admin alert indicator | Highlight repeated abuse from same user identifier |
| "Block User/IP" action | Add user identifier or IP to block list directly from log |

---

### Screen 29: RAG Retrieval Logs

**Visible to**: Super Admin — all. Admin — assigned brands only.
**SRS Reference**: Section 13

| Element | Details |
|---------|---------|
| Retrieval log table | Columns: Timestamp, Brand, User Query (truncated), Chunks Retrieved Count, Top Similarity Score |
| Detail view | Full user query, list of retrieved chunks with: entity type (product/FAQ/routine), entity name, similarity score, text excerpt |
| "No context found" indicator | Highlights queries where no chunks met the similarity threshold |

---

### Screen 30: Embedding Status Dashboard

**Visible to**: Super Admin — all. Admin — assigned brands only.
**SRS Reference**: Section 17

| Element | Details |
|---------|---------|
| Brand selector | Dropdown |
| Status overview | Counts: Total entities, Synced, Pending, Failed |
| Entity list | Table: Entity Type (Product/FAQ/Routine), Entity Name, Status (Synced/Pending/Failed), Last Updated |
| Filter by status | All / Pending / Failed |
| "Retry Failed" button | Re-triggers embedding for failed items |
| "Retry All Failed" button | Batch retry |
| Error details | For failed items: show error message |

---

### Screen 31: Bot Protection & IP Management

**Visible to**: Super Admin — all. Admin — assigned brands only.
**SRS Reference**: Section 22.3

| Element | Details |
|---------|---------|
| IP Block list | Table: IP Address, Blocked Date, Blocked By, Reason |
| "Add IP to Block List" button | Manual IP blocking |
| User identifier block list | Table: User ID, Blocked Date, Reason |
| Suspicious activity alerts | List of recent bot-like activity detections |
| reCAPTCHA stats | Pass/fail rate |

---

## PHASE 2 ADMIN SCREENS

### Screen 32: Human Agent Inbox (Phase 2)

**Visible to**: Super Admin + Admin (assigned brands). Agent users (new role in Phase 2).
**SRS Reference**: Section 26.1

| Element | Details |
|---------|---------|
| Escalated conversation queue | List: User identifier, Brand, Channel, Escalation Reason, Wait Time, Status (Waiting/In Progress/Resolved) |
| Conversation detail | Full AI conversation history (context handoff) + user session state (skin type, concerns, preferences) |
| Agent reply input | Text input for human agent to reply |
| "Send Reply" button | Sends through same channel |
| "Return to AI" button | Re-hands conversation back to AI chatbot |
| Availability hours config | Per-brand: set hours when human agents are available |
| Outside-hours message | Configurable holding message per brand shown when no agents are available |
| Agent assignment | Assign conversation to specific agent |

---

### Screen 33: Advanced Analytics Dashboard (Phase 2)

**SRS Reference**: Section 26.3

| Element | Details |
|---------|---------|
| Fallback rate | % of queries triggering fallback per brand, chart over time |
| Routine completion rate | % of users completing skin quiz + routine flow |
| Click-through rate | Clicks on product cards and purchase links |
| Drop-off analysis | Funnel visualization: Welcome → Quiz Start → Quiz Complete → Product View → Purchase Link Click |
| Conversion tracking | Lead-to-purchase tracking (requires CRM integration) |
| Channel performance | Comparative performance across Website / WhatsApp / Instagram |
| Brand performance | Cross-brand comparison dashboard for the founder |
| Cohort analysis | User behavior tracked over time across sessions |

---

### Screen 34: CRM & Webhook Settings (Phase 2)

**SRS Reference**: Section 26.4

| Element | Details |
|---------|---------|
| Outbound webhooks | Configure webhook URLs per event: Lead Captured, Conversation Ended, Escalation Requested |
| Native CRM integration | Setup for one CRM (Shopify / HubSpot / Klaviyo / Mailchimp) |
| Connection status | Connected / Not Connected with test button |
| Lead export schedule | Dropdown: Manual only / Daily / Weekly |
| Export format | CSV / JSON |

---

### Screen 35: SEO & FAQ Pages (Phase 2)

**SRS Reference**: Section 26.2

| Element | Details |
|---------|---------|
| Public FAQ pages toggle | Enable/disable per brand |
| URL structure | Subdomain vs path-based brand isolation |
| schema.org markup | Auto-generated FAQPage markup preview |
| Sitemap | Auto-generated sitemap URL |
| Indexing control | Toggle: Allow / Block search engine indexing per brand |

---

### Screen 36: A/B Testing (Phase 2)

**SRS Reference**: Section 26.7

| Element | Details |
|---------|---------|
| Test list | Table: Test Name, Type (Prompt/Tone/Recommendation), Status (Draft/Running/Completed), Winner |
| Create test | Name, Type, Variant A config, Variant B config, Traffic split (%) |
| Running test metrics | Per variant: conversion, engagement, fallback rate |
| Winner declaration | Manual or automatic (statistical significance indicator) |
| Promote winner | Button to make winning variant the new default |

---

## PART 2: CHAT WIDGET (React Embeddable Component)

The chat widget is embedded on brand websites via a `<script>` tag. It must be fully branded per brand — colors, logo, card styles, everything follows the brand's configured visual identity.

**SRS Reference**: Section 6, 7, 2.3 (styling), 2.7, 14 (channel-specific behavior)

---

### Widget Screen 1: Minimized State (Chat Bubble)

| Element | Details |
|---------|---------|
| Chat bubble/icon | Floating button in bottom-right corner of the website |
| Brand color | Bubble uses brand's primary color |
| Unread message indicator | Badge showing unread count |
| Click action | Expands to Welcome Screen or Chat Interface (if session exists) |

---

### Widget Screen 2: Welcome Screen

**SRS Reference**: Section 7

| Element | Details |
|---------|---------|
| Brand logo | Displayed at top |
| Brand name | Below logo |
| Greeting message | Brand-specific welcome text from brand config |
| Quick-action buttons | Three buttons: "Browse Products" / "Skin Quiz" / "FAQ" |
| User input box | Text input at bottom for typing a message |
| Close button | Minimizes widget back to bubble |
| Brand theming | All colors, fonts, button styles match brand's configured visual identity |

---

### Widget Screen 3: Chat Interface

**SRS Reference**: Section 6, 7, 14

| Element | Details |
|---------|---------|
| Chat header | Brand logo (small) + brand name + minimize/close button |
| Message area | Scrollable area with message bubbles |
| User messages | Right-aligned bubbles in a neutral color |
| AI messages | Left-aligned bubbles in brand color |
| Typing indicator | Animated dots shown while AI is generating response |
| User input box | Text input with send button |
| Timestamp | Per message or grouped by time |
| Quick reply buttons | Shown below AI messages when applicable (e.g., "Yes" / "No" / "Tell me more") |
| **Inline Product Cards** (see Widget Screen 5) | Shown within message flow when AI recommends products |
| **Inline Routine Cards** (see Widget Screen 6) | Shown within message flow when AI suggests routines |
| Scroll to bottom | Auto-scrolls on new message; "scroll to bottom" button if user has scrolled up |

**Channel-specific formatting (SRS Section 14):**
- Website chat: Rich and detailed, full HTML, styled per brand, product cards, routine cards, quick-action buttons
- This is the richest format — WhatsApp and Instagram use their native apps (no widget needed)

---

### Widget Screen 4: Skin Quiz Flow

**SRS Reference**: Section 7, Section 2.6

| Element | Details |
|---------|---------|
| Quiz introduction | AI message explaining the quiz: "Let me help you find your perfect routine!" |
| **Question 1: Skin Type** | |
| Quick reply buttons | Oily / Dry / Combination / Sensitive / Normal |
| **Question 2: Skin Concerns** | |
| Multi-select buttons | Acne / Aging / Hydration / Hyperpigmentation / Sensitivity / Dullness |
| "Done" button | After selecting concerns |
| **Question 3: Preferences** | |
| Quick reply buttons/checkboxes | Fragrance-Free / Vegan / Budget-Friendly (brand-configurable options) |
| **Result** | |
| Personalized routine display | (see Widget Screen 6) |
| Product recommendations | (see Widget Screen 5) |

**Session personalization rules (SRS Section 15):**
- Once user answers skin type, it is stored — chatbot NEVER re-asks in the same session
- Concerns and preferences are also retained for the entire session
- Products already recommended are tracked — chatbot does NOT recommend the same product again

---

### Widget Screen 5: Product Card (Inline)

**SRS Reference**: Section 7, Section 2.3

| Element | Details |
|---------|---------|
| Product image | From S3, displayed according to brand's image-style rules (rounded/sharp edges, background color, overlay) |
| Product name | Bold text |
| Price | Formatted with currency |
| Short description | 1-2 lines truncated |
| "View Product" / "Shop Now" button | External link to brand's e-commerce page (opens in new tab) |
| Card styling | Follows brand's product card style rules (edges, background, overlay) |

---

### Widget Screen 6: Routine Display (Inline)

**SRS Reference**: Section 7, Section 2.3

| Element | Details |
|---------|---------|
| Routine title | e.g., "Your Morning Glow Routine" |
| Step cards | Vertically stacked, numbered |
| Each step: Step number + name | e.g., "Step 1: Cleanse" |
| Each step: Product card | Product image (brand-styled), name, price |
| Each step: Brief description | How to use this product in this step |
| Overall card styling | Follows brand's routine card style rules |

---

### Widget Screen 7: Lead Capture Form

**SRS Reference**: Section 22

| Element | Details |
|---------|---------|
| Form container | Modal overlay or inline within chat, based on trigger |
| Trigger | Appears based on brand config: on welcome / after N messages / on intent / manual |
| Name field | Text input, required |
| Email field | Email input, required, validation |
| Phone field | Phone input, optional (only shown if brand enables it) |
| GDPR consent checkbox | With brand-specific editable consent text |
| "Submit" button | |
| "Skip" button | Dismisses form, conversation continues normally |
| reCAPTCHA v3 | Invisible — runs on form submission |
| Honeypot fields | Hidden fields — invisible to real users, auto-filled by bots for detection |
| Success message | "Thank you! Let's continue." |

---

### Widget Screen 8: Fallback Message Display

**SRS Reference**: Section 2.5, Section 7

| Element | Details |
|---------|---------|
| Fallback message | Brand-specific message configured in admin, displayed in brand's fallback tone |
| Visual treatment | Same as regular AI message bubble but may include a subtle indicator |
| Trigger | When AI cannot answer safely, compliance violation, timeout (>8 sec), or API failure |

---

### Widget Screen 9: Error / Offline State

| Element | Details |
|---------|---------|
| Connection lost message | "Connection lost. Trying to reconnect..." |
| Reconnecting indicator | Loading spinner |
| Reconnected message | "Connected! You can continue chatting." |
| Service unavailable | "Our advisor is temporarily unavailable. Please try again shortly." |

---

## PART 3: NAVIGATION STRUCTURE

### Admin Panel — Sidebar Navigation

**Super Admin sees:**
```
Dashboard
Brand Management
  └─ All Brands (list + add/edit/delete)
[Per-Brand Section — select brand first]
  ├─ Brand Config
  ├─ Tone & Personality
  ├─ Products
  ├─ FAQs
  ├─ Routines
  ├─ Compliance Rules
  ├─ Recommendation Rules
  ├─ Image-Style Rules
  ├─ Prompt Editor
  ├─ Channel Config
  ├─ Conversation Logs
  ├─ Analytics
  ├─ Leads
  └─ Embedding Status
Logs
  ├─ Admin Activity Logs
  ├─ Error Logs
  ├─ Compliance Logs
  ├─ Moderation Logs
  └─ RAG Retrieval Logs
User Management
Secret Management
Bot Protection
[Phase 2]
  ├─ Agent Inbox
  ├─ Advanced Analytics
  ├─ CRM & Webhooks
  ├─ SEO & FAQ Pages
  └─ A/B Testing
Settings
  └─ Change Password
```

**Admin sees (scoped to assigned brands):**
```
Dashboard (assigned brands only)
[Per-Brand Section — only assigned brands visible]
  ├─ Brand Config (edit)
  ├─ Tone & Personality
  ├─ Products
  ├─ FAQs
  ├─ Routines
  ├─ Compliance Rules
  ├─ Recommendation Rules
  ├─ Image-Style Rules
  ├─ Prompt Editor
  ├─ Channel Config
  ├─ Conversation Logs
  ├─ Analytics (brand-level only)
  ├─ Leads
  └─ Embedding Status
Logs (assigned brands only)
  ├─ Compliance Logs
  ├─ Moderation Logs
  └─ RAG Retrieval Logs
Settings
  └─ Change Password
```

**Hidden from Admin:**
- Brand creation/deletion
- User Management
- Secret Management
- System-wide analytics
- Admin Activity Logs (system-wide)
- Error Logs (system-wide)

---

## PART 4: CONSISTENT UI PATTERNS

These patterns apply across all admin screens:

| Pattern | Details |
|---------|---------|
| **Consistent response format** | All data displayed in tables with: search, filter, sort, pagination |
| **Pagination** | `Page 1 of X` with `per_page` selector (10/20/50) |
| **Confirmation dialogs** | All destructive actions (delete, override, disable) require confirmation dialog |
| **Toast notifications** | Success/error messages appear as toast notifications after actions |
| **Loading states** | Skeleton loaders or spinners while data is loading |
| **Empty states** | Friendly message when no data exists: "No products yet. Add your first product." |
| **Brand context** | Brand selector visible on all brand-scoped screens. Current brand shown in header/breadcrumb. |
| **Breadcrumbs** | Navigation breadcrumbs on all pages: Home > Brand Name > Products > Edit Product |
| **Responsive design** | Admin panel should work on desktop and tablet |
| **Data masking** | Email: `pr***@example.com`. Phone: `***-***-1234`. Secrets: `****ABCD` |

---

## PART 5: SCREEN COUNT SUMMARY

| Category | Phase 1 | Phase 2 | Total |
|----------|---------|---------|-------|
| Auth screens (Login, Reset, First Login) | 4 | 0 | 4 |
| Dashboard | 1 | 0 | 1 |
| Brand management | 2 | 0 | 2 |
| Brand config | 1 | 0 | 1 |
| Tone & personality | 1 | 0 | 1 |
| Product management | 2 | 0 | 2 |
| FAQ management | 1 | 0 | 1 |
| Routine builder | 2 | 0 | 2 |
| Compliance rules | 1 | 0 | 1 |
| Recommendation rules | 1 | 0 | 1 |
| Image-style rules | 1 | 0 | 1 |
| Prompt editor | 1 | 0 | 1 |
| Channel config | 1 | 0 | 1 |
| Conversation logs | 1 | 0 | 1 |
| Analytics | 1 | 1 | 2 |
| Lead management | 1 | 0 | 1 |
| User management | 1 | 1 | 2 |
| Secret management | 1 | 0 | 1 |
| Activity/Error/Compliance/Moderation/RAG logs | 5 | 0 | 5 |
| Embedding status | 1 | 0 | 1 |
| Bot protection/IP management | 1 | 0 | 1 |
| Human agent inbox | 0 | 1 | 1 |
| CRM & webhooks | 0 | 1 | 1 |
| SEO & FAQ pages | 0 | 1 | 1 |
| A/B testing | 0 | 1 | 1 |
| **Admin Panel Total** | **31** | **6** | **37** |
| Chat widget screens | 9 | 0 | 9 |
| **Grand Total** | **40** | **6** | **46** |
