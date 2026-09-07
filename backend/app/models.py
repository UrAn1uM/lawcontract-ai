"""ORM 实体：用户 / 合同与版本 / 条款库 / 法规库 / 审查报告 / 问答会话。"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(20), default="user")  # user / admin
    created_at = Column(DateTime, default=datetime.utcnow)

    contracts = relationship("Contract", back_populates="owner")


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    contract_type = Column(String(50), default="其他")
    status = Column(String(20), default="uploaded")  # uploaded / reviewed / generated
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="contracts")
    versions = relationship(
        "ContractVersion",
        back_populates="contract",
        order_by="ContractVersion.version_no",
    )
    reports = relationship("ReviewReport", back_populates="contract")


class ContractVersion(Base):
    __tablename__ = "contract_versions"

    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, index=True)
    version_no = Column(Integer, default=1)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    contract = relationship("Contract", back_populates="versions")


class Clause(Base):
    """标准条款库：RAG 知识源之一，供风险比对与生成参考。"""

    __tablename__ = "clauses"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    category = Column(String(50), default="通用")  # 违约责任/保密/知识产权/付款...
    risk_level = Column(String(10), default="低")  # 该条款偏离时的风险等级
    content = Column(Text, nullable=False)
    source = Column(String(200), default="自定义")
    created_at = Column(DateTime, default=datetime.utcnow)


class Regulation(Base):
    """法规库：GDPR / 数据安全法 / 个人信息保护法等条文。"""

    __tablename__ = "regulations"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)  # 法规名称
    article_no = Column(String(50), nullable=False)  # 第X条
    jurisdiction = Column(String(50), default="中国")  # 中国 / 欧盟
    content = Column(Text, nullable=False)
    effective_date = Column(String(20), default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class ReviewReport(Base):
    __tablename__ = "review_reports"

    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, index=True)
    review_type = Column(String(20), default="risk")  # risk / compliance
    overall_risk = Column(String(20), default="无风险")  # 高 / 中 / 低 / 无风险
    summary = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    contract = relationship("Contract", back_populates="reports")
    items = relationship(
        "RiskItem", back_populates="report", cascade="all, delete-orphan"
    )


class RiskItem(Base):
    __tablename__ = "risk_items"

    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey("review_reports.id"), nullable=False, index=True)
    clause_no = Column(String(50), default="")
    risk_level = Column(String(10), default="低")
    title = Column(String(200), default="")
    description = Column(Text, default="")
    suggestion = Column(Text, default="")
    legal_basis = Column(Text, default="")

    report = relationship("ReviewReport", back_populates="items")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), default="新会话")
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship(
        "ChatMessage", back_populates="session", order_by="ChatMessage.id"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String(20))  # user / assistant
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")
