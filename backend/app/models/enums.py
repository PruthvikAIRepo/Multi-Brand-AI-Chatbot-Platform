import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"


class SkinType(str, enum.Enum):
    OILY = "oily"
    DRY = "dry"
    COMBINATION = "combination"
    SENSITIVE = "sensitive"
    NORMAL = "normal"


class SkinConcern(str, enum.Enum):
    ACNE = "acne"
    AGING = "aging"
    HYDRATION = "hydration"
    HYPERPIGMENTATION = "hyperpigmentation"
    SENSITIVITY = "sensitivity"
    DULLNESS = "dullness"


class ChannelType(str, enum.Enum):
    WEBSITE = "website"
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    AGENT = "agent"


class ResponseLength(str, enum.Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class ChatbotStatus(str, enum.Enum):
    NORMAL = "normal"
    SAFE_MODE = "safe_mode"
    DISABLED = "disabled"


class EmotionalStyle(str, enum.Enum):
    WARM = "warm"
    CLINICAL = "clinical"
    LUXURIOUS = "luxurious"
    FRIENDLY = "friendly"


class CommunicationStyle(str, enum.Enum):
    FORMAL = "formal"
    CASUAL = "casual"


class SoftnessLevel(str, enum.Enum):
    GENTLE = "gentle"
    NEUTRAL = "neutral"
    DIRECT = "direct"


class ImageStyleProfile(str, enum.Enum):
    SOFT_LUXURY = "soft_luxury"
    CLINICAL_LUXURY = "clinical_luxury"
    K_BEAUTY_MINIMAL = "k_beauty_minimal"
    BOTANICAL = "botanical"
    MODERN_CLEAN = "modern_clean"
    CUSTOM = "custom"


class CardEdges(str, enum.Enum):
    ROUNDED = "rounded"
    SHARP = "sharp"


class OverlayStyle(str, enum.Enum):
    NONE = "none"
    GRADIENT = "gradient"
    SHADOW = "shadow"


class ComplianceRuleType(str, enum.Enum):
    BLOCKED_PHRASE = "blocked_phrase"
    ALLOWED_PHRASE = "allowed_phrase"
    BLOCKED_TOPIC = "blocked_topic"
    CONVERSATION_BOUNDARY = "conversation_boundary"


class RecommendationRuleType(str, enum.Enum):
    EXCLUSION = "exclusion"
    CONFLICT = "conflict"
    PRIORITY = "priority"
    SUITABILITY = "suitability"


class RoutineStepName(str, enum.Enum):
    CLEANSE = "cleanse"
    TONE = "tone"
    SERUM = "serum"
    TREAT = "treat"
    MOISTURIZE = "moisturize"
    SUNSCREEN = "sunscreen"
    CUSTOM = "custom"


class ModerationSensitivity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ModerationResponse(str, enum.Enum):
    SILENT_DROP = "silent_drop"
    POLITE_REFUSAL = "polite_refusal"
    BRAND_FALLBACK = "brand_fallback"


class ModerationReason(str, enum.Enum):
    SPAM = "spam"
    ABUSE = "abuse"
    PROMPT_INJECTION = "prompt_injection"
    OFF_TOPIC = "off_topic"


class EntityType(str, enum.Enum):
    PRODUCT = "product"
    FAQ = "faq"
    ROUTINE = "routine"


class EmbeddingStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class SecretType(str, enum.Enum):
    ANTHROPIC_API_KEY = "anthropic_api_key"
    EMBEDDINGS_API_KEY = "embeddings_api_key"
    S3_CREDENTIALS = "s3_credentials"
    META_WHATSAPP_TOKEN = "meta_whatsapp_token"
    META_INSTAGRAM_TOKEN = "meta_instagram_token"
    WEBHOOK_SECRET = "webhook_secret"


class CaptureTrigger(str, enum.Enum):
    ON_WELCOME = "on_welcome"
    AFTER_N_MESSAGES = "after_n_messages"
    ON_INTENT = "on_intent"
    MANUAL = "manual"


class ErrorType(str, enum.Enum):
    AI_API_FAILURE = "ai_api_failure"
    EMBEDDINGS_API_FAILURE = "embeddings_api_failure"
    STORAGE_FAILURE = "storage_failure"
    TIMEOUT = "timeout"
    WEBHOOK_FAILURE = "webhook_failure"


class AdminActionType(str, enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    PUBLISHED = "published"
    RESTORED = "restored"
    OVERRIDDEN = "overridden"
    ENABLED = "enabled"
    DISABLED = "disabled"
    INVITED = "invited"
    REVOKED = "revoked"
    LOGIN = "login"
    FAILED_LOGIN = "failed_login"
    SECRET_ROTATED = "secret_rotated"


class NotificationType(str, enum.Enum):
    EMBEDDING_FAILED = "embedding_failed"
    REPEATED_ABUSE = "repeated_abuse"
    AI_API_FAILURE = "ai_api_failure"
    BRAND_STATUS_CHANGE = "brand_status_change"


class ApiUsageType(str, enum.Enum):
    CLAUDE = "claude"
    EMBEDDINGS = "embeddings"


class EscalationStatus(str, enum.Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class ConversationHandler(str, enum.Enum):
    AI = "ai"
    HUMAN = "human"
