# UI/UX Design Specification
## Multi-Brand AI Chatbot Platform

> This document lists every screen and feature needed in the platform.
> Two products need to be designed: **Admin Panel** (web dashboard) and **Chat Widget** (embeddable chatbot).
> Everything listed here comes directly from the approved SRS document.

---

## Roles in the System

The admin panel has two user types. The UI must show/hide menus and actions based on the logged-in user's role.

**Super Admin**
- Has access to everything across all brands
- Can create and delete brands
- Can invite and manage other admin users
- Can manage API keys and secrets
- Can view system-wide analytics and logs

**Admin**
- Can only see and manage brands assigned to them
- Can manage products, FAQs, routines, tone, compliance for their brands
- Cannot create or delete brands
- Cannot manage other users
- Cannot manage secrets

---

# ADMIN PANEL

---

### 1. Login

| Element | Details |
|---------|---------|
| Email field | Required |
| Password field | Required, masked |
| "Login" button | |
| "Forgot Password?" link | |
| Error message | "Invalid email or password" |
| Lockout message | "Account locked. Try again in X minutes." (shows after multiple failed attempts) |

---

### 2. Forgot Password

| Element | Details |
|---------|---------|
| Email field | |
| "Send Reset Link" button | |
| Success message | "If this email is registered, a reset link has been sent." |
| "Back to Login" link | |

---

### 3. Reset Password

| Element | Details |
|---------|---------|
| New password field | |
| Confirm password field | |
| "Reset Password" button | |
| Expired link message | "This link has expired. Please request a new one." |

---

### 4. First Login — Set New Password

When a new admin is invited, they must change their password on first login.

| Element | Details |
|---------|---------|
| Welcome message | "Welcome! Please set a new password to continue." |
| New password field | |
| Confirm password field | |
| "Set Password & Continue" button | |

---

### 5. Dashboard

**Super Admin sees**: all brands. **Admin sees**: only their assigned brands.

| Element | Details |
|---------|---------|
| Brand summary cards | One card per brand showing: logo, name, conversation count, active/inactive status |
| Total conversations | Count across all visible brands |
| Active users | Currently active chat sessions |
| Channel breakdown | Message counts split by: Website, WhatsApp, Instagram |
| Message volume chart | Messages over time |
| Fallback rate | Percentage of queries that triggered fallback message, per brand |
| Cross-brand comparison | Side-by-side performance of brands (Super Admin) |

---

### 6. Brand Manager — List

**Super Admin**: can add, edit, delete brands. **Admin**: can only view their assigned brands.

| Element | Details |
|---------|---------|
| Brand list/cards | Each showing: logo thumbnail, brand name, active/inactive status, product count |
| "Add New Brand" button | Super Admin only |
| Search bar | Search by brand name |
| Per-brand actions | Edit, Delete (Super Admin only) |
| Status indicator | Green = active, Red = inactive, Orange = safe mode, Grey = disabled |

---

### 7. Brand Manager — Add / Edit Brand

| Element | Details |
|---------|---------|
| Brand name | Text input, required |
| Brand slug | Auto-generated from name, used in URLs |
| Brand logo | Image upload with preview |
| Primary color | Color picker + hex code input |
| Secondary color | Color picker + hex code input |
| Accent color | Color picker + hex code input |
| Description | Textarea — brand identity statement |
| Currency | Dropdown (ISO 4217: USD, EUR, INR, …), default USD. Applies to all of this brand's product prices — products store only a numeric `price`; the brand supplies the currency. |
| Active / Inactive toggle | |
| "Save" button | |
| "Delete Brand" button | Super Admin only. Shows confirmation: "This will permanently delete all brand data." |

---

### 8. Brand Configuration

Each brand has its own configuration for chatbot behavior, moderation, lead capture, and emergency controls.

**Response Settings**
| Element | Details |
|---------|---------|
| Response length | Dropdown: Short / Medium / Long |
| Max tokens per response | Number input |
| RAG similarity threshold | Number input (e.g., 0.7). Results below this score are discarded — chatbot uses fallback instead of guessing. |
| Recommendation Top N | Number input (default 3). How many product recommendations to show when multiple match. |
| Session timeout | Number input in minutes (e.g., 30). How long a user session stays active after last message. |

**Messages**
| Element | Details |
|---------|---------|
| Greeting message | Textarea — what the chatbot says when a user opens the chat |
| Sign-off message | Textarea — closing message |
| Fallback message | Textarea — what the chatbot says when it cannot answer safely |
| Fallback tone profile | Textarea — tone instructions for fallback responses |

**Moderation Settings**
| Element | Details |
|---------|---------|
| Moderation sensitivity | Dropdown: Low / Medium / High |
| Response when input is blocked | Dropdown: Silent drop / Polite refusal / Brand fallback message |
| Allow list | Tag input — phrases always allowed through moderation |
| Block list | Tag input — phrases always blocked by moderation |
| Prompt injection patterns | List of known attack patterns, admin can add new ones |

**Lead Capture Settings**
| Element | Details |
|---------|---------|
| Capture trigger | Dropdown: On welcome / After N messages / On intent detection / Manual prompt |
| N messages threshold | Number input (visible only if "After N messages" selected) |
| Show phone field | Toggle |
| GDPR consent text | Textarea — editable consent checkbox text |
| Allow skip | Toggle — whether users can skip the lead form |

**Rate Limiting**
| Element | Details |
|---------|---------|
| Messages per user per minute | Number input |

**Data Retention**
| Element | Details |
|---------|---------|
| Conversation retention period | Number input in days (e.g., 90). Conversations older than this are automatically deleted. |
| Brute-force lockout threshold | Number input — how many failed login attempts before account is locked |
| Lockout duration | Number input in minutes |

**Emergency Controls**
| Element | Details |
|---------|---------|
| "Disable Chatbot" button | Instantly stops this brand's chatbot. Needs confirmation dialog. |
| "Switch to Safe Mode" button | Chatbot only responds with fallback message. Needs confirmation. |
| "Resume Normal Mode" button | Restores chatbot to normal |
| Current status | Display: Normal / Safe Mode / Disabled |

---

### 9. Tone & Personality

Each brand has its own voice and personality. All changes take effect immediately.

**Core Tone**
| Element | Details |
|---------|---------|
| Emotional style | Select options: Warm / Clinical / Luxurious / Friendly |
| Communication style | Dropdown: Formal / Casual |
| Emoji usage | Toggle: Allow / Don't allow |
| Preferred words | Tag input — words/phrases the brand prefers. e.g., "radiant", "nourishing" |
| Avoided words | Tag input — words/phrases the brand avoids. e.g., "cheap", "basic" |

**Micro-Tone Rules**
| Element | Details |
|---------|---------|
| Softness level | Dropdown: Gentle / Neutral / Direct |
| Sensory language | Toggle: Enable / Restrict. (When enabled, allows "silky", "velvety", "luminous" etc.) |
| Emotional cues | Multi-select: Calming / Uplifting / Nurturing / Confident |
| Restricted adjectives | Tag input — adjectives the brand must NOT use. e.g., "cheap", "harsh" |
| Clinical language | Toggle: Allow clinical/medical terms / Block by default |
| Harsh word blocking | Toggle: Block aggressive, blunt, or non-premium words |

**Override**
| Element | Details |
|---------|---------|
| "Apply Changes Now" button | All tone and vocabulary changes take effect immediately. Show confirmation. |

---

### 10. Product Manager — List

| Element | Details |
|---------|---------|
| Brand selector | Dropdown to switch brands |
| Product table | Columns: Image thumbnail, Name, Category, Price, Stock Status, Embedding Status, Actions |
| "Add Product" button | |
| Search bar | Search by product name |
| Filters | Category, Skin type, Concern, Stock status (In Stock / Out of Stock), Embedding status |
| Pagination | Page controls |
| Embedding status badge | Per product: Green "Synced" / Yellow "Pending" / Red "Failed" with retry icon |

---

### 11. Product Manager — Add / Edit Product

| Element | Details |
|---------|---------|
| Product name | Text input, required |
| Description | Textarea, required |
| Ingredients | Tag input or textarea — list of ingredients |
| Price | Number input with currency |
| Category | Dropdown: Cleansers, Toners, Serums, Moisturizers, Masks, Sunscreen, etc. |
| Product image | Image upload with preview |
| Skin type tags | Multi-select checkboxes: Oily / Dry / Combination / Sensitive / Normal |
| Concern tags | Multi-select checkboxes: Acne / Aging / Hydration / Hyperpigmentation / Sensitivity / Dullness |
| Stock status | Toggle: In Stock / Out of Stock |
| Priority score | Number input — higher score = recommended first |
| "Save" button | |
| Embedding status | Shows after save: Pending / Synced / Failed |

> When a product is saved, the system auto-embeds it into the AI knowledge base. The embedding status shows the sync progress.

---

### 12. FAQ Manager

| Element | Details |
|---------|---------|
| Brand selector | Dropdown |
| FAQ list | Columns: Question (truncated), Category, Embedding Status, Actions |
| "Add FAQ" button | |
| Search bar | Search by question text |
| Filter by category | Dropdown |
| **Add / Edit form:** | |
| Question | Text input, required |
| Answer | Textarea, required |
| Category | Dropdown or text: Ingredients, Shipping, Returns, Usage, General |
| "Save" button | |
| Embedding status | Synced / Pending / Failed |

> When a FAQ is saved, it is automatically embedded into the AI knowledge base.

---

### 13. Routine Builder — List

| Element | Details |
|---------|---------|
| Brand selector | Dropdown |
| Routine list | Columns: Name, Target Skin Type, Number of Steps, Active/Inactive, Actions |
| "Create Routine" button | |
| Active/Inactive toggle | Per routine |

---

### 14. Routine Builder — Create / Edit

| Element | Details |
|---------|---------|
| Routine name | Text input. e.g., "Morning Glow Routine" |
| Description | Textarea |
| Target skin type | Dropdown: Oily / Dry / Combination / Sensitive / Normal |
| Target concerns | Multi-select: Acne / Aging / Hydration / Hyperpigmentation / Sensitivity / Dullness |
| Active toggle | |
| **Steps** | |
| Step list | Drag-and-drop reorderable |
| Each step: Step number | Auto-assigned by order |
| Each step: Step name | Dropdown: Cleanse / Tone / Serum / Treat / Moisturize / Sunscreen / Custom |
| Each step: Product | Dropdown from brand's product catalog, shows product name + image thumbnail |
| "Add Step" button | |
| "Remove Step" button | Per step, with confirmation |
| "Save" button | |
| "Apply Changes Now" button | Routine changes take effect immediately |

---

### 15. Compliance & Safety Rules

**Rule List**
| Element | Details |
|---------|---------|
| Brand selector | Dropdown |
| Rule table | Columns: Rule Type, Value, Active/Inactive, Actions |
| Filter by type | Blocked Phrase / Allowed Phrase / Blocked Topic / Conversation Boundary |
| "Add Rule" button | |

**Add / Edit Rule**
| Element | Details |
|---------|---------|
| Rule type | Dropdown: Blocked Phrase / Allowed Phrase / Blocked Topic / Conversation Boundary |
| Value | Text input — the phrase, topic, or boundary |
| Active toggle | |

**Conversation Boundary Toggles**
| Element | Details |
|---------|---------|
| No medical claims | Toggle |
| No over-explaining | Toggle |
| No aggressive upselling | Toggle |
| No unnecessary details | Toggle |
| No medical tone | Toggle (unless clinical language allowed in tone settings) |

**Override**
| Element | Details |
|---------|---------|
| "Apply Changes Now" button | All compliance changes take effect immediately |

---

### 16. Recommendation Rules

**Rule List**
| Element | Details |
|---------|---------|
| Brand selector | Dropdown |
| Rule table | Columns: Rule Type, Description, Active/Inactive, Actions |
| Filter by type | Exclusion / Conflict / Priority / Suitability |
| "Add Rule" button | |

**Add / Edit Rule**
| Element | Details |
|---------|---------|
| Rule type | Dropdown: Exclusion / Conflict / Priority / Suitability Matrix |
| For Exclusion | Product selector + "Do not recommend for:" + skin type or concern selector |
| For Conflict | Product A selector + Product B selector + Reason text. e.g., "Retinol and Vitamin C should not be used together" |
| For Priority | Product selector + Priority score number |
| For Suitability Matrix | Product selector + multi-axis scoring grid: Skin Type (score per type), Concern (score per concern), Sensitivity Level (score), Routine Step (which step this product fits: Cleanse/Tone/Serum/Moisturize etc.) |
| Active toggle | |

**Rule Testing**
| Element | Details |
|---------|---------|
| Simulated skin type | Dropdown |
| Simulated concerns | Multi-select |
| "Run Test" button | |
| Test result | Shows: matched products (ranked), excluded products with reasons, applied filters |

**Bulk Import**
| Element | Details |
|---------|---------|
| "Download CSV Template" link | |
| CSV upload | File upload |
| Import result | "X rules imported, Y errors" with error details |

---

### 17. Image-Style Rules

Each brand defines its own visual aesthetic for the chatbot.

| Element | Details |
|---------|---------|
| Brand selector | Dropdown |
| Image style profile | Dropdown: Soft-Luxury / Clinical-Luxury / K-Beauty Minimal / Botanical / Modern-Clean / Custom |
| **Product Card Style** | |
| Card edges | Radio: Rounded / Sharp |
| Background color | Color picker |
| Overlay style | Dropdown: None / Gradient / Shadow |
| **Routine Card Style** | |
| Same options as product card | |
| **UI Element Style** | |
| Button style | Rounded/sharp, color |
| Card background | Color picker |
| Preview panel | Live preview of how cards and elements will look with current settings |

---

### 18. Prompt Editor

Each brand has its own system prompt (the instructions given to the AI). Admins can edit, version, and test it.

**Editor**
| Element | Details |
|---------|---------|
| Brand selector | Dropdown |
| Direct editing view | Full-text editor showing the complete system prompt |
| Composed view | Visual breakdown with labeled, collapsible sections: Brand Identity, Tone Rules, Vocabulary, Compliance, Fallback Instructions |
| Status indicator | "Draft (unsaved)" / "Draft (saved)" / "Live" |
| "Save Draft" button | Saves without affecting the live prompt |
| "Publish" button | Makes draft live. Confirmation: "This will replace the current live prompt immediately." |
| Syntax validation warning | Warns if prompt appears malformed |

**Live Preview**
| Element | Details |
|---------|---------|
| Sample user input | Text input to type a test message |
| "Test" button | |
| AI response preview | Shows what the AI would respond with this prompt |

**Version History**
| Element | Details |
|---------|---------|
| Version list | Table: Version #, Published By, Date/Time, Annotation, "Live" badge on current version |
| Last 20 versions shown | Older versions archived but recoverable |
| "Restore" button | Per version. Makes that version live again. |
| Annotation field | Optional comment per version. e.g., "Tweaked tone for Diwali campaign" |

**Diff View**
| Element | Details |
|---------|---------|
| Version A selector | Dropdown |
| Version B selector | Dropdown |
| Side-by-side comparison | Added text in green, removed text in red |

---

### 19. Channel Configuration

**Website Chat Widget**
| Element | Details |
|---------|---------|
| Embed code | Read-only code block showing the script tag to embed on a website |
| "Copy Code" button | |
| Widget preview | Shows how the widget will look with the brand's colors and logo |

**WhatsApp**
| Element | Details |
|---------|---------|
| Connection status | Connected / Not Connected |
| Phone number | Display connected number |
| Webhook URL | Read-only URL for Meta dashboard configuration |
| "Connect" / "Disconnect" button | |
| Template messages | List of approved outbound message templates |

**Instagram**
| Element | Details |
|---------|---------|
| Connection status | Connected / Not Connected |
| Instagram page | Display connected page name |
| "Connect" / "Disconnect" button | |

---

### 20. Conversation Logs

**Conversation List**
| Element | Details |
|---------|---------|
| Brand selector | Dropdown |
| Conversation table | Columns: Session ID, Channel (Website/WhatsApp/Instagram), Start Time, Message Count, Flagged (Yes/No), Actions |
| Filters | Channel, Date range, Flagged only toggle |
| Search | Search within conversation content |
| Pagination | |

**Conversation Detail**
| Element | Details |
|---------|---------|
| Header | Session ID, Channel, Brand, Start/End time |
| Session state panel | Shows what the chatbot remembered during this session: skin type, concerns, preferences, products recommended |
| Message thread | Chronological messages — user messages on one side, AI responses on the other, with timestamps |
| "Flag for Review" button | With optional reason text field |
| "Unflag" button | |
| "Delete Conversation" button | GDPR right to erasure. Confirmation: "This will permanently delete this conversation and all its messages." |
| RAG retrieval detail | Expandable: shows which knowledge base content was used for each AI response, with relevance scores |
| Compliance detail | Expandable: shows if any response was blocked or replaced and why |
| Moderation detail | Expandable: shows if any user input was blocked and why |
| Recommendation rule detail | Expandable: shows which rules were applied, matched products, excluded products, and reasons |

---

### 21. Analytics

**Super Admin**: system-wide + per-brand. **Admin**: assigned brands only.

**Overview**
| Element | Details |
|---------|---------|
| Total conversations | Count + trend |
| Total messages | Count + trend |
| Active sessions | Current count |
| Average messages per conversation | |

**Message Volume**
| Element | Details |
|---------|---------|
| Time-series chart | Daily / Weekly / Monthly toggle |
| Channel breakdown | Bar or pie chart: Website vs WhatsApp vs Instagram |

**Popular Questions**
| Element | Details |
|---------|---------|
| Top questions list | Ranked by frequency |

**Response Quality**
| Element | Details |
|---------|---------|
| Fallback rate | Count and percentage of responses that used fallback |
| Compliance block count | Responses blocked by safety filter |
| Average response time | |

**API Usage**
| Element | Details |
|---------|---------|
| AI API calls per brand | Count + token usage |
| Embedding API calls per brand | Count |
| Time period selector | Last 7 / 30 / 90 days / Custom range |

**Advanced Analytics**
| Element | Details |
|---------|---------|
| Routine completion rate | % of users completing skin quiz + routine flow |
| Click-through rate | Clicks on product cards and purchase links |
| Drop-off analysis | Funnel: Welcome -> Quiz -> Product View -> Purchase Link |
| Conversion tracking | Lead-to-purchase (with CRM integration) |
| Channel performance comparison | Side-by-side: Website vs WhatsApp vs Instagram |
| Cross-brand comparison | Dashboard comparing all brands (Super Admin) |
| Cohort analysis | User behavior tracked over time |

---

### 22. Lead Management

| Element | Details |
|---------|---------|
| Brand selector | Dropdown |
| Lead table | Columns: Name, Email (masked: pr***@example.com), Phone (masked), Channel, Consent Status, Date Captured, Actions |
| Filters | Date range, Channel |
| Search | By name or email |
| Sort | By date, by name |
| Pagination | |
| "Export CSV" button | Exports filtered leads |
| Per-lead actions | View details / Delete (confirmation: "This will permanently delete this lead's data per GDPR") |

**Lead Detail**
| Element | Details |
|---------|---------|
| Full name | |
| Full email | Unmasked for authorized users |
| Phone | If captured |
| Channel source | Website / WhatsApp / Instagram |
| Consent | Yes/No with consent text shown |
| Date captured | |
| Link to conversation | Where this lead was captured |

---

### 23. User Management

**Super Admin only** — Admin cannot see this screen.

| Element | Details |
|---------|---------|
| User list | Columns: Email, Role (Super Admin / Admin), Assigned Brands, Status (Active / Locked), Last Login, Actions |
| "Invite New Admin" button | |

**Invite Form**
| Element | Details |
|---------|---------|
| Email | Required |
| Role | Dropdown: Super Admin / Admin |
| Assign brands | Multi-select (visible only for Admin role) |
| "Send Invitation" button | |

**Per-user Actions**
| Element | Details |
|---------|---------|
| Edit brand assignments | Change which brands this admin can access |
| Revoke access | Deactivate user (confirmation dialog) |
| Delete user | Permanent removal (confirmation dialog) |
| View activity log | Opens activity log filtered to this user |
| Unlock account | If locked due to failed login attempts |

**Advanced Roles** (future expansion)
| Element | Details |
|---------|---------|
| Custom role creator | Create roles beyond Super Admin / Admin (e.g., Brand Manager, Content Editor, Viewer) |
| Per-feature permissions | Checkboxes: read-only on logs, edit-only on products, publish rights, etc. |
| Per-brand role assignment | Same user can have different roles on different brands |
| Permission templates | Pre-defined permission bundles |

---

### 24. Secret Management

**Super Admin only** — Admin cannot see this screen.

Secrets are API keys and tokens. They are never shown in plain text.

| Element | Details |
|---------|---------|
| Secrets table | Columns: Secret Type, Brand (or "System Default"), Status (Set / Not Set), Last 4 Characters (e.g., "****ABCD"), Last Updated, Actions |
| "Add Secret" button | |

**Add Secret Form**
| Element | Details |
|---------|---------|
| Secret type | Dropdown: Anthropic API Key / Embeddings API Key / S3 Credentials / Meta WhatsApp Token / Meta Instagram Token / Webhook Secret |
| Brand | Dropdown: System Default / specific brand |
| Secret value | Password field — value is NOT retained after submit |
| "Save" button | |

**Per-secret Actions**
| Element | Details |
|---------|---------|
| Update | Replace-only. Old value is never shown. |
| Delete | Confirmation dialog |
| Test Connection | Button — shows "Connection successful" or "Connection failed: {error}" |
| View audit log | Who accessed, modified, or deleted this secret, with timestamps |

---

### 25. Admin Activity Logs

| Element | Details |
|---------|---------|
| Activity table | Columns: Timestamp, User (email), Action Type, Entity Type, Entity Name, Brand, IP Address |
| Filters | User, Action type, Entity type, Brand, Date range |
| Search | By entity name |
| Pagination | |
| Expandable row detail | Before state (what it was), After state (what it changed to) |

Action types: Created, Updated, Deleted, Published, Restored, Overridden, Enabled, Disabled, Invited, Revoked, Login, Failed Login, Secret Rotated

---

### 26. Error Logs

| Element | Details |
|---------|---------|
| Error table | Columns: Timestamp, Error Type, Brand, Channel, Description |
| Filters | Error type (AI API Failure / Embeddings API Failure / Storage Failure / Timeout / Webhook Failure), Brand, Date range |

---

### 27. Compliance Logs

| Element | Details |
|---------|---------|
| Compliance table | Columns: Timestamp, Brand, Original Response (truncated), Replacement, Reason, Rule Triggered |
| Filters | Brand, Reason, Date range |
| Detail view | Full original response, full replacement, which rule was triggered |

---

### 28. Moderation Logs

| Element | Details |
|---------|---------|
| Moderation table | Columns: Timestamp, Brand, User Identifier (masked), Blocked Input (truncated), Reason, Action Taken |
| Filters | Brand, Reason (Spam / Abuse / Prompt Injection / Off-Topic), Date range |
| Detail view | Full blocked input, detailed reason |
| Repeated abuse indicator | Highlight when same user triggers multiple blocks |
| "Block User/IP" action | Add to block list directly from log |

---

### 29. RAG Retrieval Logs

Shows which knowledge base content was retrieved for each user query, with relevance scores. Useful for debugging why the chatbot gave a specific answer or why it used fallback.

| Element | Details |
|---------|---------|
| Brand selector | Dropdown |
| Retrieval log table | Columns: Timestamp, User Query (truncated), Chunks Retrieved Count, Top Similarity Score, Hit Threshold (Yes/No) |
| Filters | Brand, Date range, Below-threshold only toggle |
| Search | Search within user queries |
| Detail view | Full user query, list of retrieved chunks with: type (Product/FAQ/Routine), name, similarity score, text excerpt |
| "No context found" indicator | Highlights queries where no chunks met the similarity threshold |

---

### 30. Recommendation Rule Logs

Shows every recommendation rule execution — what rules were applied, what products matched, what was excluded and why.

| Element | Details |
|---------|---------|
| Brand selector | Dropdown |
| Rule log table | Columns: Timestamp, User Input Summary, Skin Type, Concerns, Matched Products Count, Excluded Count |
| Filters | Brand, Date range, Skin type, Had exclusions toggle |
| Detail view | Full input, skin profile used, all matched products (ranked), all excluded products with reason (which rule blocked them), applied filters |

---

### 31. Embedding Status

Shows whether content (products, FAQs, routines) has been successfully synced to the AI knowledge base.

| Element | Details |
|---------|---------|
| Brand selector | Dropdown |
| Status overview | Counts: Total items, Synced, Pending, Failed |
| Entity list | Table: Type (Product/FAQ/Routine), Name, Status (Synced/Pending/Failed), Last Updated |
| Filter by status | All / Pending / Failed |
| "Retry" button | Per failed item |
| "Retry All Failed" button | Batch retry |
| Error details | For failed items: error message |

---

### 32. Bot Protection

| Element | Details |
|---------|---------|
| IP block list | Table: IP Address, Blocked Date, Blocked By, Reason |
| "Add IP" button | Manual IP blocking |
| User block list | Table: User Identifier, Blocked Date, Reason |
| "Add User" button | Manual user blocking |
| Suspicious activity alerts | List of recent bot-like activity detections |

---

### 33. Notification Center

A notification bell icon in the top-right header of the admin panel. Shows alerts that need admin attention.

| Element | Details |
|---------|---------|
| Notification bell icon | In admin panel header, with unread count badge |
| Notification dropdown/panel | List of recent notifications |
| **Notification types:** | |
| Embedding failed | "{Product/FAQ name} failed to sync to knowledge base. [Retry]" |
| Repeated abuse detected | "Repeated abuse from user {masked ID} on {brand}. [View Logs] [Block User]" |
| AI API failure | "AI API call failed for {brand}. Fallback message served." |
| Brand disabled/safe mode | "{Brand} was switched to safe mode by {admin}." |
| Mark as read | Per notification or "Mark all as read" |
| View all | Link to full notification history |

---

### 34. Human Agent Inbox

When a user requests a human or the AI cannot answer confidently, the conversation is routed to a human agent.

| Element | Details |
|---------|---------|
| Escalated conversation queue | List: User Identifier, Brand, Channel, Escalation Reason (user-requested or AI-confidence), Wait Time, Status (Waiting / In Progress / Resolved) |
| Conversation detail | Full AI conversation history + user session state (skin type, concerns, preferences) — so the agent has full context |
| Agent reply input | Text input |
| "Send Reply" button | |
| "Return to AI" button | Hands conversation back to the chatbot |
| Agent availability hours | Per-brand: set hours when human agents are available |
| Outside-hours message | Configurable message shown when no agents are available |
| Agent assignment | Assign a conversation to a specific agent |

---

### 35. CRM & Webhook Settings

| Element | Details |
|---------|---------|
| Outbound webhook URLs | Configure URL per event: Lead Captured / Conversation Ended / Escalation Requested |
| CRM integration | Setup for one CRM (Shopify / HubSpot / Klaviyo / Mailchimp) |
| Connection status | Connected / Not Connected with test button |
| Lead export schedule | Manual only / Daily / Weekly |
| Export format | CSV / JSON |

---

### 36. SEO & FAQ Pages

| Element | Details |
|---------|---------|
| Public FAQ pages | Toggle: Enable / Disable per brand |
| URL structure | Subdomain vs path-based brand isolation |
| Schema markup preview | Auto-generated FAQPage markup |
| Sitemap URL | Auto-generated |
| Search engine indexing | Toggle: Allow / Block per brand |

---

### 37. A/B Testing

| Element | Details |
|---------|---------|
| Test list | Table: Test Name, Type (Prompt / Tone / Recommendation), Status (Draft / Running / Completed), Winner |
| "Create Test" button | |
| Create form | Name, Type, Variant A config, Variant B config, Traffic split percentage |
| Running test metrics | Per variant: conversion rate, engagement, fallback rate |
| Statistical significance indicator | Shows whether results are significant |
| "Promote Winner" button | Makes winning variant the default |

---

### 38. Change Password

Available to all logged-in users.

| Element | Details |
|---------|---------|
| Current password field | |
| New password field | |
| Confirm new password field | |
| "Update Password" button | |

---

# CHAT WIDGET

The chat widget is a component embedded on brand websites via a script tag. It must be fully themed per brand — colors, logo, fonts, card styles all match the brand's visual identity.

---

### W1. Chat Bubble (Minimized State)

| Element | Details |
|---------|---------|
| Floating button | Bottom-right corner of the website |
| Brand primary color | Bubble uses the brand's color |
| Unread message badge | Shows count of unread messages |
| Click | Opens the widget |

---

### W2. Welcome Screen

| Element | Details |
|---------|---------|
| Brand logo | Top of widget |
| Brand name | Below logo |
| Greeting message | Brand's configured welcome text |
| Quick-action buttons | Three buttons: "Browse Products" / "Skin Quiz" / "FAQ" |
| Text input | At bottom for typing a message |
| Close/minimize button | |

---

### W3. Chat Interface

| Element | Details |
|---------|---------|
| Header | Brand logo (small) + brand name + minimize/close button |
| Message area | Scrollable |
| User messages | Right-aligned bubbles |
| AI messages | Left-aligned bubbles in brand color |
| Typing indicator | Animated dots while AI is generating |
| Text input | With send button |
| Timestamps | Per message or grouped |
| Quick reply buttons | Below AI messages when applicable (e.g., "Yes" / "No" / "Tell me more") |
| Product cards | Shown inline when AI recommends products (see W5) |
| Routine cards | Shown inline when AI suggests routines (see W6) |
| Scroll to bottom button | Appears when user scrolls up |

---

### W4. Skin Quiz Flow

The chatbot guides users through questions to recommend a personalized routine.

| Element | Details |
|---------|---------|
| Quiz intro message | AI explains the quiz purpose |
| **Question 1: Skin Type** | Quick reply buttons: Oily / Dry / Combination / Sensitive / Normal |
| **Question 2: Concerns** | Multi-select buttons: Acne / Aging / Hydration / Hyperpigmentation / Sensitivity / Dullness + "Done" button |
| **Question 3: Preferences** | Quick reply buttons: Fragrance-Free / Vegan / Budget-Friendly (brand-configurable) |
| Result | Personalized routine with product recommendations |

> The chatbot remembers answers within the session. It never re-asks a question already answered. It never re-recommends a product already suggested.

---

### W5. Product Card (Inline in Chat)

Appears within the chat when the AI recommends a product.

| Element | Details |
|---------|---------|
| Product image | Styled per brand's image rules (rounded/sharp edges, background color, overlay) |
| Product name | Bold |
| Price | Formatted with currency |
| Short description | 1-2 lines |
| "View Product" / "Shop Now" button | External link to brand's website (opens in new tab) |

---

### W6. Routine Display (Inline in Chat)

Appears when the AI recommends a skincare routine.

| Element | Details |
|---------|---------|
| Routine title | e.g., "Your Morning Glow Routine" |
| Step cards | Vertically stacked, numbered |
| Each step: Number + name | e.g., "Step 1: Cleanse" |
| Each step: Product card | Product image (brand-styled), name, price |
| Each step: How-to | Brief usage instruction |
| Card styling | Follows brand's routine card style rules |

---

### W7. Lead Capture Form

Appears based on the brand's configured trigger (on welcome, after N messages, on intent, or manually).

| Element | Details |
|---------|---------|
| Name field | Required |
| Email field | Required, with validation |
| Phone field | Optional (only shown if brand enables it) |
| Consent checkbox | With brand-specific text |
| "Submit" button | |
| "Skip" button | Dismisses form, conversation continues |
| Success message | "Thank you! Let's continue." |
| Invisible reCAPTCHA | Runs on submission (not visible to users) |
| Hidden honeypot fields | Invisible to real users, catches bots |

---

### W8. Fallback Message

Displayed when the AI cannot answer safely, a compliance rule is triggered, or the system times out.

| Element | Details |
|---------|---------|
| Fallback message | Brand's configured fallback text, in the brand's fallback tone |
| Displayed as | Same as a regular AI message bubble |

---

### W9. Connection Error State

| Element | Details |
|---------|---------|
| Connection lost | "Connection lost. Trying to reconnect..." with loading spinner |
| Reconnected | "Connected! You can continue chatting." |
| Service unavailable | "Our advisor is temporarily unavailable. Please try again shortly." |

---

# NAVIGATION STRUCTURE

### Super Admin Sidebar

```
[Notification Bell Icon - top right header]
Dashboard
Brands
  - All Brands
  - Add New Brand
[Select a Brand] ->
  - Brand Config
  - Tone & Personality
  - Products
  - FAQs
  - Routines
  - Compliance Rules
  - Recommendation Rules
  - Image-Style Rules
  - Prompt Editor
  - Channel Config
  - Conversations
  - Analytics
  - Leads
  - Embedding Status
Logs
  - Admin Activity
  - Error Logs
  - Compliance Logs
  - Moderation Logs
  - RAG Retrieval Logs
  - Recommendation Rule Logs
Users
Secrets
Bot Protection
Agent Inbox
CRM & Webhooks
SEO & FAQ Pages
A/B Testing
Settings
  - Change Password
```

### Admin Sidebar (brand-scoped)

```
[Notification Bell Icon - top right header]
Dashboard
[Only Assigned Brands visible] ->
  - Brand Config
  - Tone & Personality
  - Products
  - FAQs
  - Routines
  - Compliance Rules
  - Recommendation Rules
  - Image-Style Rules
  - Prompt Editor
  - Channel Config
  - Conversations
  - Analytics
  - Leads
  - Embedding Status
Logs (own brands only)
  - My Activity Log
  - Error Logs (own brands only)
  - Compliance Logs
  - Moderation Logs
  - RAG Retrieval Logs
  - Recommendation Rule Logs
Settings
  - Change Password
```

**Hidden from Admin**: Brand creation/deletion, Users, Secrets, Bot Protection, System-wide Admin Activity Logs, Agent Inbox management, CRM, SEO, A/B Testing

---

# UI PATTERNS (Apply Across All Screens)

| Pattern | Details |
|---------|---------|
| Tables | All data tables have: search, filter, sort, pagination |
| Pagination | "Page 1 of X" with items-per-page selector (10 / 20 / 50) |
| Confirmations | All destructive actions (delete, override, disable) require a confirmation dialog |
| Notifications | Success and error messages shown as toast notifications |
| Loading states | Skeleton loaders or spinners while data loads |
| Empty states | Friendly message when no data: "No products yet. Add your first product." |
| Brand context | Current brand name visible in header or breadcrumb on all brand-scoped screens |
| Breadcrumbs | Navigation path on all screens: Home > Brand Name > Products > Edit Product |
| Responsive | Admin panel works on desktop and tablet |
| Data masking | Email: pr***@example.com, Phone: ***-***-1234, Secrets: ****ABCD |

---

# SCREEN COUNT

| Section | Screens |
|---------|---------|
| Auth (Login, Forgot Password, Reset Password, First Login, Change Password) | 5 |
| Dashboard | 1 |
| Brand Management (List, Add/Edit, Config) | 3 |
| Tone & Personality | 1 |
| Product Manager (List, Add/Edit) | 2 |
| FAQ Manager | 1 |
| Routine Builder (List, Create/Edit) | 2 |
| Compliance Rules | 1 |
| Recommendation Rules | 1 |
| Image-Style Rules | 1 |
| Prompt Editor (with version history + diff) | 1 |
| Channel Config | 1 |
| Conversation Logs (List + Detail) | 2 |
| Analytics | 1 |
| Lead Management | 1 |
| User Management | 1 |
| Secret Management | 1 |
| Admin Activity Logs | 1 |
| Error Logs | 1 |
| Compliance Logs | 1 |
| Moderation Logs | 1 |
| RAG Retrieval Logs | 1 |
| Recommendation Rule Logs | 1 |
| Embedding Status | 1 |
| Bot Protection | 1 |
| Notification Center | 1 |
| Human Agent Inbox | 1 |
| CRM & Webhooks | 1 |
| SEO & FAQ Pages | 1 |
| A/B Testing | 1 |
| **Admin Panel Total** | **38** |
| Chat Widget (Bubble, Welcome, Chat, Quiz, Product Card, Routine, Lead Form, Fallback, Error) | **9** |
| **Grand Total** | **47** |
