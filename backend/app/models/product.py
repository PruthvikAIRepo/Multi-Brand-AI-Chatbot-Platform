from sqlalchemy import Column, String, Text, Boolean, Integer, Numeric, DateTime, Enum, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import SkinType, SkinConcern


class Product(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "products"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    ingredients = Column(JSONB, server_default=text("'[]'::jsonb"))
    price = Column(Numeric(10, 2), nullable=False)
    image_url = Column(Text)
    category = Column(String(100), index=True)
    purchase_url = Column(Text)
    is_in_stock = Column(Boolean, default=True, index=True)
    priority_score = Column(Integer, default=0)
    deleted_at = Column(DateTime(timezone=True), index=True)

    brand = relationship("Brand", back_populates="products")
    skin_types = relationship("ProductSkinType", back_populates="product", cascade="all, delete-orphan")
    concerns = relationship("ProductConcern", back_populates="product", cascade="all, delete-orphan")


class ProductSkinType(Base, UUIDMixin):
    __tablename__ = "product_skin_types"

    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    skin_type = Column(Enum(SkinType, name="skin_type"), nullable=False)

    __table_args__ = (UniqueConstraint("product_id", "skin_type"),)

    product = relationship("Product", back_populates="skin_types")


class ProductConcern(Base, UUIDMixin):
    __tablename__ = "product_concerns"

    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    concern = Column(Enum(SkinConcern, name="skin_concern"), nullable=False)

    __table_args__ = (UniqueConstraint("product_id", "concern"),)

    product = relationship("Product", back_populates="concerns")
