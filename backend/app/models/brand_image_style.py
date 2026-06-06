from sqlalchemy import Column, String, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import ImageStyleProfile, CardEdges, OverlayStyle


class BrandImageStyle(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "brand_image_styles"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, unique=True)

    image_style_profile = Column(Enum(ImageStyleProfile, name="image_style_profile"), default=ImageStyleProfile.MODERN_CLEAN)

    # Product card
    product_card_edges = Column(Enum(CardEdges, name="card_edges", create_constraint=False), default=CardEdges.ROUNDED)
    product_card_background_color = Column(String(7), default="#FFFFFF")
    product_card_overlay_style = Column(Enum(OverlayStyle, name="overlay_style", create_constraint=False), default=OverlayStyle.NONE)

    # Routine card
    routine_card_edges = Column(Enum(CardEdges, name="card_edges", create_constraint=False), default=CardEdges.ROUNDED)
    routine_card_background_color = Column(String(7), default="#FFFFFF")
    routine_card_overlay_style = Column(Enum(OverlayStyle, name="overlay_style", create_constraint=False), default=OverlayStyle.NONE)

    # UI elements
    ui_button_style = Column(Enum(CardEdges, name="card_edges", create_constraint=False), default=CardEdges.ROUNDED)
    ui_button_color = Column(String(7))
    ui_card_background = Column(String(7), default="#FFFFFF")

    brand = relationship("Brand", back_populates="image_style")
