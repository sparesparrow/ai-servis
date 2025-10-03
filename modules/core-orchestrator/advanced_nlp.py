"""
Advanced NLP Processor for AI-SERVIS Core Orchestrator
Uses modern NLP libraries for enhanced intent recognition and context understanding
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np
from datetime import datetime

# Optional imports for advanced NLP features
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import WordNetLemmatizer
    from nltk.chunk import ne_chunk
    from nltk.tag import pos_tag
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class AdvancedIntentResult:
    """Advanced intent recognition result"""
    intent: str
    confidence: float
    parameters: Dict[str, Any]
    original_text: str
    entities: List[Dict[str, Any]] = None
    sentiment: str = "neutral"
    sentiment_score: float = 0.0
    context_used: bool = False
    alternatives: List[Tuple[str, float]] = None
    processing_time: float = 0.0
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = []
        if self.alternatives is None:
            self.alternatives = []


class AdvancedNLPProcessor:
    """Advanced NLP processor with multiple backends"""
    
    def __init__(self):
        self.intent_patterns = self._initialize_advanced_patterns()
        self.entity_patterns = self._initialize_entity_patterns()
        self.sentiment_patterns = self._initialize_sentiment_patterns()
        
        # Initialize NLP backends
        self._init_nltk()
        self._init_spacy()
        self._init_sklearn()
        
        # Intent classification model
        self.intent_classifier = None
        self.vectorizer = None
        self._train_intent_classifier()
    
    def _init_nltk(self):
        """Initialize NLTK components"""
        if not NLTK_AVAILABLE:
            logger.warning("NLTK not available, using fallback processing")
            return
        
        try:
            # Download required NLTK data
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            nltk.download('maxent_ne_chunker', quiet=True)
            nltk.download('words', quiet=True)
            
            self.stop_words = set(stopwords.words('english'))
            self.lemmatizer = WordNetLemmatizer()
            self.nltk_available = True
            logger.info("NLTK initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize NLTK: {e}")
            self.nltk_available = False
    
    def _init_spacy(self):
        """Initialize spaCy components"""
        if not SPACY_AVAILABLE:
            logger.warning("spaCy not available, using fallback processing")
            return
        
        try:
            # Try to load English model
            self.nlp = spacy.load("en_core_web_sm")
            self.spacy_available = True
            logger.info("spaCy initialized successfully")
        except OSError:
            logger.warning("spaCy English model not found, using fallback")
            self.spacy_available = False
        except Exception as e:
            logger.error(f"Failed to initialize spaCy: {e}")
            self.spacy_available = False
    
    def _init_sklearn(self):
        """Initialize scikit-learn components"""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, using fallback processing")
            return
        
        try:
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            self.sklearn_available = True
            logger.info("scikit-learn initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize scikit-learn: {e}")
            self.sklearn_available = False
    
    def _initialize_advanced_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize advanced intent patterns with weights and context"""
        return {
            "play_music": {
                "keywords": [
                    "play", "music", "song", "track", "album", "artist", "band",
                    "spotify", "youtube", "stream", "listen", "audio", "sound"
                ],
                "weight": 1.0,
                "requires_context": False,
                "context_boost": {
                    "last_intent": ["control_volume", "switch_audio"],
                    "boost": 0.3,
                },
                "entity_types": ["PERSON", "ORG", "WORK_OF_ART"],
                "sentiment_boost": {"positive": 0.2}
            },
            "control_volume": {
                "keywords": [
                    "volume", "loud", "quiet", "mute", "unmute", "louder", "quieter",
                    "sound", "audio", "level", "up", "down", "max", "min"
                ],
                "weight": 1.0,
                "requires_context": False,
                "context_boost": {"last_intent": ["play_music"], "boost": 0.2},
                "entity_types": ["CARDINAL", "PERCENT"],
                "sentiment_boost": {"neutral": 0.1}
            },
            "switch_audio": {
                "keywords": [
                    "switch", "change", "output", "headphones", "speakers", "bluetooth",
                    "rtsp", "device", "audio", "sound", "connect", "disconnect"
                ],
                "weight": 1.0,
                "requires_context": False,
                "context_boost": {
                    "last_intent": ["play_music", "control_volume"],
                    "boost": 0.2,
                },
                "entity_types": ["PRODUCT", "ORG"],
                "sentiment_boost": {"neutral": 0.1}
            },
            "system_control": {
                "keywords": [
                    "open", "close", "launch", "run", "execute", "kill", "start", "stop",
                    "application", "app", "program", "software", "process", "task"
                ],
                "weight": 1.0,
                "requires_context": False,
                "entity_types": ["PRODUCT", "ORG"],
                "sentiment_boost": {"neutral": 0.1}
            },
            "file_operation": {
                "keywords": [
                    "download", "upload", "copy", "move", "delete", "create", "save",
                    "file", "document", "folder", "directory", "path", "url"
                ],
                "weight": 1.0,
                "requires_context": False,
                "entity_types": ["URL", "PATH"],
                "sentiment_boost": {"neutral": 0.1}
            },
            "smart_home": {
                "keywords": [
                    "lights", "temperature", "thermostat", "lock", "unlock", "dim",
                    "brightness", "home", "house", "room", "door", "window", "camera"
                ],
                "weight": 1.0,
                "requires_context": False,
                "context_boost": {"location": ["home", "house"], "boost": 0.3},
                "entity_types": ["LOC", "PRODUCT"],
                "sentiment_boost": {"neutral": 0.1}
            },
            "communication": {
                "keywords": [
                    "send", "call", "message", "text", "email", "whatsapp", "telegram",
                    "notify", "contact", "phone", "sms", "chat"
                ],
                "weight": 1.0,
                "requires_context": False,
                "entity_types": ["PERSON", "ORG", "PHONE"],
                "sentiment_boost": {"positive": 0.1}
            },
            "navigation": {
                "keywords": [
                    "directions", "navigate", "route", "map", "location", "traffic",
                    "gps", "drive", "walk", "travel", "destination", "address"
                ],
                "weight": 1.0,
                "requires_context": False,
                "entity_types": ["LOC", "GPE"],
                "sentiment_boost": {"neutral": 0.1}
            },
            "hardware_control": {
                "keywords": [
                    "gpio", "pin", "sensor", "led", "relay", "pwm", "analog", "digital",
                    "hardware", "device", "component", "circuit", "board"
                ],
                "weight": 1.0,
                "requires_context": False,
                "entity_types": ["CARDINAL", "PRODUCT"],
                "sentiment_boost": {"neutral": 0.1}
            },
            "question_answer": {
                "keywords": [
                    "what", "how", "why", "when", "where", "who", "tell", "explain",
                    "define", "describe", "show", "help", "information"
                ],
                "weight": 0.8,
                "requires_context": False,
                "entity_types": ["PERSON", "ORG", "GPE", "EVENT"],
                "sentiment_boost": {"neutral": 0.2}
            },
            "follow_up": {
                "keywords": [
                    "yes", "no", "continue", "stop", "again", "repeat", "more",
                    "next", "previous", "back", "forward", "that", "this", "it"
                ],
                "weight": 0.5,
                "requires_context": True,
                "entity_types": [],
                "sentiment_boost": {"neutral": 0.3}
            },
        }
    
    def _initialize_entity_patterns(self) -> Dict[str, List[str]]:
        """Initialize entity recognition patterns"""
        return {
            "PERSON": ["artist", "singer", "musician", "composer", "director", "actor"],
            "ORG": ["spotify", "youtube", "apple", "google", "microsoft", "company"],
            "WORK_OF_ART": ["song", "album", "movie", "book", "painting", "sculpture"],
            "LOC": ["home", "office", "kitchen", "bedroom", "living room", "garage"],
            "GPE": ["city", "country", "state", "address", "street", "avenue"],
            "PRODUCT": ["phone", "computer", "speaker", "headphone", "device", "app"],
            "CARDINAL": ["one", "two", "three", "first", "second", "third"],
            "PERCENT": ["percent", "%", "percentage"],
            "PHONE": ["phone", "mobile", "cell", "telephone"],
            "URL": ["http", "https", "www", ".com", ".org", ".net"],
            "PATH": ["/", "\\", "folder", "directory", "file"],
            "EVENT": ["meeting", "appointment", "conference", "party", "event"]
        }
    
    def _initialize_sentiment_patterns(self) -> Dict[str, List[str]]:
        """Initialize sentiment analysis patterns"""
        return {
            "positive": [
                "good", "great", "excellent", "amazing", "wonderful", "fantastic",
                "love", "like", "enjoy", "happy", "pleased", "satisfied"
            ],
            "negative": [
                "bad", "terrible", "awful", "horrible", "hate", "dislike", "angry",
                "frustrated", "annoyed", "disappointed", "sad", "upset"
            ],
            "neutral": [
                "okay", "fine", "normal", "regular", "standard", "average", "medium"
            ]
        }
    
    def _train_intent_classifier(self):
        """Train intent classification model"""
        if not self.sklearn_available:
            return
        
        try:
            # Training data (in a real implementation, this would be much larger)
            training_texts = []
            training_labels = []
            
            for intent, config in self.intent_patterns.items():
                for keyword in config["keywords"]:
                    training_texts.append(keyword)
                    training_labels.append(intent)
            
            if training_texts:
                self.vectorizer.fit(training_texts)
                X = self.vectorizer.transform(training_texts)
                
                self.intent_classifier = MultinomialNB()
                self.intent_classifier.fit(X, training_labels)
                
                logger.info("Intent classifier trained successfully")
        except Exception as e:
            logger.error(f"Failed to train intent classifier: {e}")
    
    async def parse_command_advanced(
        self, text: str, context: Optional[Any] = None
    ) -> AdvancedIntentResult:
        """Advanced command parsing with multiple NLP techniques"""
        start_time = datetime.now()
        
        try:
            # Preprocess text
            processed_text = self._preprocess_text(text)
            
            # Extract entities
            entities = self._extract_entities(processed_text)
            
            # Analyze sentiment
            sentiment, sentiment_score = self._analyze_sentiment(processed_text)
            
            # Classify intent using multiple methods
            intent_scores = {}
            
            # Method 1: Pattern matching
            pattern_scores = self._calculate_pattern_scores(processed_text)
            intent_scores.update(pattern_scores)
            
            # Method 2: Machine learning classification
            if self.intent_classifier and self.vectorizer:
                ml_scores = self._calculate_ml_scores(processed_text)
                # Combine with pattern scores
                for intent, score in ml_scores.items():
                    if intent in intent_scores:
                        intent_scores[intent] = (intent_scores[intent] + score) / 2
                    else:
                        intent_scores[intent] = score
            
            # Method 3: Entity-based scoring
            entity_scores = self._calculate_entity_scores(entities)
            for intent, score in entity_scores.items():
                if intent in intent_scores:
                    intent_scores[intent] += score * 0.3
                else:
                    intent_scores[intent] = score * 0.3
            
            # Method 4: Sentiment-based scoring
            sentiment_scores = self._calculate_sentiment_scores(sentiment)
            for intent, score in sentiment_scores.items():
                if intent in intent_scores:
                    intent_scores[intent] += score * 0.2
                else:
                    intent_scores[intent] = score * 0.2
            
            # Apply context boost if available
            if context:
                context_boost = self._apply_context_boost(intent_scores, context)
                intent_scores.update(context_boost)
            
            # Get best intent
            if not intent_scores:
                best_intent = "unknown"
                best_confidence = 0.0
            else:
                best_intent = max(intent_scores, key=intent_scores.get)
                best_confidence = min(intent_scores[best_intent], 1.0)
            
            # Get alternatives
            alternatives = [
                (intent, score) for intent, score in 
                sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)[1:4]
            ]
            
            # Extract parameters
            parameters = self._extract_advanced_parameters(
                processed_text, best_intent, entities
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AdvancedIntentResult(
                intent=best_intent,
                confidence=best_confidence,
                parameters=parameters,
                original_text=text,
                entities=entities,
                sentiment=sentiment,
                sentiment_score=sentiment_score,
                context_used=context is not None,
                alternatives=alternatives,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error in advanced parsing: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            return AdvancedIntentResult(
                intent="error",
                confidence=0.0,
                parameters={},
                original_text=text,
                processing_time=processing_time
            )
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for analysis"""
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s@#%&*+-=<>/\\]', '', text)
        
        return text
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text"""
        entities = []
        
        # spaCy entity extraction
        if self.spacy_available:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    entities.append({
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "confidence": 0.9  # spaCy doesn't provide confidence scores
                    })
            except Exception as e:
                logger.error(f"spaCy entity extraction failed: {e}")
        
        # NLTK entity extraction
        if self.nltk_available and not entities:
            try:
                tokens = word_tokenize(text)
                pos_tags = pos_tag(tokens)
                chunks = ne_chunk(pos_tags)
                
                for chunk in chunks:
                    if hasattr(chunk, 'label'):
                        entities.append({
                            "text": ' '.join([token for token, pos in chunk.leaves()]),
                            "label": chunk.label(),
                            "start": 0,  # NLTK doesn't provide character positions
                            "end": 0,
                            "confidence": 0.7
                        })
            except Exception as e:
                logger.error(f"NLTK entity extraction failed: {e}")
        
        # Pattern-based entity extraction
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    entities.append({
                        "text": pattern,
                        "label": entity_type,
                        "start": text.find(pattern),
                        "end": text.find(pattern) + len(pattern),
                        "confidence": 0.6
                    })
        
        return entities
    
    def _analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """Analyze sentiment of text"""
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        words = text.split()
        
        for word in words:
            if word in self.sentiment_patterns["positive"]:
                positive_count += 1
            elif word in self.sentiment_patterns["negative"]:
                negative_count += 1
            elif word in self.sentiment_patterns["neutral"]:
                neutral_count += 1
        
        total_sentiment_words = positive_count + negative_count + neutral_count
        
        if total_sentiment_words == 0:
            return "neutral", 0.0
        
        positive_ratio = positive_count / total_sentiment_words
        negative_ratio = negative_count / total_sentiment_words
        neutral_ratio = neutral_count / total_sentiment_words
        
        if positive_ratio > negative_ratio and positive_ratio > neutral_ratio:
            return "positive", positive_ratio
        elif negative_ratio > positive_ratio and negative_ratio > neutral_ratio:
            return "negative", negative_ratio
        else:
            return "neutral", neutral_ratio
    
    def _calculate_pattern_scores(self, text: str) -> Dict[str, float]:
        """Calculate intent scores using pattern matching"""
        scores = {}
        words = text.split()
        
        for intent, config in self.intent_patterns.items():
            keywords = config["keywords"]
            weight = config["weight"]
            
            # Basic keyword matching
            keyword_score = sum(1 for keyword in keywords if keyword in text)
            
            # Position weighting (earlier words get higher weight)
            position_score = 0
            for i, word in enumerate(words[:5]):  # Check first 5 words
                if word in keywords:
                    position_score += (5 - i) * 0.1
            
            total_score = (keyword_score + position_score) * weight
            if total_score > 0:
                scores[intent] = total_score
        
        return scores
    
    def _calculate_ml_scores(self, text: str) -> Dict[str, float]:
        """Calculate intent scores using machine learning"""
        if not self.intent_classifier or not self.vectorizer:
            return {}
        
        try:
            X = self.vectorizer.transform([text])
            probabilities = self.intent_classifier.predict_proba(X)[0]
            classes = self.intent_classifier.classes_
            
            scores = {}
            for i, intent in enumerate(classes):
                scores[intent] = probabilities[i]
            
            return scores
        except Exception as e:
            logger.error(f"ML scoring failed: {e}")
            return {}
    
    def _calculate_entity_scores(self, entities: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate intent scores based on entities"""
        scores = {}
        
        for entity in entities:
            entity_type = entity["label"]
            for intent, config in self.intent_patterns.items():
                if entity_type in config.get("entity_types", []):
                    if intent not in scores:
                        scores[intent] = 0
                    scores[intent] += 0.5
        
        return scores
    
    def _calculate_sentiment_scores(self, sentiment: str) -> Dict[str, float]:
        """Calculate intent scores based on sentiment"""
        scores = {}
        
        for intent, config in self.intent_patterns.items():
            sentiment_boost = config.get("sentiment_boost", {})
            if sentiment in sentiment_boost:
                scores[intent] = sentiment_boost[sentiment]
        
        return scores
    
    def _apply_context_boost(self, scores: Dict[str, float], context: Any) -> Dict[str, float]:
        """Apply context-based score boost"""
        boosted_scores = {}
        
        for intent, score in scores.items():
            config = self.intent_patterns.get(intent, {})
            context_boost = config.get("context_boost", {})
            
            boost = 0.0
            if "last_intent" in context_boost and hasattr(context, 'last_intent'):
                if context.last_intent in context_boost["last_intent"]:
                    boost += context_boost.get("boost", 0.1)
            
            if "location" in context_boost and hasattr(context, 'variables'):
                user_location = context.variables.get("location", "").lower()
                if any(loc in user_location for loc in context_boost["location"]):
                    boost += context_boost.get("boost", 0.1)
            
            boosted_scores[intent] = score + boost
        
        return boosted_scores
    
    def _extract_advanced_parameters(
        self, text: str, intent: str, entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract parameters using advanced techniques"""
        parameters = {}
        
        # Extract parameters from entities
        for entity in entities:
            entity_type = entity["label"]
            entity_text = entity["text"]
            
            if entity_type == "PERSON":
                parameters["person"] = entity_text
            elif entity_type == "ORG":
                parameters["organization"] = entity_text
            elif entity_type == "LOC":
                parameters["location"] = entity_text
            elif entity_type == "CARDINAL":
                parameters["number"] = entity_text
            elif entity_type == "PERCENT":
                parameters["percentage"] = entity_text
            elif entity_type == "URL":
                parameters["url"] = entity_text
            elif entity_type == "PATH":
                parameters["path"] = entity_text
        
        # Intent-specific parameter extraction
        if intent == "play_music":
            # Extract artist, song, genre
            if "by" in text:
                by_index = text.find("by")
                if by_index != -1:
                    artist_part = text[by_index + 2:].strip()
                    parameters["artist"] = artist_part.split()[0]  # First word after "by"
            
            # Genre detection
            genres = ["jazz", "rock", "classical", "pop", "electronic", "ambient", "folk"]
            for genre in genres:
                if genre in text:
                    parameters["genre"] = genre
                    break
        
        elif intent == "control_volume":
            # Volume level extraction
            numbers = re.findall(r'\b(\d+)\b', text)
            if numbers:
                level = int(numbers[0])
                if 0 <= level <= 100:
                    parameters["level"] = level
            
            # Volume actions
            if any(word in text for word in ["up", "higher", "louder", "increase"]):
                parameters["action"] = "up"
            elif any(word in text for word in ["down", "lower", "quieter", "decrease"]):
                parameters["action"] = "down"
            elif any(word in text for word in ["mute", "silent", "off"]):
                parameters["action"] = "mute"
            elif any(word in text for word in ["unmute", "on"]):
                parameters["action"] = "unmute"
        
        elif intent == "smart_home":
            # Device types
            if "lights" in text or "light" in text:
                parameters["device_type"] = "lights"
            elif "temperature" in text or "thermostat" in text:
                parameters["device_type"] = "temperature"
            elif "lock" in text or "door" in text:
                parameters["device_type"] = "security"
            
            # Actions
            if any(word in text for word in ["on", "turn on", "enable"]):
                parameters["action"] = "on"
            elif any(word in text for word in ["off", "turn off", "disable"]):
                parameters["action"] = "off"
            elif "dim" in text:
                parameters["action"] = "dim"
        
        return parameters
