"""
Medical Document Agent - Handles medical document upload, processing, and RAG queries

DEPLOYMENT NOTE: AI/ML models temporarily disabled for deployment
=================================================================
The following features are temporarily commented out to reduce deployment size:
1. Sentence Transformers (sentence-transformers) - for document embeddings
2. Transformers/BERT models (transformers) - for Named Entity Recognition
3. PyTorch (torch) - deep learning backend

To re-enable AI features after deployment:
1. Uncomment lines in pyproject.toml:
   - "sentence-transformers>=2.2.0"
   - "transformers>=4.35.0" 
   - "torch>=2.1.0"

2. Uncomment imports in this file:
   - from sentence_transformers import SentenceTransformer
   - from transformers import pipeline
   - import torch

3. Set feature flags to True:
   - EMBEDDINGS_AVAILABLE = True
   - NER_AVAILABLE = True

4. Uncomment model initialization and usage throughout this file
   (search for "Temporarily commented out for deployment")

Current functionality available without AI models:
- Document upload and basic text extraction
- Pattern-based medical entity extraction
- Document storage and basic search
- Medical history compilation
=================================================================
"""

import os
import json
import uuid
import base64
import hashlib
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import asyncio

# Import base agent
from .base_agent import BaseAgent

# Import file handling libraries
try:
    import aiofiles
    import filetype
    FILE_HANDLING_AVAILABLE = True
except ImportError:
    FILE_HANDLING_AVAILABLE = False
    print("WARNING: File handling libraries not available")

# Import medical document processing libraries
try:
    import pytesseract
    import cv2
    import numpy as np
    from PIL import Image
    from pdf2image import convert_from_path
    import pypdf
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("WARNING: OCR libraries not available")

# Import AI/ML libraries
try:
    import chromadb
    # Temporarily commented out for deployment - large model size
    # from sentence_transformers import SentenceTransformer
    # import torch
    # from transformers import pipeline
    AI_AVAILABLE = True
    # Set flags for temporarily disabled AI features
    EMBEDDINGS_AVAILABLE = False  # Will be True when sentence_transformers is enabled
    NER_AVAILABLE = False  # Will be True when transformers is enabled
except ImportError:
    AI_AVAILABLE = False
    EMBEDDINGS_AVAILABLE = False
    NER_AVAILABLE = False
    print("WARNING: AI/ML libraries not available")

# Import database models
try:
    from database import (
        Patient, MedicalDocument, ExtractedMedicalData, 
        DocumentEmbedding, SessionLocal
    )
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("WARNING: Database models not available")

class MedicalDocumentAgent(BaseAgent):
    """Agent specialized in medical document processing and RAG queries"""
    
    def __init__(self):
        super().__init__("Medical Document Agent", "medical_document_agent")
        self.upload_dir = Path(__file__).parent.parent / "uploads" / "medical_documents"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize AI models if available
        self.embedding_model = None
        self.ner_pipeline = None
        self.chroma_client = None
        self.chroma_collection = None
        
        if AI_AVAILABLE:
            try:
                # Initialize sentence transformer for embeddings
                # Temporarily commented out for deployment - large model size
                # self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                # print("✅ Embedding model initialized")
                print("⚠️ Embedding model disabled for deployment")
                
                # Initialize NER pipeline for medical entity extraction
                # Temporarily commented out for deployment - large model size
                # try:
                #     self.ner_pipeline = pipeline(
                #         "ner", 
                #         model="dbmdz/bert-large-cased-finetuned-conll03-english",
                #         aggregation_strategy="simple",
                #         device=0 if torch.cuda.is_available() else -1
                #     )
                #     print("✅ NER pipeline initialized")
                # except Exception as e:
                #     print(f"⚠️ NER pipeline failed, using fallback: {e}")
                print("⚠️ NER pipeline disabled for deployment")
                
                # Initialize ChromaDB for RAG
                self.chroma_client = chromadb.PersistentClient(
                    path=str(Path(__file__).parent.parent / "chroma_db")
                )
                self.chroma_collection = self.chroma_client.get_or_create_collection(
                    name="medical_documents",
                    metadata={"description": "Medical documents and extracted text"}
                )
                print("✅ ChromaDB initialized")
                
            except Exception as e:
                print(f"❌ Failed to initialize AI models: {e}")
                # Don't set AI_AVAILABLE to False here as it's a global variable
    
    def get_tools(self) -> List[str]:
        """Return list of medical document management tools"""
        return [
            "upload_medical_document",
            "process_medical_document", 
            "get_patient_medical_history",
            "search_medical_documents",
            "extract_medical_entities",
            "query_medical_knowledge",
            "get_document_by_id",
            "update_document_verification",
            "get_medical_timeline"
        ]
    
    def get_capabilities(self) -> List[str]:
        """Return list of medical document management capabilities"""
        return [
            "Medical document upload and storage",
            "OCR text extraction from images and PDFs",
            "AI-powered medical entity extraction",
            "Medical history timeline generation", 
            "RAG-based medical document search",
            "Prescription and lab result processing",
            "Medical knowledge query answering",
            "Document verification and validation"
        ]
    
    def upload_medical_document(
        self, 
        patient_id: str, 
        file_content: str, 
        file_name: str,
        document_type: str = "prescription",
        mime_type: str = None
    ) -> Dict[str, Any]:
        """Upload and store a medical document."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            # Decode base64 file content
            file_data = base64.b64decode(file_content)
            
            # Generate unique filename
            file_hash = hashlib.md5(file_data).hexdigest()
            file_extension = Path(file_name).suffix
            unique_filename = f"{patient_id}_{file_hash}{file_extension}"
            file_path = self.upload_dir / unique_filename
            
            # Detect file type if not provided
            if not mime_type and FILE_HANDLING_AVAILABLE:
                kind = filetype.guess(file_data)
                mime_type = kind.mime if kind else "application/octet-stream"
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Create database record
            db = self.get_db_session()
            document = MedicalDocument(
                patient_id=uuid.UUID(patient_id),
                document_type=document_type,
                file_name=file_name,
                file_path=str(file_path),
                file_size=len(file_data),
                mime_type=mime_type or "application/octet-stream",
                processing_status='pending'
            )
            db.add(document)
            db.commit()
            db.refresh(document)
            
            # Log interaction
            self.log_interaction(
                query=f"Upload medical document: {file_name}",
                response=f"Document uploaded successfully with ID: {document.id}",
                tool_used="upload_medical_document",
                metadata={"action": "document_upload", "confidence": 0.95}
            )
            
            return {
                "success": True,
                "document_id": str(document.id),
                "message": "Document uploaded successfully",
                "file_path": str(file_path),
                "processing_status": "pending"
            }
            
        except Exception as e:
            self.log_interaction(
                query=f"Upload medical document: {file_name}",
                response=f"Upload failed: {str(e)}",
                tool_used="upload_medical_document",
                metadata={"action": "document_upload_error", "error": str(e)}
            )
            return {"success": False, "message": f"Upload failed: {str(e)}"}
        finally:
            if 'db' in locals():
                db.close()
    
    def process_medical_document(self, document_id: str) -> Dict[str, Any]:
        """Process uploaded medical document with OCR and AI extraction."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            document = db.query(MedicalDocument).filter(
                MedicalDocument.id == uuid.UUID(document_id)
            ).first()
            
            if not document:
                return {"success": False, "message": "Document not found"}
            
            # Update status to processing
            document.processing_status = 'processing'
            db.commit()
            
            # Extract text based on file type
            extracted_text = ""
            if document.mime_type and document.mime_type.startswith('image/'):
                extracted_text = self._extract_text_from_image(document.file_path)
            elif document.mime_type == 'application/pdf':
                extracted_text = self._extract_text_from_pdf(document.file_path)
            else:
                # Try to read as text file
                try:
                    with open(document.file_path, 'r', encoding='utf-8') as f:
                        extracted_text = f.read()
                except:
                    extracted_text = "Could not extract text from this file type"
            
            # Store extracted text
            document.extracted_text = extracted_text
            
            # Extract medical entities using AI
            medical_entities = []
            if AI_AVAILABLE and extracted_text:
                medical_entities = self._extract_medical_entities(extracted_text)
                
                # Store extracted entities
                for entity in medical_entities:
                    # Extract additional fields
                    entity_value = entity.get('dosage', entity.get('value'))
                    doctor_name = entity.get('doctor')
                    
                    extracted_data = ExtractedMedicalData(
                        document_id=document.id,
                        patient_id=document.patient_id,
                        data_type=entity.get('entity_group', 'unknown').lower(),
                        entity_name=entity.get('word', ''),
                        entity_value=entity_value,
                        doctor_name=doctor_name,
                        extraction_confidence=float(entity.get('score', 0.0)),
                        extraction_method='AI_PARSING'
                    )
                    db.add(extracted_data)
                
                # Create embeddings for RAG
                self._create_document_embeddings(document.id, extracted_text)
            
            # Update processing status
            document.processing_status = 'completed'
            document.confidence_score = float(sum(e.get('score', 0) for e in medical_entities) / len(medical_entities) if medical_entities else 0.0)
            
            db.commit()
            
            self.log_interaction(
                query=f"Process document: {document.file_name}",
                response=f"Processed successfully. Extracted {len(medical_entities)} entities",
                tool_used="process_medical_document",
                metadata={"action": "document_processing", "entities_count": len(medical_entities)}
            )
            
            # Convert entities to pure Python types for JSON serialization
            clean_entities = []
            for entity in medical_entities[:10]:  # Return first 10 entities
                clean_entity = {
                    "entity_group": entity.get("entity_group", ""),
                    "score": float(entity.get("score", 0.0)),
                    "word": entity.get("word", ""),
                    "start": int(entity.get("start", 0)),
                    "end": int(entity.get("end", 0))
                }
                clean_entities.append(clean_entity)
            
            return {
                "success": True,
                "extracted_text": extracted_text,
                "entities_count": len(medical_entities),
                "entities": clean_entities,
                "confidence_score": float(document.confidence_score or 0.0)
            }
            
        except Exception as e:
            if 'document' in locals() and 'db' in locals():
                document.processing_status = 'failed'
                db.commit()
            
            return {"success": False, "message": f"Processing failed: {str(e)}"}
        finally:
            if 'db' in locals():
                db.close()
    
    def get_patient_medical_history(self, patient_id: str) -> Dict[str, Any]:
        """Get comprehensive medical history for a patient from documents."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            
            # Get all documents for patient
            documents = db.query(MedicalDocument).filter(
                MedicalDocument.patient_id == uuid.UUID(patient_id),
                MedicalDocument.processing_status == 'completed'
            ).order_by(MedicalDocument.upload_date.desc()).all()
            
            # Get extracted medical data
            medical_data = db.query(ExtractedMedicalData).filter(
                ExtractedMedicalData.patient_id == uuid.UUID(patient_id)
            ).order_by(ExtractedMedicalData.date_prescribed.desc()).all()
            
            # Organize by data type with proper mapping
            history = {
                "medications": [],
                "conditions": [],
                "procedures": [],
                "allergies": [],
                "vital_signs": [],
                "instructions": [],
                "documents": []
            }
            
            # Map data types to categories
            type_mapping = {
                "medication": "medications",
                "medicine": "medications",
                "drug": "medications",
                "diagnosis": "conditions",
                "condition": "conditions",
                "disease": "conditions",
                "symptom": "conditions",
                "allergy": "allergies",
                "allergic": "allergies",
                "procedure": "procedures",
                "surgery": "procedures",
                "operation": "procedures",
                "instruction": "instructions",
                "directions": "instructions",
                "vital": "vital_signs",
                "vitals": "vital_signs",
                "per": "conditions",  # Person names often get mixed with conditions
                "misc": "conditions"
            }
            
            for data in medical_data:
                # Map data type to appropriate category
                data_type = data.data_type.lower() if data.data_type else "misc"
                category = type_mapping.get(data_type, "conditions")
                
                # Skip person names unless they're clearly medical entities
                if data_type == "per" and len(data.entity_name.split()) <= 2:
                    # Skip simple person names
                    continue
                
                history[category].append({
                    "id": str(data.id),
                    "name": data.entity_name,
                    "value": data.entity_value,
                    "unit": data.entity_unit,
                    "date": data.date_prescribed.isoformat() if data.date_prescribed else None,
                    "doctor": data.doctor_name,
                    "confidence": float(data.extraction_confidence or 0.0)
                })
            
            for doc in documents:
                history["documents"].append({
                    "id": str(doc.id),
                    "type": doc.document_type,
                    "filename": doc.file_name,
                    "upload_date": doc.upload_date.isoformat(),
                    "confidence": float(doc.confidence_score or 0.0)
                })
            
            return {
                "success": True,
                "patient_id": patient_id,
                "total_documents": len(documents),
                "medical_history": history
            }
            
        except Exception as e:
            return {"success": False, "message": f"Failed to get medical history: {str(e)}"}
        finally:
            if 'db' in locals():
                db.close()
    
    def search_medical_documents(self, patient_id: str = None, document_type: str = None, 
                               date_from: str = None, date_to: str = None) -> Dict[str, Any]:
        """Search medical documents with filters."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            query = db.query(MedicalDocument)
            
            # Apply filters
            if patient_id:
                query = query.filter(MedicalDocument.patient_id == uuid.UUID(patient_id))
            if document_type:
                query = query.filter(MedicalDocument.document_type == document_type)
            if date_from:
                from_date = datetime.fromisoformat(date_from)
                query = query.filter(MedicalDocument.upload_date >= from_date)
            if date_to:
                to_date = datetime.fromisoformat(date_to)
                query = query.filter(MedicalDocument.upload_date <= to_date)
            
            documents = query.order_by(MedicalDocument.upload_date.desc()).all()
            
            results = []
            for doc in documents:
                results.append({
                    "id": str(doc.id),
                    "patient_id": str(doc.patient_id),
                    "type": doc.document_type,
                    "filename": doc.file_name,
                    "upload_date": doc.upload_date.isoformat(),
                    "status": doc.processing_status,
                    "confidence": float(doc.confidence_score or 0.0)
                })
            
            return {
                "success": True,
                "total_found": len(results),
                "documents": results
            }
            
        except Exception as e:
            return {"success": False, "message": f"Search failed: {str(e)}"}
        finally:
            if 'db' in locals():
                db.close()
    
    def query_medical_knowledge(self, query: str, patient_id: str = None) -> Dict[str, Any]:
        """Query medical documents using RAG system."""
        if not AI_AVAILABLE or not EMBEDDINGS_AVAILABLE:
            return {"success": False, "message": "AI/RAG system not available - embeddings disabled for deployment"}
        
        try:
            # Create query embedding
            # Temporarily commented out for deployment - requires sentence_transformers
            # query_embedding = self.embedding_model.encode([query])[0].tolist()
            return {"success": False, "message": "Embedding functionality disabled for deployment"}
            
            # Search in ChromaDB
            search_filter = {}
            if patient_id:
                search_filter = {"patient_id": patient_id}
            
            results = self.chroma_collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                where=search_filter if search_filter else None
            )
            
            # Format results
            relevant_docs = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    relevant_docs.append({
                        "text": doc,
                        "score": results['distances'][0][i] if results['distances'] else 0.0,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                    })
            
            return {
                "success": True,
                "query": query,
                "results_count": len(relevant_docs),
                "relevant_documents": relevant_docs
            }
            
        except Exception as e:
            return {"success": False, "message": f"Query failed: {str(e)}"}
    
    def extract_medical_entities(self, text: str) -> Dict[str, Any]:
        """Extract medical entities from text using AI."""
        if not AI_AVAILABLE:
            return {"success": False, "message": "AI system not available"}
        
        try:
            entities = self._extract_medical_entities(text)
            return {
                "success": True,
                "text": text,
                "entities_count": len(entities),
                "entities": entities
            }
        except Exception as e:
            return {"success": False, "message": f"Entity extraction failed: {str(e)}"}
    
    def get_document_by_id(self, document_id: str) -> Dict[str, Any]:
        """Get a specific document by ID."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            document = db.query(MedicalDocument).filter(
                MedicalDocument.id == uuid.UUID(document_id)
            ).first()
            
            if not document:
                return {"success": False, "message": "Document not found"}
            
            return {
                "success": True,
                "document": {
                    "id": str(document.id),
                    "patient_id": str(document.patient_id),
                    "type": document.document_type,
                    "filename": document.file_name,
                    "upload_date": document.upload_date.isoformat(),
                    "status": document.processing_status,
                    "extracted_text": document.extracted_text,
                    "confidence": float(document.confidence_score or 0.0)
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Failed to get document: {str(e)}"}
        finally:
            if 'db' in locals():
                db.close()
    
    def update_document_verification(self, document_id: str, verified: bool) -> Dict[str, Any]:
        """Update document verification status."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            
            # Update all extracted data for this document
            extracted_data = db.query(ExtractedMedicalData).filter(
                ExtractedMedicalData.document_id == uuid.UUID(document_id)
            ).all()
            
            for data in extracted_data:
                data.verified = verified
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Document verification updated to {verified}",
                "updated_entities": len(extracted_data)
            }
            
        except Exception as e:
            return {"success": False, "message": f"Verification update failed: {str(e)}"}
        finally:
            if 'db' in locals():
                db.close()
    
    def get_medical_timeline(self, patient_id: str) -> Dict[str, Any]:
        """Get chronological medical timeline for a patient."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            
            # Get all medical data with dates
            medical_data = db.query(ExtractedMedicalData).filter(
                ExtractedMedicalData.patient_id == uuid.UUID(patient_id),
                ExtractedMedicalData.date_prescribed.isnot(None)
            ).order_by(ExtractedMedicalData.date_prescribed.desc()).all()
            
            timeline = []
            for data in medical_data:
                timeline.append({
                    "date": data.date_prescribed.isoformat(),
                    "type": data.data_type,
                    "entity": data.entity_name,
                    "value": data.entity_value,
                    "doctor": data.doctor_name,
                    "verified": data.verified,
                    "confidence": float(data.extraction_confidence or 0.0)
                })
            
            return {
                "success": True,
                "patient_id": patient_id,
                "timeline_events": len(timeline),
                "timeline": timeline
            }
            
        except Exception as e:
            return {"success": False, "message": f"Timeline generation failed: {str(e)}"}
        finally:
            if 'db' in locals():
                db.close()
    
    def _extract_text_from_image(self, file_path: str) -> str:
        """Extract text from image using OCR."""
        if not OCR_AVAILABLE:
            return "OCR not available"
        
        try:
            # Load and preprocess image
            image = cv2.imread(file_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply image preprocessing for better OCR
            gray = cv2.medianBlur(gray, 3)
            
            # Use Tesseract OCR
            text = pytesseract.image_to_string(gray, config='--psm 6')
            return text.strip()
            
        except Exception as e:
            print(f"OCR extraction failed: {e}")
            return ""
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        if not OCR_AVAILABLE:
            return "PDF processing not available"
        
        try:
            text = ""
            
            # Try direct text extraction first
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            # If direct extraction fails, use OCR on PDF images
            if not text.strip():
                images = convert_from_path(file_path)
                for image in images:
                    text += pytesseract.image_to_string(image) + "\n"
            
            return text.strip()
            
        except Exception as e:
            print(f"PDF extraction failed: {e}")
            return ""
    
    def _extract_medical_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract medical entities using NER model and enhanced parsing."""
        try:
            entities = []
            
            # Use NER pipeline first
            # Temporarily commented out for deployment - requires transformers models
            # if self.ner_pipeline:
            #     ner_entities = self.ner_pipeline(text)
            #     entities.extend(ner_entities)
            
            # Enhanced medical content extraction (pattern-based, no AI models)
            enhanced_entities = self._extract_structured_medical_data(text)
            entities.extend(enhanced_entities)
            
            return entities
            
        except Exception as e:
            print(f"Entity extraction failed: {e}")
            return []
    
    def _extract_structured_medical_data(self, text: str) -> List[Dict[str, Any]]:
        """Extract structured medical data from text using patterns and keywords."""
        import re
        entities = []
        
        # Extract medications and dosages
        medication_patterns = [
            r'(\w+(?:\s+\w+)*)\s+(\d+\s*mg|mg|\d+\s*ml|ml|\d+\s*tablets?|\d+\s*capsules?)',
            r'(\w+(?:\s+\w+)*)\s+(\d+\s*mg)',
            r'(\d+\s*mg|\d+\s*ml)\s+(\w+(?:\s+\w+)*)',
        ]
        
        for pattern in medication_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    med_name = match.group(1).strip()
                    dosage = match.group(2).strip()
                    
                    # Filter out common non-medication words
                    non_medications = ['patient', 'name', 'date', 'birth', 'gender', 'male', 'female', 'return', 'review']
                    if med_name.lower() not in non_medications and len(med_name) > 2:
                        entities.append({
                            'entity_group': 'medication',
                            'word': med_name,
                            'dosage': dosage,
                            'score': 0.8,
                            'start': match.start(),
                            'end': match.end()
                        })
        
        # Extract diagnoses
        diagnosis_keywords = ['diagnosis:', 'diagnosed with', 'condition:', 'symptoms:', 'presents with']
        for keyword in diagnosis_keywords:
            pattern = rf'{keyword}\s*([^.]*\.?)'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                diagnosis = match.group(1).strip()
                if diagnosis and len(diagnosis) > 5:
                    entities.append({
                        'entity_group': 'diagnosis',
                        'word': diagnosis,
                        'score': 0.85,
                        'start': match.start(),
                        'end': match.end()
                    })
        
        # Extract allergies
        allergy_patterns = [
            r'allerg(?:y|ies)(?:\s+to)?\s*:?\s*([^.,;]+)',
            r'allergic\s+to\s+([^.,;]+)'
        ]
        
        for pattern in allergy_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                allergy = match.group(1).strip()
                if allergy and len(allergy) > 2:
                    entities.append({
                        'entity_group': 'allergy',
                        'word': allergy,
                        'score': 0.9,
                        'start': match.start(),
                        'end': match.end()
                    })
        
        # Extract instructions
        instruction_patterns = [
            r'instructions?:\s*([^.]*\.?)',
            r'take\s+([^.]*\.?)',
            r'avoid\s+([^.]*\.?)',
            r'(\d+\s+(?:tablet|capsule|spray)s?\s+[^.]*\.?)'
        ]
        
        for pattern in instruction_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                instruction = match.group(1).strip()
                if instruction and len(instruction) > 5:
                    entities.append({
                        'entity_group': 'instruction',
                        'word': instruction,
                        'score': 0.75,
                        'start': match.start(),
                        'end': match.end()
                    })
        
        # Extract doctor names
        doctor_patterns = [
            r'Dr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Doctor\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        for pattern in doctor_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                doctor = match.group(1).strip()
                if doctor:
                    entities.append({
                        'entity_group': 'doctor',
                        'word': doctor,
                        'score': 0.85,
                        'start': match.start(),
                        'end': match.end()
                    })
        
        return entities
    
    def _create_document_embeddings(self, document_id: uuid.UUID, text: str):
        """Create and store document embeddings for RAG."""
        try:
            if not AI_AVAILABLE or not EMBEDDINGS_AVAILABLE or not text.strip():
                print("⚠️ Skipping embeddings creation - disabled for deployment")
                return
            
            # Split text into chunks
            chunks = self._split_text_into_chunks(text, max_length=500)
            
            # Create embeddings for each chunk
            # Temporarily commented out for deployment - requires sentence_transformers
            # embeddings = self.embedding_model.encode(chunks)
            print("⚠️ Embeddings creation skipped - disabled for deployment")
            return
            
            # Store in ChromaDB
            chunk_ids = [f"{document_id}_{i}" for i in range(len(chunks))]
            
            self.chroma_collection.add(
                ids=chunk_ids,
                embeddings=embeddings.tolist(),
                documents=chunks,
                metadatas=[{
                    "document_id": str(document_id),
                    "chunk_index": i
                } for i in range(len(chunks))]
            )
            
        except Exception as e:
            print(f"Embedding creation failed: {e}")
    
    def _split_text_into_chunks(self, text: str, max_length: int = 500) -> List[str]:
        """Split text into smaller chunks for embedding."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > max_length:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
