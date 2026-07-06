from pydantic import BaseModel, Field
from app.models.enums import (
    ResponseLength, CaptureTrigger, EmotionalStyle, CommunicationStyle,
    SoftnessLevel, ModerationSensitivity, ModerationResponse,
    ImageStyleProfile, CardEdges, OverlayStyle, ChatbotStatus,
)


class BrandConfigUpdateRequest(BaseModel):
    model_config = {"extra": "forbid"}
    response_length: ResponseLength | None = None
    max_tokens: int | None = Field(None, ge=100, le=4000)
    rag_similarity_threshold: float | None = Field(None, ge=0.0, le=1.0)
    recommendation_top_n: int | None = Field(None, ge=1, le=20)
    session_timeout_minutes: int | None = Field(None, ge=1, le=1440)
    greeting_message: str | None = None
    signoff_message: str | None = None
    fallback_message: str | None = None
    fallback_tone_profile: str | None = None
    no_medical_claims: bool | None = None
    no_over_explaining: bool | None = None
    no_aggressive_upselling: bool | None = None
    no_unnecessary_details: bool | None = None
    no_medical_tone: bool | None = None
    rate_limit_per_user: int | None = Field(None, ge=1, le=1000)
    conversation_retention_days: int | None = Field(None, ge=1, le=3650)
    lead_capture_trigger: CaptureTrigger | None = None
    lead_capture_n_messages: int | None = Field(None, ge=1, le=100)
    lead_show_phone_field: bool | None = None
    lead_gdpr_consent_text: str | None = None
    lead_allow_skip: bool | None = None


class ToneSettingsUpdateRequest(BaseModel):
    model_config = {"extra": "forbid"}
    emotional_style: EmotionalStyle | None = None
    communication_style: CommunicationStyle | None = None
    emoji_usage: bool | None = None
    vocabulary_preferred: list[str] | None = None
    vocabulary_avoided: list[str] | None = None
    softness_level: SoftnessLevel | None = None
    sensory_language_enabled: bool | None = None
    emotional_cues: list[str] | None = None
    restricted_adjectives: list[str] | None = None
    clinical_language_allowed: bool | None = None
    harsh_word_blocking: bool | None = None


class ModerationConfigUpdateRequest(BaseModel):
    model_config = {"extra": "forbid"}
    sensitivity: ModerationSensitivity | None = None
    response_on_block: ModerationResponse | None = None
    allow_list: list[str] | None = None
    block_list: list[str] | None = None
    prompt_injection_patterns: list[str] | None = None


class ImageStyleUpdateRequest(BaseModel):
    model_config = {"extra": "forbid"}
    image_style_profile: ImageStyleProfile | None = None
    product_card_edges: CardEdges | None = None
    product_card_background_color: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    product_card_overlay_style: OverlayStyle | None = None
    routine_card_edges: CardEdges | None = None
    routine_card_background_color: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    routine_card_overlay_style: OverlayStyle | None = None
    ui_button_style: CardEdges | None = None
    ui_button_color: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    ui_card_background: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')


class ChatbotStatusRequest(BaseModel):
    status: ChatbotStatus
