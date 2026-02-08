"""
AI-Powered Relationship CRM - Enterprise Edition v3.0
=====================================================
Personable network search emphasizing what makes each connection uniquely valuable

KEY IMPROVEMENTS v3.0:
✓ Person-centric summaries (not rating-centric)
✓ Highlights unique/niche qualities
✓ Relationship context over metrics
✓ Clean, minimal, human-friendly output
✓ Ready for frontend integration
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
    """Relationship-first search configuration"""
    HF_TOKEN: str = os.getenv('HF_TOKEN', '')
    MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    MAX_RESPONSE_TOKENS: int = 500
    TEMPERATURE: float = 0.7  # Warmer for personable responses
    MAX_CANDIDATES: int = 10
    MIN_RELEVANCE_SCORE: float = 2.0  # Lower threshold for broader matches
    
    # Scoring weights - REBALANCED for relationship context
    EXACT_NAME_MATCH: float = 100.0
    PARTIAL_NAME_MATCH: float = 40.0
    NICHE_SKILL_MATCH: float = 25.0      # NEW: Reward unique skills
    ACCOMPLISHMENT_MATCH: float = 20.0   # NEW: Highlight achievements
    PERSONAL_NOTE_MATCH: float = 18.0    # NEW: Personal context matters
    INDUSTRY_MATCH: float = 12.0
    TITLE_MATCH: float = 10.0
    COMPANY_MATCH: float = 8.0
    SKILL_MATCH: float = 6.0
    KEYWORD_MATCH: float = 3.0
    
    # Relationship quality signals (not just ratings)
    INNER_CIRCLE_BOOST: float = 15.0
    RECENT_CONTACT_BOOST: float = 12.0
    IMPROVING_MOMENTUM_BOOST: float = 8.0
    
    LOG_LEVEL: str = "INFO"


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class QueryIntent(Enum):
    """What the user is really asking for"""
    PROFILE_LOOKUP = "profile_lookup"         # "Who is X?" → Tell me about them
    EXPERTISE_SEARCH = "expertise_search"     # "Who knows X?" → Find the expert
    RECOMMENDATION = "recommendation"          # "Who should I..." → Suggest someone
    ENGAGEMENT_ADVICE = "engagement_advice"   # "When to contact..." → Timing help
    NETWORK_ANALYSIS = "network_analysis"     # "Show my network" → Overview
    RELATIONSHIP_CONTEXT = "relationship_context"  # NEW: "How do I know X?"
    GENERAL_SEARCH = "general_search"         # Catch-all


# ═══════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Connection:
    """A person in your network - with human context"""
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
        """All searchable content - prioritize unique details"""
        if self._search_text_cache is not None:
            return self._search_text_cache
        
        # Weight personal context higher
        fields = [
            self.full_name or '',
            self.personal_notes or '',  # Personal context first
            self.key_accomplishments or '',  # Then unique achievements
            self.skills_experience or '',
            self.job_title or '',
            self.company or '',
            self.industry or '',
            self.sector or '',
            self.ai_summary or ''
        ]
        self._search_text_cache = ' '.join(fields).lower()
        return self._search_text_cache
    
    def get_name_variations(self) -> Set[str]:
        """Handle different name formats"""
        if self._name_variations is not None:
            return self._name_variations
        
        variations, name = set(), self.full_name or ''
        variations.add(name.lower())
        parts = name.split()
        
        if len(parts) >= 2:
            variations.add(' '.join(parts).lower())
            variations.add(f"{parts[-1]}, {' '.join(parts[:-1])}".lower())
            variations.add(f"{parts[0][0]}. {parts[-1]}".lower())
            variations.add(parts[0].lower())  # First name
            variations.add(parts[-1].lower())  # Last name
            
            # Middle initials
            if len(parts) >= 3:
                variations.add(f"{parts[0]} {parts[-1]}".lower())
        
        self._name_variations = variations
        return variations
    
    def get_unique_traits(self) -> List[str]:
        """Extract what makes this person special"""
        traits = []
        
        # Check for niche/unique keywords in skills
        if self.skills_experience:
            niche_indicators = ['rare', 'unique', 'specialized', 'expert', 'pioneered', 
                              'invented', 'founded', 'first', 'only', 'award']
            skills_lower = self.skills_experience.lower()
            if any(ind in skills_lower for ind in niche_indicators):
                traits.append(self.skills_experience)
        
        # Accomplishments are inherently unique
        if self.key_accomplishments:
            traits.append(self.key_accomplishments)
        
        # Personal notes often contain the quirky details
        if self.personal_notes:
            traits.append(self.personal_notes)
        
        return traits


@dataclass
class SearchResult:
    """A match with human-readable context"""
    connection: Connection
    relevance_score: float
    matched_fields: List[str]
    match_quality: str
    explanation: str
    unique_angle: Optional[str] = None  # NEW: What makes this match special
    
    def to_dict(self) -> Dict[str, Any]:
        """Clean output for frontend"""
        conn = self.connection
        
        # Build human-friendly connection summary
        conn_dict = {
            'id': conn.id,
            'name': conn.full_name,
            'title': conn.job_title or 'N/A',
            'company': conn.company or 'N/A',
            'industry': conn.industry or 'N/A',
            'relationship': conn.relationship_status or 'Professional',
            'last_contact': self._format_last_contact(conn.days_since_contact),
            
            # The good stuff - what makes them special
            'unique_traits': conn.get_unique_traits(),
            'summary': conn.ai_summary or 'No summary available',
            'skills': conn.skills_experience or 'N/A',
            'accomplishments': conn.key_accomplishments or 'N/A',
            'notes': conn.personal_notes or None,
            
            # Subtle context (not front-and-center)
            'meta': {
                'rating': conn.ai_rating,
                'momentum': conn.rating_momentum or 'Stagnant',
                'days_since_contact': conn.days_since_contact
            }
        }
        
        return {
            'connection': conn_dict,
            'relevance': round(self.relevance_score, 2),
            'matched_on': self.matched_fields,
            'quality': self.match_quality,
            'why': self.explanation,
            'angle': self.unique_angle  # NEW: Special insight
        }
    
    @staticmethod
    def _format_last_contact(days: int) -> str:
        """Human-readable time since contact"""
        if days == 0: return "Today"
        if days == 1: return "Yesterday"
        if days < 7: return f"{days} days ago"
        if days < 30: return f"{days // 7} weeks ago"
        if days < 90: return f"{days // 30} months ago"
        return f"{days // 30} months ago (overdue)"


# ═══════════════════════════════════════════════════════════════════════════════
# QUERY PROCESSOR
# ═══════════════════════════════════════════════════════════════════════════════

class SemanticQueryProcessor:
    """Understand what the user is really asking"""
    
    STOP_WORDS = {'who', 'what', 'when', 'where', 'how', 'why', 'can', 'could', 'should',
                   'the', 'a', 'an', 'for', 'and', 'or', 'with', 'about', 'help', 'me', 'my',
                   'find', 'show', 'tell', 'is', 'are', 'was', 'were', 'have', 'has', 'had'}
    
    INTENT_PATTERNS = {
        QueryIntent.PROFILE_LOOKUP: [
            r'\b(who\s+is|tell\s+me\s+about|info\s+(?:on|about)|profile|remind\s+me\s+about)\b',
            r'\b(introduce|meet|know\s+about|details\s+on)\b'
        ],
        QueryIntent.EXPERTISE_SEARCH: [
            r'\b(who\s+knows|expert|specialist|experienced\s+in|skilled|good\s+at)\b',
            r'\b(find\s+(?:someone|people))\s+(?:who|with)\b'
        ],
        QueryIntent.RECOMMENDATION: [
            r'\b(recommend|suggest|who\s+should\s+i\s+(?:talk|speak)|best\s+(?:person|connection))\b',
            r'\b(looking\s+for|need\s+someone|connect\s+me|introduce\s+me)\b'
        ],
        QueryIntent.ENGAGEMENT_ADVICE: [
            r'\b(who\s+should\s+i\s+(?:reach\s+out|reconnect|contact|follow\s+up))\b',
            r'\b(when\s+should|how\s+to\s+(?:reach|contact)|reach\s+out|touch\s+base)\b'
        ],
        QueryIntent.RELATIONSHIP_CONTEXT: [
            r'\b(how\s+do\s+i\s+know|where\s+did\s+i\s+meet|remind\s+me\s+how)\b',
            r'\b(what\'s\s+my\s+relationship|connection\s+with)\b'
        ],
        QueryIntent.NETWORK_ANALYSIS: [
            r'\b(analyze|overview|show\s+me|display)\s+(?:my\s+)?(?:network|connections)\b',
            r'\b(how\s+many|count|statistics|metrics)\b'
        ]
    }
    
    @staticmethod
    @lru_cache(maxsize=512)
    def normalize_query(query: str) -> str:
        """Clean and standardize query"""
        normalized = query.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        contractions = {
            "don't": "do not", "can't": "cannot", "haven't": "have not",
            "isn't": "is not", "won't": "will not", "who's": "who is",
            "what's": "what is", "where's": "where is"
        }
        for c, e in contractions.items():
            normalized = normalized.replace(c, e)
        return normalized
    
    @staticmethod
    @lru_cache(maxsize=512)
    def extract_keywords(query: str) -> Tuple[str, ...]:
        """Pull out meaningful search terms"""
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if len(w) > 2 and w not in SemanticQueryProcessor.STOP_WORDS]
        
        # Add bigrams for context
        bigrams = [f"{keywords[i]} {keywords[i+1]}" for i in range(len(keywords)-1)]
        
        return tuple(keywords + bigrams)
    
    @classmethod
    def detect_intent(cls, query: str) -> Tuple[QueryIntent, float]:
        """Figure out what the user wants"""
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
# RELEVANCE SCORER - Relationship-first
# ═══════════════════════════════════════════════════════════════════════════════

class RelationshipScorer:
    """Score connections by what makes them uniquely valuable"""
    
    def __init__(self, config: SearchConfig = SearchConfig()):
        self.config = config
    
    def score_connection(self, conn: Connection, keywords: List[str], 
                        query_lower: str, intent: QueryIntent) -> Tuple[float, List[str], str, Optional[str]]:
        """Score + explain the match with human context"""
        score, matched = 0.0, []
        search_text = conn.to_search_text()
        name_lower = (conn.full_name or '').lower()
        name_vars = conn.get_name_variations()
        unique_angle = None
        
        # ─────────────────────────────────────────────────────────────────────
        # 1. NAME MATCHING (still important for lookups)
        # ─────────────────────────────────────────────────────────────────────
        if name_lower in query_lower or query_lower in name_lower:
            score += self.config.EXACT_NAME_MATCH
            matched.insert(0, 'name')
            unique_angle = "Direct name match"
        elif any(v in query_lower for v in name_vars):
            score += self.config.PARTIAL_NAME_MATCH
            matched.insert(0, 'name')
        
        # ─────────────────────────────────────────────────────────────────────
        # 2. UNIQUE/NICHE MATCHING (what makes them special)
        # ─────────────────────────────────────────────────────────────────────
        for kw in keywords:
            if len(kw) <= 2: continue
            
            # Personal notes = gold (quirky details)
            if conn.personal_notes and kw in conn.personal_notes.lower():
                score += self.config.PERSONAL_NOTE_MATCH
                if 'personal_context' not in matched:
                    matched.append('personal_context')
                    unique_angle = f"Personal note mentions: {kw}"
            
            # Accomplishments = what they've done
            if conn.key_accomplishments and kw in conn.key_accomplishments.lower():
                score += self.config.ACCOMPLISHMENT_MATCH
                if 'accomplishments' not in matched:
                    matched.append('accomplishments')
                    if not unique_angle:
                        unique_angle = f"Notable for: {kw}"
            
            # Skills (check for niche indicators)
            if conn.skills_experience and kw in conn.skills_experience.lower():
                niche_boost = 0
                skills_lower = conn.skills_experience.lower()
                if any(x in skills_lower for x in ['expert', 'specialized', 'rare', 'unique']):
                    niche_boost = self.config.NICHE_SKILL_MATCH
                    if not unique_angle:
                        unique_angle = f"Specialized in {kw}"
                else:
                    niche_boost = self.config.SKILL_MATCH
                
                score += niche_boost
                if 'skills' not in matched:
                    matched.append('skills')
            
            # Industry/Sector/Title/Company (lower priority)
            if conn.industry and kw in conn.industry.lower():
                score += self.config.INDUSTRY_MATCH
                if 'industry' not in matched: matched.append('industry')
            
            if conn.job_title and kw in conn.job_title.lower():
                score += self.config.TITLE_MATCH
                if 'title' not in matched: matched.append('title')
            
            if conn.company and kw in conn.company.lower():
                score += self.config.COMPANY_MATCH
                if 'company' not in matched: matched.append('company')
            
            # General keyword match (catch-all)
            if kw in search_text:
                score += self.config.KEYWORD_MATCH
        
        # ─────────────────────────────────────────────────────────────────────
        # 3. RELATIONSHIP QUALITY (not just ratings)
        # ─────────────────────────────────────────────────────────────────────
        if conn.relationship_status in ['Inner Circle', 'Strategic Partner']:
            score += self.config.INNER_CIRCLE_BOOST
            if not unique_angle:
                unique_angle = f"{conn.relationship_status} relationship"
        
        if conn.rating_momentum == 'Improving':
            score += self.config.IMPROVING_MOMENTUM_BOOST
        
        # Recent contact = active relationship
        if 0 <= conn.days_since_contact <= 30:
            score += self.config.RECENT_CONTACT_BOOST
        
        # ─────────────────────────────────────────────────────────────────────
        # 4. INTENT-SPECIFIC BOOSTS
        # ─────────────────────────────────────────────────────────────────────
        if intent == QueryIntent.PROFILE_LOOKUP:
            # Boost if name keywords match
            if any(kw in name_lower for kw in keywords):
                score += 50.0
        
        elif intent == QueryIntent.EXPERTISE_SEARCH:
            # Boost if they have documented expertise
            if conn.skills_experience or conn.key_accomplishments:
                score += 20.0
        
        elif intent == QueryIntent.RECOMMENDATION:
            # Slight boost for quality relationships
            if conn.ai_rating >= 7:
                score += 10.0
        
        elif intent == QueryIntent.ENGAGEMENT_ADVICE:
            # Boost those who haven't been contacted recently
            days = conn.days_since_contact or 0
            if 14 <= days <= 90:
                score += 25.0
                if not unique_angle:
                    unique_angle = f"Haven't connected in {days} days"
            elif days > 90:
                score += 15.0
                if not unique_angle:
                    unique_angle = "Overdue for reconnection"
        
        # ─────────────────────────────────────────────────────────────────────
        # 5. MATCH QUALITY DETERMINATION
        # ─────────────────────────────────────────────────────────────────────
        if score >= self.config.EXACT_NAME_MATCH:
            quality = 'exact'
        elif score >= 40:
            quality = 'high'
        elif score >= 20:
            quality = 'medium'
        else:
            quality = 'low'
        
        return score, list(set(matched)), quality, unique_angle


# ═══════════════════════════════════════════════════════════════════════════════
# RESPONSE FORMATTER - Clean, minimal, personable
# ═══════════════════════════════════════════════════════════════════════════════

class PersonableFormatter:
    """Human-friendly, minimal output"""
    
    def format_response(self, intent: QueryIntent, query: str, 
                       results: List[SearchResult]) -> Dict[str, Any]:
        """Route to appropriate formatter"""
        if not results:
            return self._empty_response(query)
        
        formatters = {
            QueryIntent.PROFILE_LOOKUP: self._format_profile,
            QueryIntent.EXPERTISE_SEARCH: self._format_experts,
            QueryIntent.RECOMMENDATION: self._format_recommendation,
            QueryIntent.ENGAGEMENT_ADVICE: self._format_engagement,
            QueryIntent.RELATIONSHIP_CONTEXT: self._format_relationship,
            QueryIntent.NETWORK_ANALYSIS: self._format_insights
        }
        
        formatter = formatters.get(intent, self._format_simple_list)
        return formatter(results)
    
    def _format_profile(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Single person profile - focus on what makes them special"""
        result = results[0]
        conn = result.connection
        
        # Build the story
        header = f"**{conn.full_name}**"
        if conn.job_title and conn.company:
            header += f"\n{conn.job_title} at {conn.company}"
        elif conn.job_title:
            header += f"\n{conn.job_title}"
        
        body_parts = [header]
        
        # Their story (not their rating)
        if conn.ai_summary:
            body_parts.append(f"\n{conn.ai_summary}")
        
        # What makes them unique
        unique_traits = conn.get_unique_traits()
        if unique_traits:
            body_parts.append(f"\n**What makes them special:**")
            for trait in unique_traits[:2]:  # Top 2 only
                body_parts.append(f"• {trait}")
        
        # Context
        body_parts.append(f"\n**Relationship:** {conn.relationship_status}")
        body_parts.append(f"**Last contact:** {SearchResult._format_last_contact(conn.days_since_contact)}")
        
        # Mutual connections (if any)
        if conn.mutual_connections:
            body_parts.append(f"**Mutual connections:** {conn.mutual_connections}")
        
        return {
            'title': conn.full_name,
            'summary': f"{conn.job_title or 'Connection'} at {conn.company or 'Unknown'}",
            'body': '\n'.join(body_parts),
            'context': self._build_context(results),
            'next_steps': self._suggest_actions(conn)
        }
    
    def _format_experts(self, results: List[SearchResult]) -> Dict[str, Any]:
        """List of experts - highlight unique angles"""
        lines = []
        
        for i, r in enumerate(results[:5], 1):
            c = r.connection
            line = f"**{i}. {c.full_name}**"
            
            if c.job_title:
                line += f" – {c.job_title}"
            
            # Why they're a match (the unique angle)
            if r.unique_angle:
                line += f"\n   ↳ {r.unique_angle}"
            elif r.explanation:
                line += f"\n   ↳ {r.explanation}"
            
            lines.append(line)
        
        return {
            'title': f"Found {len(results)} expert{'' if len(results)==1 else 's'}",
            'summary': f"{len(results)} connection{'' if len(results)==1 else 's'} with relevant expertise",
            'body': '\n\n'.join(lines),
            'context': self._build_context(results),
            'next_steps': ["Review profiles to find best match", "Check recent activity"]
        }
    
    def _format_recommendation(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Suggest people - focus on why they're right"""
        lines = []
        
        for i, r in enumerate(results[:3], 1):
            c = r.connection
            line = f"**{i}. {c.full_name}**"
            
            # The pitch
            if r.unique_angle:
                line += f"\n   {r.unique_angle}"
            
            # Supporting details
            if c.relationship_status != 'Professional':
                line += f"\n   {c.relationship_status} • Last contact: {SearchResult._format_last_contact(c.days_since_contact)}"
            
            lines.append(line)
        
        return {
            'title': "Here's who I'd recommend",
            'summary': f"Top {len(results)} recommendation{'' if len(results)==1 else 's'} based on your network",
            'body': '\n\n'.join(lines),
            'context': self._build_context(results),
            'next_steps': ["Consider relationship strength", "Review mutual connections"]
        }
    
    def _format_engagement(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Who to reach out to - with timing context"""
        lines = []
        
        for i, r in enumerate(results[:3], 1):
            c = r.connection
            days = c.days_since_contact
            
            line = f"**{i}. {c.full_name}**"
            if c.job_title:
                line += f" – {c.job_title}"
            
            # Timing advice
            if days > 90:
                line += f"\n   🔴 {days} days since last contact – reconnect soon"
            elif days > 30:
                line += f"\n   🟡 {days} days – good time to follow up"
            else:
                line += f"\n   🟢 Recently connected ({days} days ago)"
            
            lines.append(line)
        
        return {
            'title': "Engagement opportunities",
            'summary': f"{len(results)} connection{'' if len(results)==1 else 's'} to consider",
            'body': '\n\n'.join(lines),
            'context': [],
            'next_steps': ["Personalize outreach", "Reference shared context", "Check for recent news"]
        }
    
    def _format_relationship(self, results: List[SearchResult]) -> Dict[str, Any]:
        """How you know someone - the story"""
        result = results[0]
        conn = result.connection
        
        body = f"**{conn.full_name}**\n"
        
        # Relationship context
        body += f"\n**How you know them:** {conn.relationship_status}"
        
        if conn.personal_notes:
            body += f"\n**Your notes:** {conn.personal_notes}"
        
        if conn.mutual_connections:
            body += f"\n**Mutual connections:** {conn.mutual_connections}"
        
        body += f"\n**Last contact:** {SearchResult._format_last_contact(conn.days_since_contact)}"
        
        return {
            'title': f"Your connection with {conn.full_name}",
            'summary': conn.relationship_status or 'Professional',
            'body': body,
            'context': [],
            'next_steps': []
        }
    
    def _format_insights(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Network overview - patterns and insights"""
        total = len(results)
        
        # Quality distribution
        high_value = sum(1 for r in results if r.connection.ai_rating >= 7)
        inner_circle = sum(1 for r in results if r.connection.relationship_status == 'Inner Circle')
        
        # Engagement patterns
        overdue = sum(1 for r in results if r.connection.days_since_contact > 90)
        recent = sum(1 for r in results if r.connection.days_since_contact <= 30)
        
        body = f"**Network overview:** {total} connections\n"
        body += f"\n**Quality:**"
        body += f"\n• {high_value} high-value connections"
        body += f"\n• {inner_circle} in your inner circle\n"
        body += f"\n**Engagement:**"
        body += f"\n• {recent} contacted recently"
        body += f"\n• {overdue} overdue for reconnection"
        
        # Top connections
        if results:
            body += f"\n\n**Top connections:**"
            for i, r in enumerate(results[:3], 1):
                c = r.connection
                body += f"\n{i}. {c.full_name} – {c.job_title or 'N/A'}"
        
        return {
            'title': "Your network insights",
            'summary': f"{total} connections analyzed",
            'body': body,
            'context': self._build_context(results),
            'next_steps': ["Reconnect with overdue contacts", "Strengthen inner circle"]
        }
    
    def _format_simple_list(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Generic list view - clean and minimal"""
        lines = []
        
        for i, r in enumerate(results[:5], 1):
            c = r.connection
            line = f"**{i}. {c.full_name}**"
            
            if c.job_title and c.company:
                line += f" – {c.job_title} at {c.company}"
            elif c.job_title:
                line += f" – {c.job_title}"
            
            if r.unique_angle:
                line += f"\n   {r.unique_angle}"
            
            lines.append(line)
        
        return {
            'title': f"{len(results)} connection{'' if len(results)==1 else 's'} found",
            'summary': f"Found {len(results)} relevant result{'' if len(results)==1 else 's'}",
            'body': '\n\n'.join(lines),
            'context': self._build_context(results),
            'next_steps': []
        }
    
    def _empty_response(self, query: str) -> Dict[str, Any]:
        """No results found"""
        return {
            'title': "No matches found",
            'summary': f"Couldn't find anyone matching '{query}'",
            'body': "**Try:**\n• Broader search terms\n• Check spelling\n• Different keywords",
            'context': [],
            'next_steps': ["Broaden search", "Add more connections"]
        }
    
    def _build_context(self, results: List[SearchResult]) -> List[str]:
        """Interesting patterns in the results"""
        context = []
        
        # Industry clustering
        industries = [r.connection.industry for r in results if r.connection.industry]
        if industries:
            top_industry = Counter(industries).most_common(1)[0]
            if top_industry[1] > 1:
                context.append(f"Mostly in {top_industry[0]} ({top_industry[1]} people)")
        
        # Relationship strength
        strong = sum(1 for r in results if r.connection.relationship_status in ['Inner Circle', 'Strategic Partner'])
        if strong > 0:
            context.append(f"{strong} strong relationship{'' if strong==1 else 's'}")
        
        # Engagement status
        overdue = sum(1 for r in results if r.connection.days_since_contact > 90)
        if overdue > 0:
            context.append(f"{overdue} overdue for reconnection")
        
        return context[:3]  # Max 3 insights
    
    def _suggest_actions(self, conn: Connection) -> List[str]:
        """What to do next with this person"""
        actions = []
        
        if conn.days_since_contact > 90:
            actions.append("Reconnect soon – it's been a while")
        elif conn.days_since_contact > 30:
            actions.append("Good time for a check-in")
        
        if conn.key_accomplishments:
            actions.append("Congratulate on recent accomplishments")
        
        if conn.mutual_connections:
            actions.append("Reference mutual connections")
        
        if not actions:
            actions.append("Review profile for conversation starters")
        
        return actions[:2]  # Max 2 suggestions


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN SEARCH ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class AISearchEngine:
    """Relationship-first search with personable output"""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[SearchConfig] = None):
        self.config = config or SearchConfig()
        
        # API setup
        token = api_key or self.config.HF_TOKEN
        if not token:
            raise ValueError("HF_TOKEN required (parameter or environment variable)")
        
        self.client = InferenceClient(api_key=token)
        self.processor = SemanticQueryProcessor()
        self.scorer = RelationshipScorer(self.config)
        self.formatter = PersonableFormatter()
        
        # Logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(levelname)s | %(message)s'))
            self.logger.addHandler(handler)
        
        self.logger.info("✨ AISearchEngine v3.0 initialized (Relationship-first)")
    
    def search(self, query: str, connections: List[Connection], 
               user_id: Optional[int] = None) -> Dict[str, Any]:
        """Execute personable search"""
        start = time.time()
        
        # Validation
        if not query or len(query.strip()) < 2:
            return self._error("Query too short")
        if not connections:
            return self._error("No connections to search")
        
        try:
            # 1. UNDERSTAND
            normalized = self.processor.normalize_query(query)
            keywords = list(self.processor.extract_keywords(normalized))
            intent, confidence = self.processor.detect_intent(normalized)
            
            self.logger.info(f"Query: '{query}' → Intent: {intent.value} ({confidence:.0%})")
            
            # 2. FIND & SCORE
            results = []
            for conn in connections:
                score, matched, quality, unique_angle = self.scorer.score_connection(
                    conn, keywords, normalized.lower(), intent
                )
                
                if score < self.config.MIN_RELEVANCE_SCORE:
                    continue
                
                explanation = self._explain_match(matched, quality)
                results.append(SearchResult(
                    conn, score, matched, quality, explanation, unique_angle
                ))
            
            # Sort by relevance
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            results = results[:self.config.MAX_CANDIDATES]
            
            # 3. FORMAT
            formatted = self.formatter.format_response(intent, query, results)
            
            # Package response
            duration = time.time() - start
            self.logger.info(f"✓ {len(results)} results in {duration:.2f}s")
            
            return {
                'query': query,
                'intent': intent.value,
                'confidence': round(confidence, 2),
                'content': formatted,
                'results': [r.to_dict() for r in results[:10]],  # Top 10 detailed
                'meta': {
                    'count': len(results),
                    'time': round(duration, 3)
                }
            }
        
        except Exception as e:
            self.logger.error(f"Search failed: {e}", exc_info=True)
            return self._error("Search error occurred")
    
    def _explain_match(self, matched: List[str], quality: str) -> str:
        """Human-readable match explanation"""
        if quality == 'exact':
            return "Exact match"
        
        if not matched:
            return "General relevance"
        
        # Map field names to readable labels
        readable_map = {
            'name': 'name',
            'personal_context': 'your notes',
            'accomplishments': 'achievements',
            'skills': 'expertise',
            'title': 'role',
            'company': 'company',
            'industry': 'industry',
            'sector': 'sector'
        }
        
        readable = [readable_map.get(f, f) for f in matched[:3]]
        
        if len(readable) == 1:
            return f"Matches in {readable[0]}"
        elif len(readable) == 2:
            return f"Matches in {readable[0]} and {readable[1]}"
        else:
            return f"Matches in {', '.join(readable[:-1])}, and {readable[-1]}"
    
    def _error(self, msg: str) -> Dict[str, Any]:
        """Error response"""
        return {
            'query': '',
            'intent': 'error',
            'confidence': 0,
            'content': {
                'title': 'Error',
                'summary': msg,
                'body': msg,
                'context': [],
                'next_steps': []
            },
            'results': [],
            'meta': {'count': 0, 'time': 0}
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Engine info"""
        return {
            'version': '3.0.0',
            'model': self.config.MODEL,
            'focus': 'Relationship-first, personable output',
            'features': [
                'Unique trait highlighting',
                'Personal context prioritization',
                'Clean minimal formatting',
                'Intent-aware responses',
                'Relationship-centric scoring'
            ]
        }


# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY & EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

def create_search_engine(api_key: Optional[str] = None, **overrides) -> AISearchEngine:
    """Create configured search engine"""
    config = SearchConfig()
    for k, v in overrides.items():
        if hasattr(config, k):
            setattr(config, k, v)
    return AISearchEngine(api_key, config)


__all__ = [
    'AISearchEngine',
    'Connection',
    'SearchResult',
    'QueryIntent',
    'SearchConfig',
    'create_search_engine'
]
__version__ = '3.0.0'