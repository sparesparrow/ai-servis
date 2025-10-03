"""
Intent Classification System for Command Processing
"""
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score
import pickle
import json
from pathlib import Path

from command_models import IntentType, IntentSchema, ParameterSchema, ParameterType

logger = logging.getLogger(__name__)


class IntentClassifier:
    """Advanced intent classification system"""
    
    def __init__(self):
        self.intent_schemas = self._initialize_intent_schemas()
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        self.classifier = MultinomialNB()
        self.pipeline = Pipeline([
            ('vectorizer', self.vectorizer),
            ('classifier', self.classifier)
        ])
        self.is_trained = False
        self.training_data = []
        self.model_path = Path("models/intent_classifier.pkl")
        self.model_path.parent.mkdir(exist_ok=True)
        
        # Load pre-trained model if available
        self._load_model()
    
    def _initialize_intent_schemas(self) -> Dict[IntentType, IntentSchema]:
        """Initialize intent classification schemas"""
        return {
            IntentType.AUDIO_CONTROL: IntentSchema(
                intent=IntentType.AUDIO_CONTROL,
                keywords=[
                    "play", "music", "song", "track", "album", "artist", "band",
                    "volume", "loud", "quiet", "mute", "unmute", "louder", "quieter",
                    "pause", "stop", "resume", "next", "previous", "skip",
                    "headphones", "speakers", "bluetooth", "audio", "sound"
                ],
                parameters=[
                    ParameterSchema(
                        name="action",
                        type=ParameterType.STRING,
                        required=True,
                        choices=["play", "pause", "stop", "volume", "skip", "switch"],
                        description="Audio control action"
                    ),
                    ParameterSchema(
                        name="target",
                        type=ParameterType.STRING,
                        required=False,
                        description="Target (song, artist, device, etc.)"
                    ),
                    ParameterSchema(
                        name="level",
                        type=ParameterType.INTEGER,
                        required=False,
                        min_value=0,
                        max_value=100,
                        description="Volume level (0-100)"
                    ),
                    ParameterSchema(
                        name="device",
                        type=ParameterType.STRING,
                        required=False,
                        choices=["headphones", "speakers", "bluetooth"],
                        description="Audio output device"
                    )
                ],
                service="ai-audio-assistant",
                tool="control_audio",
                description="Audio and music control commands",
                examples=[
                    "play music",
                    "turn up the volume",
                    "pause the song",
                    "switch to headphones",
                    "play jazz music"
                ]
            ),
            
            IntentType.SYSTEM_CONTROL: IntentSchema(
                intent=IntentType.SYSTEM_CONTROL,
                keywords=[
                    "open", "close", "launch", "run", "execute", "start", "stop",
                    "application", "app", "program", "software", "process", "task",
                    "shutdown", "restart", "reboot", "sleep", "hibernate",
                    "file", "folder", "directory", "document"
                ],
                parameters=[
                    ParameterSchema(
                        name="action",
                        type=ParameterType.STRING,
                        required=True,
                        choices=["open", "close", "launch", "run", "start", "stop", "kill"],
                        description="System control action"
                    ),
                    ParameterSchema(
                        name="target",
                        type=ParameterType.STRING,
                        required=True,
                        description="Target application or process"
                    ),
                    ParameterSchema(
                        name="path",
                        type=ParameterType.FILE_PATH,
                        required=False,
                        description="File or directory path"
                    )
                ],
                service="ai-platform-linux",
                tool="execute_command",
                description="System and application control",
                examples=[
                    "open browser",
                    "launch calculator",
                    "close all windows",
                    "run python script"
                ]
            ),
            
            IntentType.SMART_HOME: IntentSchema(
                intent=IntentType.SMART_HOME,
                keywords=[
                    "lights", "light", "lamp", "bulb", "brightness", "dim",
                    "temperature", "thermostat", "heating", "cooling", "ac",
                    "lock", "unlock", "door", "window", "security", "alarm",
                    "camera", "sensor", "motion", "detection"
                ],
                parameters=[
                    ParameterSchema(
                        name="device_type",
                        type=ParameterType.STRING,
                        required=True,
                        choices=["lights", "temperature", "security", "camera"],
                        description="Type of smart home device"
                    ),
                    ParameterSchema(
                        name="action",
                        type=ParameterType.STRING,
                        required=True,
                        choices=["on", "off", "dim", "brighten", "lock", "unlock", "set"],
                        description="Action to perform"
                    ),
                    ParameterSchema(
                        name="location",
                        type=ParameterType.STRING,
                        required=False,
                        description="Room or location"
                    ),
                    ParameterSchema(
                        name="value",
                        type=ParameterType.INTEGER,
                        required=False,
                        description="Value for dimming or temperature"
                    )
                ],
                service="ai-home-automation",
                tool="control_device",
                description="Smart home device control",
                examples=[
                    "turn on the lights",
                    "dim the bedroom lights",
                    "set temperature to 72",
                    "lock the front door"
                ]
            ),
            
            IntentType.COMMUNICATION: IntentSchema(
                intent=IntentType.COMMUNICATION,
                keywords=[
                    "send", "message", "text", "sms", "email", "call", "phone",
                    "whatsapp", "telegram", "slack", "discord", "notify",
                    "contact", "person", "friend", "family"
                ],
                parameters=[
                    ParameterSchema(
                        name="action",
                        type=ParameterType.STRING,
                        required=True,
                        choices=["send", "call", "message", "notify"],
                        description="Communication action"
                    ),
                    ParameterSchema(
                        name="recipient",
                        type=ParameterType.STRING,
                        required=True,
                        description="Recipient name or contact"
                    ),
                    ParameterSchema(
                        name="message",
                        type=ParameterType.STRING,
                        required=False,
                        description="Message content"
                    ),
                    ParameterSchema(
                        name="platform",
                        type=ParameterType.STRING,
                        required=False,
                        choices=["sms", "email", "whatsapp", "telegram"],
                        description="Communication platform"
                    )
                ],
                service="ai-communications",
                tool="send_message",
                description="Communication and messaging",
                examples=[
                    "send message to John",
                    "call mom",
                    "text my friend",
                    "send email to boss"
                ]
            ),
            
            IntentType.NAVIGATION: IntentSchema(
                intent=IntentType.NAVIGATION,
                keywords=[
                    "directions", "navigate", "route", "map", "location", "address",
                    "drive", "walk", "travel", "destination", "gps", "traffic",
                    "distance", "time", "eta", "waypoint"
                ],
                parameters=[
                    ParameterSchema(
                        name="destination",
                        type=ParameterType.STRING,
                        required=True,
                        description="Destination address or location"
                    ),
                    ParameterSchema(
                        name="origin",
                        type=ParameterType.STRING,
                        required=False,
                        description="Starting location"
                    ),
                    ParameterSchema(
                        name="mode",
                        type=ParameterType.STRING,
                        required=False,
                        choices=["driving", "walking", "transit", "cycling"],
                        description="Travel mode"
                    )
                ],
                service="ai-maps-navigation",
                tool="get_directions",
                description="Navigation and directions",
                examples=[
                    "directions to the mall",
                    "how to get to work",
                    "navigate to 123 Main St",
                    "walking directions to park"
                ]
            ),
            
            IntentType.INFORMATION: IntentSchema(
                intent=IntentType.INFORMATION,
                keywords=[
                    "what", "how", "why", "when", "where", "who", "tell", "explain",
                    "define", "describe", "show", "help", "information", "question",
                    "weather", "time", "date", "news", "search", "find"
                ],
                parameters=[
                    ParameterSchema(
                        name="query",
                        type=ParameterType.STRING,
                        required=True,
                        description="Information query"
                    ),
                    ParameterSchema(
                        name="type",
                        type=ParameterType.STRING,
                        required=False,
                        choices=["weather", "time", "news", "general"],
                        description="Type of information"
                    )
                ],
                service="ai-information",
                tool="get_information",
                description="Information and question answering",
                examples=[
                    "what's the weather",
                    "what time is it",
                    "tell me about Python",
                    "how do I cook pasta"
                ]
            ),
            
            IntentType.FILE_OPERATION: IntentSchema(
                intent=IntentType.FILE_OPERATION,
                keywords=[
                    "download", "upload", "copy", "move", "delete", "create", "save",
                    "file", "document", "folder", "directory", "path", "url",
                    "backup", "sync", "share", "export", "import"
                ],
                parameters=[
                    ParameterSchema(
                        name="action",
                        type=ParameterType.STRING,
                        required=True,
                        choices=["download", "upload", "copy", "move", "delete", "create"],
                        description="File operation action"
                    ),
                    ParameterSchema(
                        name="source",
                        type=ParameterType.STRING,
                        required=False,
                        description="Source file or URL"
                    ),
                    ParameterSchema(
                        name="destination",
                        type=ParameterType.STRING,
                        required=False,
                        description="Destination path"
                    )
                ],
                service="file-manager",
                tool="file_operation",
                description="File and document operations",
                examples=[
                    "download file from URL",
                    "copy file to desktop",
                    "delete old documents",
                    "create new folder"
                ]
            ),
            
            IntentType.HARDWARE_CONTROL: IntentSchema(
                intent=IntentType.HARDWARE_CONTROL,
                keywords=[
                    "gpio", "pin", "sensor", "led", "relay", "pwm", "analog", "digital",
                    "hardware", "device", "component", "circuit", "board", "arduino",
                    "raspberry", "pi", "microcontroller"
                ],
                parameters=[
                    ParameterSchema(
                        name="pin",
                        type=ParameterType.INTEGER,
                        required=True,
                        min_value=0,
                        max_value=40,
                        description="GPIO pin number"
                    ),
                    ParameterSchema(
                        name="action",
                        type=ParameterType.STRING,
                        required=True,
                        choices=["on", "off", "toggle", "read", "write", "pwm"],
                        description="Hardware action"
                    ),
                    ParameterSchema(
                        name="value",
                        type=ParameterType.INTEGER,
                        required=False,
                        min_value=0,
                        max_value=255,
                        description="Value for PWM or analog write"
                    )
                ],
                service="hardware-bridge",
                tool="control_hardware",
                description="Hardware and GPIO control",
                examples=[
                    "turn on LED on pin 13",
                    "read sensor on pin 2",
                    "set PWM on pin 9 to 128",
                    "toggle relay on pin 5"
                ]
            )
        }
    
    async def classify_intent(self, text: str, context: Dict[str, Any]) -> Tuple[IntentType, float, List[Tuple[str, float]]]:
        """Classify command intent with confidence score and alternatives"""
        start_time = datetime.now()
        
        try:
            # Preprocess text
            processed_text = self._preprocess_text(text)
            
            # Use multiple classification methods
            results = []
            
            # Method 1: Keyword-based classification
            keyword_result = self._classify_by_keywords(processed_text, context)
            results.append(keyword_result)
            
            # Method 2: Machine learning classification (if trained)
            if self.is_trained:
                ml_result = self._classify_by_ml(processed_text)
                results.append(ml_result)
            
            # Method 3: Pattern-based classification
            pattern_result = self._classify_by_patterns(processed_text, context)
            results.append(pattern_result)
            
            # Combine results
            final_intent, confidence, alternatives = self._combine_classification_results(results)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.debug(f"Intent classification completed in {processing_time:.3f}s: {final_intent} (confidence: {confidence:.2f})")
            
            return final_intent, confidence, alternatives
            
        except Exception as e:
            logger.error(f"Error in intent classification: {e}")
            return IntentType.UNKNOWN, 0.0, []
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for classification"""
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s@#%&*+-=<>/\\]', '', text)
        
        return text
    
    def _classify_by_keywords(self, text: str, context: Dict[str, Any]) -> Tuple[IntentType, float]:
        """Classify intent using keyword matching"""
        intent_scores = {}
        
        for intent_type, schema in self.intent_schemas.items():
            score = 0
            keywords = schema.keywords
            
            # Count keyword matches
            for keyword in keywords:
                if keyword in text:
                    score += 1
            
            # Normalize score
            if keywords:
                score = score / len(keywords)
            
            if score > 0:
                intent_scores[intent_type] = score
        
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent]
            return best_intent, confidence
        
        return IntentType.UNKNOWN, 0.0
    
    def _classify_by_ml(self, text: str) -> Tuple[IntentType, float]:
        """Classify intent using machine learning"""
        try:
            # Predict using trained model
            prediction = self.pipeline.predict([text])[0]
            probabilities = self.pipeline.predict_proba([text])[0]
            
            # Get confidence score
            confidence = max(probabilities)
            
            # Convert prediction to IntentType
            intent_type = IntentType(prediction)
            
            return intent_type, confidence
            
        except Exception as e:
            logger.error(f"Error in ML classification: {e}")
            return IntentType.UNKNOWN, 0.0
    
    def _classify_by_patterns(self, text: str, context: Dict[str, Any]) -> Tuple[IntentType, float]:
        """Classify intent using pattern matching"""
        patterns = {
            IntentType.AUDIO_CONTROL: [
                r'\b(play|pause|stop|volume|mute|unmute)\b',
                r'\b(music|song|track|audio|sound)\b',
                r'\b(headphones|speakers|bluetooth)\b'
            ],
            IntentType.SYSTEM_CONTROL: [
                r'\b(open|close|launch|run|start|stop|kill)\b',
                r'\b(application|app|program|software)\b',
                r'\b(shutdown|restart|reboot)\b'
            ],
            IntentType.SMART_HOME: [
                r'\b(lights?|lamp|bulb|brightness|dim)\b',
                r'\b(temperature|thermostat|heating|cooling)\b',
                r'\b(lock|unlock|door|window|security)\b'
            ],
            IntentType.COMMUNICATION: [
                r'\b(send|message|text|call|phone|email)\b',
                r'\b(whatsapp|telegram|slack|discord)\b',
                r'\b(contact|person|friend|family)\b'
            ],
            IntentType.NAVIGATION: [
                r'\b(directions?|navigate|route|map|location)\b',
                r'\b(drive|walk|travel|destination|gps)\b',
                r'\b(distance|time|eta|waypoint)\b'
            ],
            IntentType.INFORMATION: [
                r'\b(what|how|why|when|where|who|tell|explain)\b',
                r'\b(weather|time|date|news|search|find)\b',
                r'\b(help|information|question)\b'
            ],
            IntentType.FILE_OPERATION: [
                r'\b(download|upload|copy|move|delete|create|save)\b',
                r'\b(file|document|folder|directory|path|url)\b',
                r'\b(backup|sync|share|export|import)\b'
            ],
            IntentType.HARDWARE_CONTROL: [
                r'\b(gpio|pin|sensor|led|relay|pwm|analog|digital)\b',
                r'\b(hardware|device|component|circuit|board)\b',
                r'\b(arduino|raspberry|pi|microcontroller)\b'
            ]
        }
        
        intent_scores = {}
        
        for intent_type, pattern_list in patterns.items():
            score = 0
            for pattern in pattern_list:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches
            
            if score > 0:
                intent_scores[intent_type] = score / len(pattern_list)
        
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = min(intent_scores[best_intent], 1.0)
            return best_intent, confidence
        
        return IntentType.UNKNOWN, 0.0
    
    def _combine_classification_results(self, results: List[Tuple[IntentType, float]]) -> Tuple[IntentType, float, List[Tuple[str, float]]]:
        """Combine multiple classification results"""
        if not results:
            return IntentType.UNKNOWN, 0.0, []
        
        # Weight different methods
        weights = [0.4, 0.4, 0.2]  # keyword, ml, pattern
        
        combined_scores = {}
        
        for i, (intent, score) in enumerate(results):
            if i < len(weights):
                weight = weights[i]
                if intent in combined_scores:
                    combined_scores[intent] += score * weight
                else:
                    combined_scores[intent] = score * weight
        
        if combined_scores:
            # Sort by score
            sorted_intents = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
            
            best_intent, best_score = sorted_intents[0]
            alternatives = [(intent.value, score) for intent, score in sorted_intents[1:4]]
            
            return best_intent, best_score, alternatives
        
        return IntentType.UNKNOWN, 0.0, []
    
    async def extract_parameters(self, text: str, intent: IntentType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters from command text"""
        try:
            schema = self.intent_schemas.get(intent)
            if not schema:
                return {}
            
            parameters = {}
            
            # Extract parameters based on intent type
            if intent == IntentType.AUDIO_CONTROL:
                parameters = self._extract_audio_parameters(text)
            elif intent == IntentType.SYSTEM_CONTROL:
                parameters = self._extract_system_parameters(text)
            elif intent == IntentType.SMART_HOME:
                parameters = self._extract_smart_home_parameters(text)
            elif intent == IntentType.COMMUNICATION:
                parameters = self._extract_communication_parameters(text)
            elif intent == IntentType.NAVIGATION:
                parameters = self._extract_navigation_parameters(text)
            elif intent == IntentType.INFORMATION:
                parameters = self._extract_information_parameters(text)
            elif intent == IntentType.FILE_OPERATION:
                parameters = self._extract_file_parameters(text)
            elif intent == IntentType.HARDWARE_CONTROL:
                parameters = self._extract_hardware_parameters(text)
            
            return parameters
            
        except Exception as e:
            logger.error(f"Error extracting parameters: {e}")
            return {}
    
    def _extract_audio_parameters(self, text: str) -> Dict[str, Any]:
        """Extract audio control parameters"""
        parameters = {}
        
        # Action extraction
        actions = {
            "play": ["play", "start", "begin"],
            "pause": ["pause", "hold"],
            "stop": ["stop", "end", "quit"],
            "volume": ["volume", "loud", "quiet", "mute", "unmute"],
            "skip": ["skip", "next", "previous"],
            "switch": ["switch", "change", "output"]
        }
        
        for action, keywords in actions.items():
            if any(keyword in text for keyword in keywords):
                parameters["action"] = action
                break
        
        # Volume level extraction
        volume_match = re.search(r'(\d+)', text)
        if volume_match:
            level = int(volume_match.group(1))
            if 0 <= level <= 100:
                parameters["level"] = level
        
        # Device extraction
        devices = ["headphones", "speakers", "bluetooth"]
        for device in devices:
            if device in text:
                parameters["device"] = device
                break
        
        # Target extraction (artist, song, etc.)
        if "by" in text:
            by_match = re.search(r'by\s+([^,\n]+)', text)
            if by_match:
                parameters["target"] = by_match.group(1).strip()
        
        return parameters
    
    def _extract_system_parameters(self, text: str) -> Dict[str, Any]:
        """Extract system control parameters"""
        parameters = {}
        
        # Action extraction
        actions = ["open", "close", "launch", "run", "start", "stop", "kill"]
        for action in actions:
            if action in text:
                parameters["action"] = action
                break
        
        # Target extraction
        words = text.split()
        for i, word in enumerate(words):
            if word in actions and i + 1 < len(words):
                target = " ".join(words[i + 1:])
                parameters["target"] = target
                break
        
        return parameters
    
    def _extract_smart_home_parameters(self, text: str) -> Dict[str, Any]:
        """Extract smart home parameters"""
        parameters = {}
        
        # Device type extraction
        if "light" in text:
            parameters["device_type"] = "lights"
        elif "temperature" in text or "thermostat" in text:
            parameters["device_type"] = "temperature"
        elif "lock" in text or "door" in text:
            parameters["device_type"] = "security"
        elif "camera" in text:
            parameters["device_type"] = "camera"
        
        # Action extraction
        actions = ["on", "off", "dim", "brighten", "lock", "unlock", "set"]
        for action in actions:
            if action in text:
                parameters["action"] = action
                break
        
        # Location extraction
        locations = ["bedroom", "kitchen", "living room", "bathroom", "office", "garage"]
        for location in locations:
            if location in text:
                parameters["location"] = location
                break
        
        # Value extraction
        value_match = re.search(r'(\d+)', text)
        if value_match:
            parameters["value"] = int(value_match.group(1))
        
        return parameters
    
    def _extract_communication_parameters(self, text: str) -> Dict[str, Any]:
        """Extract communication parameters"""
        parameters = {}
        
        # Action extraction
        actions = ["send", "call", "message", "notify"]
        for action in actions:
            if action in text:
                parameters["action"] = action
                break
        
        # Platform extraction
        platforms = ["sms", "email", "whatsapp", "telegram", "slack"]
        for platform in platforms:
            if platform in text:
                parameters["platform"] = platform
                break
        
        # Recipient extraction (simplified)
        if "to" in text:
            to_match = re.search(r'to\s+([^,\n]+)', text)
            if to_match:
                parameters["recipient"] = to_match.group(1).strip()
        
        return parameters
    
    def _extract_navigation_parameters(self, text: str) -> Dict[str, Any]:
        """Extract navigation parameters"""
        parameters = {}
        
        # Destination extraction
        if "to" in text:
            to_match = re.search(r'to\s+([^,\n]+)', text)
            if to_match:
                parameters["destination"] = to_match.group(1).strip()
        
        # Mode extraction
        modes = ["driving", "walking", "transit", "cycling"]
        for mode in modes:
            if mode in text:
                parameters["mode"] = mode
                break
        
        return parameters
    
    def _extract_information_parameters(self, text: str) -> Dict[str, Any]:
        """Extract information parameters"""
        parameters = {}
        
        # Query extraction (simplified)
        parameters["query"] = text
        
        # Type extraction
        if "weather" in text:
            parameters["type"] = "weather"
        elif "time" in text:
            parameters["type"] = "time"
        elif "news" in text:
            parameters["type"] = "news"
        else:
            parameters["type"] = "general"
        
        return parameters
    
    def _extract_file_parameters(self, text: str) -> Dict[str, Any]:
        """Extract file operation parameters"""
        parameters = {}
        
        # Action extraction
        actions = ["download", "upload", "copy", "move", "delete", "create"]
        for action in actions:
            if action in text:
                parameters["action"] = action
                break
        
        # URL extraction
        url_match = re.search(r'https?://[^\s]+', text)
        if url_match:
            parameters["source"] = url_match.group(0)
        
        # Path extraction
        path_match = re.search(r'[/\\][\w\s/\\.-]+', text)
        if path_match:
            parameters["destination"] = path_match.group(0)
        
        return parameters
    
    def _extract_hardware_parameters(self, text: str) -> Dict[str, Any]:
        """Extract hardware control parameters"""
        parameters = {}
        
        # Pin extraction
        pin_match = re.search(r'pin\s*(\d+)|gpio\s*(\d+)', text)
        if pin_match:
            pin_num = pin_match.group(1) or pin_match.group(2)
            parameters["pin"] = int(pin_num)
        
        # Action extraction
        actions = ["on", "off", "toggle", "read", "write", "pwm"]
        for action in actions:
            if action in text:
                parameters["action"] = action
                break
        
        # Value extraction
        value_match = re.search(r'to\s+(\d+)|value\s+(\d+)|(\d+)%', text)
        if value_match:
            value = value_match.group(1) or value_match.group(2) or value_match.group(3)
            parameters["value"] = int(value)
        
        return parameters
    
    def train_model(self, training_data: List[Tuple[str, str]]):
        """Train the machine learning model"""
        try:
            if not training_data:
                logger.warning("No training data provided")
                return
            
            texts, labels = zip(*training_data)
            
            # Train the pipeline
            self.pipeline.fit(texts, labels)
            self.is_trained = True
            
            # Save the model
            self._save_model()
            
            logger.info(f"Model trained with {len(training_data)} examples")
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
    
    def _save_model(self):
        """Save trained model to disk"""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.pipeline, f)
            logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def _load_model(self):
        """Load trained model from disk"""
        try:
            if self.model_path.exists():
                with open(self.model_path, 'rb') as f:
                    self.pipeline = pickle.load(f)
                self.is_trained = True
                logger.info(f"Model loaded from {self.model_path}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
    
    def get_intent_schema(self, intent: IntentType) -> Optional[IntentSchema]:
        """Get schema for specific intent"""
        return self.intent_schemas.get(intent)
    
    def get_all_schemas(self) -> Dict[IntentType, IntentSchema]:
        """Get all intent schemas"""
        return self.intent_schemas.copy()
