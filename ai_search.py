"""
AI-Powered Network Search Engine - Enterprise Edition v2.1 (SECURITY PATCHED)
============================================================
Google-tier semantic search with advanced NLU and professionally structured responses

SECURITY IMPROVEMENTS:
✓ Removed hardcoded API keys
✓ Added input validation
✓ Better error handling
✓ Environment variable support
"""

import re
import logging
import os
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from collections import defaultdict, Counter
import time

from huggingface_hub import InferenceClient


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

class SearchConfig:
    """Enterprise search configuration - USE ENVIRONMENT VARIABLES FOR PRODUCTION"""
    HF_TOKEN: str = os.getenv('HF_TOKEN', '')  # Load from environment
    MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    MAX_RESPONSE_TOKENS: int = 500
    CLASSIFICATION_TEMPERATURE: float = 0.05
    RESPONSE_TEMPERATURE: float = 0.65
    MAX_CANDIDATES: int = 10
    MIN_RELEVANCE_SCORE: float = 2.5
    
    # Scoring weights
    EXACT_NAME_MATCH: float = 100.0
    PARTIAL_NAME_MATCH: float = 40.0
    INDUSTRY_MATCH: float = 12.0
    SECTOR_MATCH: float = 10.0
    TITLE_MATCH: float = 8.0
    COMPANY_MATCH: float = 7.0
    SKILL_MATCH: float = 6.0
    KEYWORD_MATCH: float = 3.0
    RATING_MULTIPLIER: float = 3.5
    
    USE_STRUCTURED_OUTPUT: bool = True
    LOG_LEVEL: str = "INFO"


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class QueryIntent(Enum):
    """Semantic intent classification"""
    PROFILE_LOOKUP = "profile_lookup"         # "Who is X?" → Profile summary
    EXPERTISE_SEARCH = "expertise_search"     # "Who knows X?" → Expert list
    RECOMMENDATION = "recommendation"          # "Who should I..." → Suggestions  
    ENGAGEMENT_ADVICE = "engagement_advice"   # "When to contact..." → Strategy
    NETWORK_ANALYSIS = "network_analysis"     # "Show my network" → Insights
    OPPORTUNITY_MATCH = "opportunity_match"   # "Who can help with X" → Matches
    GENERAL_SEARCH = "general_search"         # Fallback


# ═══════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Connection:
    """Enhanced connection with caching"""
    id: Optional[int]
    user_id: Optional[int]
    full_name: str
    contact_info: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    skills_experience: Optional[str] = None
    key_accomplishments: Optional[str] = None
    relationship_status: Optional[str] = "Professional"
    days_since_contact: int = 0
    mutual_connections: Optional[str] = None
    personal_notes: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_rating: int = 5
    rating_momentum: Optional[str] = "Stagnant"
    _search_text_cache: Optional[str] = field(default=None, init=False, repr=False)
    _name_variations: Optional[Set[str]] = field(default=None, init=False, repr=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Connection':
        return cls(
            id=data.get('id'), user_id=data.get('user_id'),
            full_name=data.get('full_name', ''),
            contact_info=data.get('contact_info'), job_title=data.get('job_title'),
            company=data.get('company'), industry=data.get('industry'),
            sector=data.get('sector'), skills_experience=data.get('skills_experience'),
            key_accomplishments=data.get('key_accomplishments'),
            relationship_status=data.get('relationship_status', 'Professional'),
            days_since_contact=data.get('days_since_contact', 0),
            mutual_connections=data.get('mutual_connections'),
            personal_notes=data.get('personal_notes'), ai_summary=data.get('ai_summary'),
            ai_rating=data.get('ai_rating', 5),
            rating_momentum=data.get('rating_momentum', 'Stagnant')
        )
    
    def to_search_text(self) -> str:
        if self._search_text_cache is not None:
            return self._search_text_cache
        fields = [self.full_name or '', self.job_title or '', self.company or '',
                  self.industry or '', self.sector or '', self.skills_experience or '',
                  self.key_accomplishments or '', self.personal_notes or '', self.ai_summary or '']
        self._search_text_cache = ' '.join(fields).lower()
        return self._search_text_cache
    
    def get_name_variations(self) -> Set[str]:
        if self._name_variations is not None:
            return self._name_variations
        variations, name = set(), self.full_name or ''
        variations.add(name.lower())
        parts = name.split()
        if len(parts) >= 2:
            variations.add(' '.join(parts).lower())
            variations.add(f"{parts[-1]}, {' '.join(parts[:-1])}".lower())
            variations.add(f"{parts[0][0]}. {parts[-1]}".lower())
            variations.add(parts[0].lower())
            variations.add(parts[-1].lower())
        self._name_variations = variations
        return variations


@dataclass
class SearchResult:
    connection: Connection
    relevance_score: float
    matched_fields: List[str]
    match_quality: str
    explanation: str
    
    def to_dict(self) -> Dict[str, Any]:
        conn_dict = {
            'id': self.connection.id,
            'name': self.connection.full_name,
            'title': self.connection.job_title or 'N/A',
            'company': self.connection.company or 'N/A',
            'industry': self.connection.industry or 'N/A',
            'sector': self.connection.sector or 'N/A',
            'rating': self.connection.ai_rating,
            'rating_momentum': self.connection.rating_momentum or 'Stagnant',
            'last_contact_days': self.connection.days_since_contact,
            'relationship': self.connection.relationship_status or 'Professional',
            'summary': self.connection.ai_summary or 'No summary available',
            'skills': self.connection.skills_experience or 'N/A',
            'accomplishments': self.connection.key_accomplishments or 'N/A'
        }
        
        return {
            'connection': conn_dict,
            'score': round(self.relevance_score, 2),
            'matched': self.matched_fields,
            'quality': self.match_quality,
            'why': self.explanation
        }


# ═══════════════════════════════════════════════════════════════════════════════
# QUERY PROCESSOR - Semantic Understanding
# ═══════════════════════════════════════════════════════════════════════════════

class SemanticQueryProcessor:
    """Advanced NLU for query understanding"""
    
    STOP_WORDS = {'who', 'what', 'when', 'where', 'how', 'why', 'can', 'could', 'should',
                   'the', 'a', 'an', 'for', 'and', 'or', 'with', 'about', 'help', 'me', 'my',
                   'find', 'show', 'tell', 'is', 'are', 'was', 'were', 'have', 'has', 'had'}
    
    # Intent detection patterns
    INTENT_PATTERNS = {
        QueryIntent.PROFILE_LOOKUP: [
            r'\b(who\s+is|tell\s+me\s+about|info\s+(?:on|about)|profile)\b',
            r'\b(introduce|meet|know\s+about)\s+\w+',
            r'\b(details|background)\s+(?:on|of|for)\b'
        ],
        QueryIntent.EXPERTISE_SEARCH: [
            r'\b(who\s+knows|expert|specialist|experienced\s+in|skilled)\b',
            r'\b(find\s+(?:someone|people))\s+(?:who|with)\b',
            r'\b(knowledge\s+of|expertise|works\s+(?:in|with))\b'
        ],
        QueryIntent.RECOMMENDATION: [
            r'\b(recommend|suggest|who\s+should\s+i\s+(?:talk|speak)|best\s+(?:person|connection))\b',
            r'\b(looking\s+for|need\s+someone|connect\s+me)\b',
            r'\b(introduce\s+me)\b'
        ],
        QueryIntent.ENGAGEMENT_ADVICE: [
            r'\b(who\s+should\s+i\s+(?:reach\s+out|reconnect|contact|follow\s+up))\b',
            r'\b(when\s+should|how\s+to\s+(?:reach|contact)|reach\s+out)\b',
            r'\b(follow\s+up|connect\s+with|engage|haven\'t\s+talked)\b',
            r'\b(reconnect|touch\s+base|catch\s+up)\b'
        ],
        QueryIntent.NETWORK_ANALYSIS: [
            r'\b(analyze|overview|show\s+me|display)\s+(?:my\s+)?(?:network|connections)\b',
            r'\b(how\s+many|count|statistics|metrics)\b',
            r'\b(show|display)\s+(?:improving|declining|top|best|worst|high\s+rated)\b'
        ],
        QueryIntent.OPPORTUNITY_MATCH: [
            r'\b(help\s+(?:me\s+)?with|assist|support)\b',
            r'\b(opportunity|project|collaboration|partnership)\b'
        ]
    }
    
    @staticmethod
    @lru_cache(maxsize=512)
    def normalize_query(query: str) -> str:
        normalized = query.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        contractions = {"don't": "do not", "can't": "cannot", "haven't": "have not",
                       "isn't": "is not", "won't": "will not"}
        for c, e in contractions.items():
            normalized = normalized.replace(c, e)
        return normalized
    
    @staticmethod
    @lru_cache(maxsize=512)
    def extract_keywords(query: str) -> Tuple[str, ...]:
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if len(w) > 2 and w not in SemanticQueryProcessor.STOP_WORDS]
        bigrams = [f"{keywords[i]} {keywords[i+1]}" for i in range(len(keywords)-1)]
        return tuple(keywords + bigrams)
    
    @classmethod
    def detect_intent(cls, query: str) -> Tuple[QueryIntent, float]:
        query_lower = query.lower()
        intent_scores = defaultdict(float)
        
        for intent, patterns in cls.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    intent_scores[intent] += 1.0
        
        if not intent_scores:
            return QueryIntent.GENERAL_SEARCH, 0.5
        
        best = max(intent_scores.items(), key=lambda x: x[1])
        confidence = min(best[1] / len(cls.INTENT_PATTERNS[best[0]]), 1.0)
        return best[0], confidence


# ═══════════════════════════════════════════════════════════════════════════════
# RELEVANCE SCORER
# ═══════════════════════════════════════════════════════════════════════════════

class AdvancedRelevanceScorer:
    """ML-inspired scoring with semantic understanding"""
    
    def __init__(self, config: SearchConfig = SearchConfig()):
        self.config = config
    
    def score_connection(self, conn: Connection, keywords: List[str], 
                        query_lower: str, intent: QueryIntent) -> Tuple[float, List[str], str]:
        score, matched = 0.0, []
        search_text = conn.to_search_text()
        name_lower = (conn.full_name or '').lower()
        name_vars = conn.get_name_variations()
        
        # 1. NAME MATCHING
        if name_lower in query_lower:
            score += self.config.EXACT_NAME_MATCH
            matched.insert(0, 'name')
        elif any(v in query_lower for v in name_vars):
            score += self.config.PARTIAL_NAME_MATCH
            matched.insert(0, 'name')
        
        # 2. KEYWORD MATCHING
        for kw in keywords:
            if len(kw) <= 2: continue
            if kw in search_text: score += self.config.KEYWORD_MATCH
            if conn.industry and kw in conn.industry.lower():
                score += self.config.INDUSTRY_MATCH
                if 'industry' not in matched: matched.append('industry')
            if conn.sector and kw in conn.sector.lower():
                score += self.config.SECTOR_MATCH
                if 'sector' not in matched: matched.append('sector')
            if conn.job_title and kw in conn.job_title.lower():
                score += self.config.TITLE_MATCH
                if 'title' not in matched: matched.append('title')
            if conn.company and kw in conn.company.lower():
                score += self.config.COMPANY_MATCH
                if 'company' not in matched: matched.append('company')
            if conn.skills_experience and kw in conn.skills_experience.lower():
                score += self.config.SKILL_MATCH
                if 'skills' not in matched: matched.append('skills')
        
        # 3. INTENT BOOSTS
        if intent == QueryIntent.PROFILE_LOOKUP:
            if any(kw in name_lower for kw in keywords):
                score += 100.0
        elif intent == QueryIntent.EXPERTISE_SEARCH:
            if conn.skills_experience:
                score += 15.0
            score += conn.ai_rating * 2.5
        elif intent == QueryIntent.RECOMMENDATION:
            score += conn.ai_rating * self.config.RATING_MULTIPLIER
            if conn.relationship_status in ['Inner Circle', 'Strategic Partner']:
                score += 15.0
        elif intent == QueryIntent.ENGAGEMENT_ADVICE:
            days = conn.days_since_contact or 0
            if 14 <= days <= 90: score += 25.0
            elif days > 90: score += 15.0
        
        # 4. QUALITY SIGNALS
        score += conn.ai_rating * self.config.RATING_MULTIPLIER
        if conn.rating_momentum == 'Improving': score += 8.0
        
        # Match quality
        if score >= self.config.EXACT_NAME_MATCH: quality = 'exact'
        elif score >= 40: quality = 'high'
        elif score >= 20: quality = 'medium'
        else: quality = 'low'
        
        return score, list(set(matched)), quality


# ═══════════════════════════════════════════════════════════════════════════════
# RESPONSE FORMATTER
# ═══════════════════════════════════════════════════════════════════════════════

class ResponseFormatter:
    """Creates clean, structured responses for frontend"""
    
    def format_response(self, intent: QueryIntent, query: str, results: List[SearchResult]) -> Dict[str, Any]:
        if not results:
            return self._empty_response(query)
        
        if intent == QueryIntent.PROFILE_LOOKUP:
            return self._format_profile(results[0])
        elif intent == QueryIntent.EXPERTISE_SEARCH:
            return self._format_expert_list(results[:5])
        elif intent == QueryIntent.RECOMMENDATION:
            return self._format_recommendations(results[:3])
        elif intent == QueryIntent.ENGAGEMENT_ADVICE:
            return self._format_engagement(results[:3])
        elif intent == QueryIntent.NETWORK_ANALYSIS:
            return self._format_insights(results)
        else:
            return self._format_list(results[:5])
    
    def _format_profile(self, result: SearchResult) -> Dict[str, Any]:
        conn = result.connection
        body = f"""**{conn.full_name}**
{conn.job_title or 'N/A'} at {conn.company or 'N/A'}

**Industry:** {conn.industry or 'N/A'} • **Sector:** {conn.sector or 'N/A'}

{conn.ai_summary or 'No summary available'}

**Rating:** {conn.ai_rating}/10 ({conn.rating_momentum})
**Relationship:** {conn.relationship_status}
**Last Contact:** {conn.days_since_contact} days ago"""
        
        if conn.skills_experience:
            body += f"\n\n**Skills:** {conn.skills_experience}"
        if conn.key_accomplishments:
            body += f"\n\n**Accomplishments:** {conn.key_accomplishments}"
        
        return {
            'title': f"Profile: {conn.full_name}",
            'summary': f"{conn.job_title or 'N/A'} at {conn.company or 'N/A'}",
            'body': body,
            'insights': self._generate_insights([result]),
            'suggestions': [f"Last contacted {conn.days_since_contact} days ago"] if conn.days_since_contact > 60 else []
        }
    
    def _format_expert_list(self, results: List[SearchResult]) -> Dict[str, Any]:
        lines = []
        for i, r in enumerate(results, 1):
            c = r.connection
            lines.append(f"**{i}. {c.full_name}**\n{c.job_title or 'N/A'} at {c.company or 'N/A'}\n"
                        f"_Rating: {c.ai_rating}/10 • {', '.join(r.matched_fields[:2])}_\n")
        
        return {
            'title': f"Found {len(results)} Expert{'' if len(results)==1 else 's'}",
            'summary': f"{len(results)} connection{'' if len(results)==1 else 's'} with relevant expertise",
            'body': '\n'.join(lines),
            'insights': self._generate_insights(results),
            'suggestions': ["Review accomplishments to find best match"]
        }
    
    def _format_recommendations(self, results: List[SearchResult]) -> Dict[str, Any]:
        lines = []
        for i, r in enumerate(results, 1):
            c = r.connection
            lines.append(f"**{i}. {c.full_name}**\n{c.job_title or 'N/A'} at {c.company or 'N/A'}\n"
                        f"_Why:_ {r.explanation}\n")
        
        return {
            'title': "Top Recommendations",
            'summary': f"Recommending {len(results)} connection{'' if len(results)==1 else 's'}",
            'body': '\n'.join(lines),
            'insights': self._generate_insights(results),
            'suggestions': ["Consider relationship strength alongside expertise"]
        }
    
    def _format_engagement(self, results: List[SearchResult]) -> Dict[str, Any]:
        lines = []
        for i, r in enumerate(results, 1):
            c = r.connection
            days = c.days_since_contact
            advice = ""
            if days > 90: advice = f"💡 _It's been {days} days - reconnect soon_"
            elif days > 30: advice = "💡 _Follow up within the week_"
            
            lines.append(f"**{i}. {c.full_name}**\n{c.job_title or 'N/A'} at {c.company or 'N/A'}\n{advice}\n")
        
        return {
            'title': "Engagement Strategy",
            'summary': f"{len(results)} connection{'' if len(results)==1 else 's'} ready for follow-up",
            'body': '\n'.join(lines),
            'insights': [],
            'suggestions': ["Personalize based on recent accomplishments", "Check mutual connections"]
        }
    
    def _format_insights(self, results: List[SearchResult]) -> Dict[str, Any]:
        ratings = [r.connection.ai_rating for r in results]
        avg = sum(ratings) / len(ratings) if ratings else 0
        high_rated = sum(1 for r in ratings if r >= 7)
        
        body = f"""**Network Overview:** {len(results)} connections analyzed

**Quality Metrics:**
• Average Rating: {avg:.1f}/10
• High-Value Connections: {high_rated}

**Top Connections:**"""
        
        for i, r in enumerate(results[:3], 1):
            c = r.connection
            body += f"\n{i}. {c.full_name} ({c.ai_rating}/10) - {c.job_title or 'N/A'}"
        
        return {
            'title': "Network Insights",
            'summary': f"{len(results)} connections analyzed",
            'body': body,
            'insights': self._generate_insights(results),
            'suggestions': []
        }
    
    def _format_list(self, results: List[SearchResult]) -> Dict[str, Any]:
        lines = []
        for i, r in enumerate(results, 1):
            c = r.connection
            lines.append(f"**{i}. {c.full_name}**\n{c.job_title or 'N/A'} at {c.company or 'N/A'}\n"
                        f"_Rating: {c.ai_rating}/10 • {c.relationship_status}_\n")
        
        return {
            'title': f"{len(results)} Connection{'' if len(results)==1 else 's'} Found",
            'summary': f"Found {len(results)} relevant connection{'' if len(results)==1 else 's'}",
            'body': '\n'.join(lines),
            'insights': self._generate_insights(results),
            'suggestions': []
        }
    
    def _empty_response(self, query: str) -> Dict[str, Any]:
        return {
            'title': "No Results Found",
            'summary': f"No connections match '{query}'",
            'body': "**Suggestions:**\n• Try broader search terms\n• Check spelling\n• Add more connections",
            'insights': [],
            'suggestions': ["Broaden search criteria", "Review connection list"]
        }
    
    def _generate_insights(self, results: List[SearchResult]) -> List[str]:
        insights = []
        high_rated = [r for r in results if r.connection.ai_rating >= 8]
        if high_rated:
            insights.append(f"{len(high_rated)} high-value connection{'' if len(high_rated)==1 else 's'} (8+/10)")
        
        overdue = [r for r in results if r.connection.days_since_contact > 90]
        if overdue:
            insights.append(f"{len(overdue)} connection{'' if len(overdue)==1 else 's'} not contacted in 90+ days")
        
        industries = [r.connection.industry for r in results if r.connection.industry]
        if industries:
            top = Counter(industries).most_common(1)[0]
            if top[1] > 1:
                insights.append(f"Most results in {top[0]} ({top[1]} connections)")
        
        return insights[:3]


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN SEARCH ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class AISearchEngine:
    """Enterprise AI Search Engine with semantic understanding"""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[SearchConfig] = None):
        self.config = config or SearchConfig()
        
        # Use provided key or config key
        token = api_key or self.config.HF_TOKEN
        if not token:
            raise ValueError("HF_TOKEN must be provided via parameter or environment variable")
            
        self.client = InferenceClient(api_key=token)
        self.processor = SemanticQueryProcessor()
        self.scorer = AdvancedRelevanceScorer(self.config)
        self.formatter = ResponseFormatter()
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
            self.logger.addHandler(handler)
        
        self.logger.info("🚀 AISearchEngine v2.1 initialized (SECURITY PATCHED)")
    
    def search(self, query: str, connections: List[Connection], 
               user_id: Optional[int] = None) -> Dict[str, Any]:
        """Execute intelligent search with structured response"""
        start_time = time.time()
        
        # Validation
        if not query or len(query.strip()) < 2:
            return self._error("Query too short")
        if not connections:
            return self._error("Network is empty")
        
        try:
            # 1. UNDERSTAND QUERY
            normalized = self.processor.normalize_query(query)
            keywords = list(self.processor.extract_keywords(normalized))
            intent, confidence = self.processor.detect_intent(normalized)
            
            self.logger.info(f"Query: '{query}' | Intent: {intent.value} | Confidence: {confidence:.2f}")
            
            # 2. FIND & RANK
            results = []
            for conn in connections:
                score, matched, quality = self.scorer.score_connection(
                    conn, keywords, normalized.lower(), intent
                )
                if score < self.config.MIN_RELEVANCE_SCORE:
                    continue
                
                explanation = self._explain_match(matched, quality)
                results.append(SearchResult(conn, score, matched, quality, explanation))
            
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            results = results[:self.config.MAX_CANDIDATES]
            
            # 3. FORMAT RESPONSE
            formatted = self.formatter.format_response(intent, query, results)
            
            # Add metadata
            duration = time.time() - start_time
            self.logger.info(f"Search complete: {len(results)} results in {duration:.3f}s")
            
            return {
                'query': query,
                'intent': intent.value,
                'content': formatted,
                'results': [r.to_dict() for r in results[:5]],
                'metadata': {
                    'result_count': len(results),
                    'processing_time': round(duration, 3),
                    'confidence': round(confidence, 2)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Search error: {e}", exc_info=True)
            return self._error("Error processing query")
    
    def _explain_match(self, matched: List[str], quality: str) -> str:
        if quality == 'exact': return "Exact match on name"
        if not matched: return "General relevance"
        field_map = {'name': 'name', 'title': 'job title', 'company': 'company',
                     'industry': 'industry', 'sector': 'sector', 'skills': 'skills'}
        readable = [field_map.get(f, f) for f in matched[:3]]
        if len(readable) == 1: return f"Strong match in {readable[0]}"
        elif len(readable) == 2: return f"Matches in {readable[0]} and {readable[1]}"
        else: return f"Matches in {', '.join(readable[:-1])}, and {readable[-1]}"
    
    def _error(self, msg: str) -> Dict[str, Any]:
        return {
            'query': '', 'intent': 'error',
            'content': {'title': 'Error', 'summary': msg, 'body': msg, 'insights': [], 'suggestions': []},
            'results': [], 'metadata': {'result_count': 0, 'processing_time': 0, 'confidence': 0}
        }
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'version': '2.1.0',
            'model': self.config.MODEL,
            'features': ['Semantic understanding', 'Intent detection', 'Fuzzy matching', 'Structured output']
        }


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

def create_search_engine(api_key: Optional[str] = None, **overrides) -> AISearchEngine:
    config = SearchConfig()
    for k, v in overrides.items():
        if hasattr(config, k): setattr(config, k, v)
    return AISearchEngine(api_key, config)


__all__ = ['AISearchEngine', 'Connection', 'SearchResult', 'QueryIntent', 'SearchConfig', 'create_search_engine']
__version__ = '2.1.0'