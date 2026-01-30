"""
Professional AI-Powered Connection Management System
Refined for concise, actionable responses.
"""

import sqlite3
import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
from contextlib import contextmanager
from huggingface_hub import InferenceClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    HF_TOKEN: str = "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"
    MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    DB_PATH: str = "database_two.db"
    MAX_CANDIDATES: int = 8  # Reduced from 15
    MAX_RESPONSE_TOKENS: int = 250  # Reduced from 500
    CLASSIFICATION_TEMPERATURE: float = 0.1
    RESPONSE_TEMPERATURE: float = 0.6  # Slightly lower for more focused responses


class QueryCategory(Enum):
    SUMMARY_INSIGHTS = "Connection Summary & Insights"
    RECOMMENDATIONS = "Best Connection Recommendations"
    ENGAGEMENT = "Engagement & Follow-up Suggestions"
    ANALYTICS = "Connection Analytics & Tracking"
    OPPORTUNITY_MAPPING = "Opportunity Mapping"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Connection:
    id: Optional[int]
    full_name: str
    contact_info: Optional[str]
    job_title: Optional[str]
    company: Optional[str]
    industry: Optional[str]
    sector: Optional[str]
    skills_experience: Optional[str]
    ai_summary: Optional[str]
    ai_rating: int
    rating_momentum: Optional[str]
    key_accomplishments: Optional[str]
    relationship_status: Optional[str]
    days_since_contact: int
    mutual_connections: Optional[str]
    personal_notes: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict) -> 'Connection':
        return cls(
            id=data.get('id'),
            full_name=data.get('full_name', ''),
            contact_info=data.get('contact_info'),
            job_title=data.get('job_title'),
            company=data.get('company'),
            industry=data.get('industry'),
            sector=data.get('sector'),
            skills_experience=data.get('skills_experience'),
            ai_summary=data.get('ai_summary'),
            ai_rating=data.get('ai_rating', 5),
            rating_momentum=data.get('rating_momentum'),
            key_accomplishments=data.get('key_accomplishments'),
            relationship_status=data.get('relationship_status'),
            days_since_contact=data.get('days_since_contact', 0),
            mutual_connections=data.get('mutual_connections'),
            personal_notes=data.get('personal_notes')
        )

    def to_search_text(self) -> str:
        fields = [
            self.full_name or '',
            self.job_title or '',
            self.company or '',
            self.industry or '',
            self.sector or '',
            self.skills_experience or '',
            self.key_accomplishments or '',
            self.personal_notes or ''
        ]
        return ' '.join(fields).lower()


# ============================================================================
# DATABASE LAYER
# ============================================================================

class DatabaseManager:
    
    def __init__(self, db_path: str = Config.DB_PATH):
        self.db_path = db_path
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def get_all_connections(self) -> List[Connection]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM connections 
                    ORDER BY ai_rating DESC, days_since_contact ASC
                """)
                rows = cursor.fetchall()
                return [Connection.from_dict(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching connections: {e}")
            return []
    
    def add_connection(self, connection: Connection) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO connections (
                        full_name, contact_info, job_title, company, industry, 
                        sector, skills_experience, ai_summary, ai_rating, 
                        rating_momentum, key_accomplishments, relationship_status,
                        days_since_contact, mutual_connections, personal_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    connection.full_name, connection.contact_info, 
                    connection.job_title, connection.company, connection.industry,
                    connection.sector, connection.skills_experience, 
                    connection.ai_summary, connection.ai_rating,
                    connection.rating_momentum, connection.key_accomplishments,
                    connection.relationship_status, connection.days_since_contact,
                    connection.mutual_connections, connection.personal_notes
                ))
                conn.commit()
                logger.info(f"Successfully added connection: {connection.full_name}")
                return True
        except Exception as e:
            logger.error(f"Error adding connection: {e}")
            return False


# ============================================================================
# AI SERVICES - REFINED FOR CONCISE RESPONSES
# ============================================================================

class AIService:
    
    def __init__(self):
        self.client = InferenceClient(
            token=Config.HF_TOKEN,
            model=Config.MODEL
        )
    
    def classify_query(self, query: str) -> QueryCategory:
        categories_list = "\n".join([
            f"{i+1}. {cat.value}" 
            for i, cat in enumerate(QueryCategory)
        ])
        
        prompt = f"""Classify this query into ONE category:

CATEGORIES:
{categories_list}

QUERY: "{query}"

Return only the category name."""

        try:
            response = self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=Config.CLASSIFICATION_TEMPERATURE
            )
            
            category_text = response.choices[0].message.content.strip()
            
            for category in QueryCategory:
                if category.value.lower() in category_text.lower():
                    logger.info(f"Query classified as: {category.value}")
                    return category
            
            return QueryCategory.RECOMMENDATIONS
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return QueryCategory.RECOMMENDATIONS
    
    def generate_response(
        self, 
        category: QueryCategory, 
        query: str, 
        candidates: List[Connection]
    ) -> str:
        
        if not candidates:
            return self._generate_empty_response(query)
        
        # Build concise context (top 5 only)
        context = self._build_candidate_context(candidates[:5])
        
        # Streamlined system prompts
        system_prompts = {
            QueryCategory.SUMMARY_INSIGHTS: 
                "You're a network advisor. Provide brief, insightful analysis of connections. Keep it under 100 words.",
            
            QueryCategory.RECOMMENDATIONS: 
                "You're a networking strategist. Recommend 2-3 connections with brief reasoning. Keep it under 120 words.",
            
            QueryCategory.ENGAGEMENT: 
                "You're a relationship expert. Suggest engagement approach in 2-3 sentences with one actionable tip.",
            
            QueryCategory.ANALYTICS: 
                "You're a network analyst. Highlight 2-3 key patterns or insights. Keep it under 100 words.",
            
            QueryCategory.OPPORTUNITY_MAPPING: 
                "You're a strategy advisor. Provide focused action plan with 2-3 connections. Keep it under 120 words."
        }
        
        user_prompt = f"""QUERY: "{query}"

TOP CONNECTIONS:
{context}

{self._get_category_instruction(category)}

REQUIREMENTS:
- Keep response under {self._get_word_limit(category)} words
- Use clear, simple formatting
- Be specific and actionable
- No fluff or repetition
- List names naturally in recommendations

Response:"""

        try:
            response = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompts[category]},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=Config.MAX_RESPONSE_TOKENS,
                temperature=Config.RESPONSE_TEMPERATURE
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return "Unable to generate response. Please try rephrasing your query."
    
    def _build_candidate_context(self, candidates: List[Connection]) -> str:
        """Build minimal context for top candidates"""
        lines = []
        for i, c in enumerate(candidates, 1):
            lines.append(
                f"{i}. {c.full_name} - {c.job_title or 'N/A'} at {c.company or 'N/A'} "
                f"({c.industry or 'N/A'}) | Rating: {c.ai_rating}/10 | "
                f"Last contact: {c.days_since_contact}d ago"
            )
        return "\n".join(lines)
    
    def _get_word_limit(self, category: QueryCategory) -> int:
        """Category-specific word limits"""
        limits = {
            QueryCategory.SUMMARY_INSIGHTS: 100,
            QueryCategory.RECOMMENDATIONS: 120,
            QueryCategory.ENGAGEMENT: 80,
            QueryCategory.ANALYTICS: 100,
            QueryCategory.OPPORTUNITY_MAPPING: 120
        }
        return limits.get(category, 100)
    
    def _get_category_instruction(self, category: QueryCategory) -> str:
        """Concise instructions per category"""
        instructions = {
            QueryCategory.SUMMARY_INSIGHTS: 
                "Provide key insights about this connection's value and relationship status.",
            
            QueryCategory.RECOMMENDATIONS: 
                "List 2-3 best connections for this need with brief reasoning.",
            
            QueryCategory.ENGAGEMENT: 
                "Suggest when and how to reach out with one specific conversation starter.",
            
            QueryCategory.ANALYTICS: 
                "Identify 2-3 meaningful patterns in the network data.",
            
            QueryCategory.OPPORTUNITY_MAPPING: 
                "Show how 2-3 connections can help achieve this goal with clear next steps."
        }
        return instructions[category]
    
    def _generate_empty_response(self, query: str) -> str:
        return f"""No matches found for: "{query}"

Try broader search terms or add more connections to your network."""


# ============================================================================
# SEARCH ENGINE
# ============================================================================

class ConnectionSearchEngine:
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        stop_words = {
            'who', 'what', 'when', 'where', 'how', 'can', 'should',
            'the', 'for', 'and', 'with', 'about', 'help', 'me', 'my'
        }
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if len(w) > 2 and w not in stop_words]
    
    @staticmethod
    def calculate_relevance_score(
        connection: Connection,
        keywords: List[str],
        category: QueryCategory,
        query_lower: str
    ) -> float:
        score = 0.0
        search_text = connection.to_search_text()
        name_lower = (connection.full_name or '').lower()
        
        for keyword in keywords:
            if keyword in search_text:
                score += 2.0
            if keyword in (connection.industry or '').lower():
                score += 8.0
            if keyword in (connection.sector or '').lower():
                score += 7.0
            if keyword in (connection.job_title or '').lower():
                score += 6.0
            if keyword in name_lower:
                score += 50.0 if any(kw in query_lower for kw in name_lower.split()) else 15.0
        
        if category == QueryCategory.SUMMARY_INSIGHTS:
            if any(kw in name_lower for kw in keywords):
                score += 100.0
        
        elif category == QueryCategory.ENGAGEMENT:
            days = connection.days_since_contact or 0
            if 14 <= days <= 90:
                score += 20.0
            elif days > 90:
                score += 10.0
            
        elif category == QueryCategory.ANALYTICS:
            score += (connection.ai_rating or 5) * 3.0
            if connection.rating_momentum == 'improving':
                score += 12.0
        
        else:
            score += (connection.ai_rating or 5) * 2.5
            if connection.relationship_status in ['inner circle', 'professional']:
                score += 10.0
        
        return score
    
    def find_relevant_connections(
        self,
        query: str,
        category: QueryCategory,
        all_connections: List[Connection],
        limit: int = Config.MAX_CANDIDATES
    ) -> List[Connection]:
        
        if not all_connections:
            return []
        
        keywords = self.extract_keywords(query)
        query_lower = query.lower()
        
        scored_connections = []
        
        for connection in all_connections:
            score = self.calculate_relevance_score(
                connection, keywords, category, query_lower
            )
            
            if score > 3.0:
                scored_connections.append((score, connection))
        
        scored_connections.sort(key=lambda x: x[0], reverse=True)
        
        logger.info(f"Found {len(scored_connections)} relevant connections")
        return [conn for _, conn in scored_connections[:limit]]


# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

class ConnectionIntelligenceSystem:
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.ai_service = AIService()
        self.search_engine = ConnectionSearchEngine()
    
    def process_query(self, query: str) -> str:
        
        if not query or len(query.strip()) < 3:
            return "Please provide a more specific query."
        
        logger.info(f"Processing query: {query}")
        
        all_connections = self.db_manager.get_all_connections()
        
        if not all_connections:
            return """Your network is empty. Add connections to get started with AI-powered insights."""
        
        category = self.ai_service.classify_query(query)
        candidates = self.search_engine.find_relevant_connections(
            query, category, all_connections
        )
        
        response = self.ai_service.generate_response(
            category, query, candidates
        )
        
        return response


# ============================================================================
# PUBLIC API
# ============================================================================

_system = ConnectionIntelligenceSystem()

def process_ai_query(query: str) -> str:
    return _system.process_query(query)

def add_connection(data: Dict) -> bool:
    try:
        connection = Connection.from_dict(data)
        return _system.db_manager.add_connection(connection)
    except Exception as e:
        logger.error(f"Error adding connection: {e}")
        return False

def get_all_connections() -> List[Dict]:
    connections = _system.db_manager.get_all_connections()
    return [vars(conn) for conn in connections]

def get_all_people():
    connections = get_all_connections()
    return [
        {
            "id": conn.get("id"),
            "full_name": conn.get("full_name") or "Unnamed",
            "contact_info": conn.get("contact_info") or "",
            "job_title": conn.get("job_title") or "Not specified",
            "company": conn.get("company") or "Not specified",
            "industry": conn.get("industry") or "Not specified",
            "sector": conn.get("sector") or "Not specified",
            "ai_rating": conn.get("ai_rating") or 5,
            "days_since_contact": conn.get("days_since_contact") or 0,
            "relationship_status": conn.get("relationship_status") or "Professional",
            "key_accomplishments": conn.get("key_accomplishments") or "",
            "personal_notes": conn.get("personal_notes") or ""
        }
        for conn in connections
    ]

def add_person(data: dict):
    cleaned_data = {
        "id": None,
        "full_name": data.get("full_name", "").strip(),
        "contact_info": data.get("contact_info"),
        "job_title": data.get("job_title"),
        "company": data.get("company"),
        "industry": data.get("industry"),
        "sector": data.get("sector"),
        "skills_experience": data.get("skills_experience"),
        "ai_summary": data.get("ai_summary"),
        "ai_rating": int(data.get("ai_rating", 5)) if data.get("ai_rating") else 5,
        "rating_momentum": data.get("rating_momentum"),
        "key_accomplishments": data.get("key_accomplishments"),
        "relationship_status": data.get("relationship_status"),
        "days_since_contact": int(data.get("days_since_contact", 0)),
        "mutual_connections": data.get("mutual_connections"),
        "personal_notes": data.get("personal_notes")
    }
    return add_connection(cleaned_data)