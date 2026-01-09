from sqlalchemy import Column, String, Float, DateTime, JSON, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database import Base
import datetime
import uuid

class User(Base):
    """Modelo de Usuario para autenticación"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Patient(Base):
    """Modelo para Pacientes"""
    __tablename__ = "patients"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    did = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relación opcional con logs, si se desea
    # session_logs = relationship("SessionLog", back_populates="patient")

class SessionLog(Base):
    """
    Nuevo modelo para PsychoWebAI.
    Almacena el registro de las sesiones, el texto crudo y el análisis de emociones.
    """
    __tablename__ = "session_logs"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    
    # Texto de la sesión o nota del paciente
    raw_text = Column(Text, nullable=False)
    
    # Análisis de emociones (JSON: {'alegria': 0.1, 'tristeza': 0.8, ...})
    emotion_analysis = Column(JSON, nullable=True)
    
    # Bandera de riesgo (True si se detectan palabras clave como "suicidio")
    risk_flag = Column(Boolean, default=False, index=True)
    
    # Informe clínico generado (Formato SOAP)
    soap_report = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relación con Patient
    patient = relationship("Patient")

class AnalysisFeedback(Base):
    """
    Modelo para Active Learning.
    Almacena las correcciones realizadas por el médico sobre el análisis de la IA.
    """
    __tablename__ = "analysis_feedback"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("session_logs.id"), nullable=False, index=True)
    
    # Análisis original de la IA (JSON)
    original_ai_output = Column(JSON, nullable=False)
    
    # Corrección del médico (JSON)
    doctor_corrected_output = Column(JSON, nullable=False)
    
    # Comentarios opcionales del médico
    comments = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relación
    session = relationship("SessionLog")