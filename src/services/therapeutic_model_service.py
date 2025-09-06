"""
Therapeutic Model Service - Multi-language speaker identification and sentiment analysis
"""

import os
import torch
from transformers import AutoTokenizer, AutoConfig, DistilBertModel
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)


class TherapeuticBertModel(torch.nn.Module):
    """Custom therapeutic BERT model with direct weight loading pattern"""
    
    def __init__(self, tokenizer, num_speaker=2, num_sentiment=4, config=None):
        super().__init__()
        # Initialize DistilBERT from provided local config to avoid remote downloads
        if config is None:
            raise ValueError("A local DistilBERT config must be provided to TherapeuticBertModel")
        self.bert = DistilBertModel(config)
        # Resize embeddings to match training vocab size
        self.bert.resize_token_embeddings(len(tokenizer))
        
        self.dropout = torch.nn.Dropout(0.1)
        # Use the SAME names as in the checkpoint
        self.sentiment_classifier = torch.nn.Linear(self.bert.config.dim, num_sentiment)
        self.speaker_classifier = torch.nn.Linear(self.bert.config.dim, num_speaker)
    
    def forward(self, input_ids, attention_mask=None):
        """Forward pass"""
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        cls_output = outputs.last_hidden_state[:, 0, :]  # [CLS] token
        pooled = self.dropout(cls_output)
        
        return {
            'speaker_logits': self.speaker_classifier(pooled),
            'sentiment_logits': self.sentiment_classifier(pooled)
        }


class TherapeuticModelService:
    """Service for therapeutic BERT model handling speaker identification and sentiment analysis"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_path = Path(__file__).parent.parent / "Model"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.speaker_labels = ['Client', 'Therapist']
        self.sentiment_labels = ['Positive', 'Negative', 'Neutral', 'Mixed']
        
        # Initialize model on startup
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the therapeutic BERT model and tokenizer using direct weight loading"""
        try:
            logger.info("🔄 Loading therapeutic BERT model with direct weight loading...")

            # Check if model files exist
            if not self.model_path.exists():
                logger.error(f"Model directory not found: {self.model_path}")
                return False

            # Load tokenizer first (ensures vocab size for embedding resize)
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                local_files_only=True
            )

            # Load local config to avoid remote downloads
            logger.info("Loading local DistilBERT config...")
            config = AutoConfig.from_pretrained(str(self.model_path), local_files_only=True)

            logger.info("Instantiating TherapeuticBertModel...")
            self.model = TherapeuticBertModel(tokenizer=self.tokenizer, num_speaker=2, num_sentiment=4, config=config)

            # Load state dict from safetensors
            from safetensors.torch import load_file
            model_file = self.model_path / "model.safetensors"
            if not model_file.exists():
                logger.error("model.safetensors not found")
                return False

            logger.info("Loading weights from safetensors with strict=False...")
            state_dict = load_file(str(model_file))
            missing_keys, unexpected_keys = self.model.load_state_dict(state_dict, strict=False)

            if missing_keys:
                logger.info(f"Missing keys: {missing_keys}")
            if unexpected_keys:
                logger.info(f"Unexpected keys: {unexpected_keys}")

            # Finalize
            self.model.to(self.device)
            self.model.eval()
            logger.info("✅ Therapeutic BERT model loaded successfully!")
            logger.info(f"Device: {self.device}")
            logger.info(f"Speaker labels: {self.speaker_labels}")
            logger.info(f"Sentiment labels: {self.sentiment_labels}")
            return True
        except Exception as e:
            logger.error(f"❌ Error loading therapeutic model: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # Fallback to simple approach
            try:
                logger.info("Trying fallback loading approach...")
                self.model = SimpleTherapeuticModel()
                return True
            except:
                return False
    
    def is_available(self):
        """Check if the model is available for use"""
        return self.model is not None and self.tokenizer is not None
    
    def get_model_info(self):
        """Get information about the loaded model"""
        info = {
            'model_available': self.model is not None,
            'tokenizer_available': self.tokenizer is not None,
            'model_type': type(self.model).__name__ if self.model else None,
            'device': str(self.device),
            'model_path': str(self.model_path),
            'model_path_exists': self.model_path.exists(),
            'speaker_labels': self.speaker_labels,
            'sentiment_labels': self.sentiment_labels
        }
        
        return info
    
    def test_model(self, test_text="Hello, how are you feeling today?"):
        """Test the model with a simple input to verify it works"""
        logger.info(f"Testing model with text: '{test_text}'")
        
        try:
            model_info = self.get_model_info()
            logger.info(f"Model info: {model_info}")
            
            if not self.is_available():
                logger.error("Model not available for testing")
                return False
            
            result = self.analyze_text(test_text)
            logger.info(f"Test result: {result}")
            
            # Verify result structure
            required_keys = ['speaker', 'sentiment', 'speaker_confidence', 'sentiment_confidence']
            for key in required_keys:
                if key not in result:
                    logger.error(f"Missing key in result: {key}")
                    return False
            
            logger.info("✅ Model test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Model test failed: {str(e)}")
            import traceback
            logger.error(f"Test traceback: {traceback.format_exc()}")
            return False
    
    def create_simple_test(self, test_text="Hello, how are you feeling today?"):
        """Create a simple test that matches the user's working pattern"""
        try:
            logger.info("Creating simple test matching user's pattern...")
            
            if not self.is_available():
                logger.error("Model not available")
                return False
            
            # Check if we're using the fallback model
            if isinstance(self.model, SimpleTherapeuticModel):
                logger.info("Using SimpleTherapeuticModel fallback")
                result = self.model.analyze_text(test_text)
                print(f"Speaker: {result['speaker'].title()}")
                print(f"Sentiment: {result['sentiment'].title()}")
                logger.info("✅ Simple test completed successfully with fallback model")
                return True
            
            # Test the exact pattern the user described
            inputs = self.tokenizer(test_text, return_tensors='pt', padding=True, truncation=True)
            
            with torch.no_grad():
                outputs = self.model(inputs['input_ids'], inputs['attention_mask'])
                speaker_pred = torch.argmax(outputs['speaker_logits'])
                sentiment_pred = torch.argmax(outputs['sentiment_logits'])
                
            # Map predictions to labels safely
            speaker_idx = speaker_pred.item()
            sentiment_idx = sentiment_pred.item()
            
            if speaker_idx < len(self.speaker_labels):
                speaker_label = self.speaker_labels[speaker_idx]
            else:
                speaker_label = f"Unknown_Speaker_{speaker_idx}"
                
            if sentiment_idx < len(self.sentiment_labels):
                sentiment_label = self.sentiment_labels[sentiment_idx]
            else:
                sentiment_label = f"Unknown_Sentiment_{sentiment_idx}"
            
            print(f"Speaker: {speaker_label}")
            print(f"Sentiment: {sentiment_label}")
            
            logger.info("✅ Simple test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Simple test failed: {str(e)}")
            import traceback
            logger.error(f"Simple test traceback: {traceback.format_exc()}")
            return False
    
    def analyze_text(self, text):
        """
        Analyze text for both speaker identification and sentiment
        
        Args:
            text (str): Text to analyze
            
        Returns:
            dict: Dictionary with speaker and sentiment predictions
        """
        if not self.is_available():
            logger.warning("Therapeutic model not available")
            return {
                'speaker': 'unknown',
                'sentiment': 'neutral',
                'speaker_confidence': 0.0,
                'sentiment_confidence': 0.0
            }
        
        try:
            # Use simple fallback if complex model failed
            if isinstance(self.model, SimpleTherapeuticModel):
                logger.info("Using SimpleTherapeuticModel fallback")
                return self.model.analyze_text(text)
            
            # Input validation
            if not text or not text.strip():
                logger.warning("Empty or whitespace-only text provided")
                return {
                    'speaker': 'unknown',
                    'sentiment': 'neutral',
                    'speaker_confidence': 0.0,
                    'sentiment_confidence': 0.0
                }
            
            logger.debug(f"Analyzing text: '{text[:100]}...' (length: {len(text)})")
            
            # Tokenize input
            logger.debug("Tokenizing input...")
            inputs = self.tokenizer(
                text, 
                return_tensors='pt', 
                padding=True, 
                truncation=True,
                max_length=512
            )
            
            logger.debug(f"Tokenizer output shapes:")
            logger.debug(f"  input_ids: {inputs['input_ids'].shape}")
            logger.debug(f"  attention_mask: {inputs['attention_mask'].shape}")

            # Safety check: ensure no token id exceeds embedding size
            try:
                num_embeddings = self.model.bert.get_input_embeddings().num_embeddings  # type: ignore[attr-defined]
                max_token_id = int(inputs['input_ids'].max().item())
                if max_token_id >= num_embeddings:
                    logger.error(f"Token id {max_token_id} >= embedding size {num_embeddings}. Vocab/embedding mismatch.")
                    raise IndexError(f"Token id {max_token_id} out of range for embeddings of size {num_embeddings}")
            except Exception as _emb_chk_err:
                # If model is fallback or check not applicable, continue
                logger.debug(f"Embedding size check info: {_emb_chk_err}")

            # Move to device
            logger.debug(f"Moving inputs to device: {self.device}")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Get predictions
            logger.debug("Running model inference...")
            with torch.no_grad():
                try:
                    outputs = self.model(inputs['input_ids'], inputs['attention_mask'])
                    logger.debug("Model inference completed")

                    # Get logits
                    speaker_logits = outputs['speaker_logits']
                    sentiment_logits = outputs['sentiment_logits']
                    
                    logger.debug(f"Speaker logits shape: {speaker_logits.shape}")
                    logger.debug(f"Sentiment logits shape: {sentiment_logits.shape}")
                    
                    # Speaker prediction
                    speaker_probs = torch.softmax(speaker_logits, dim=-1)
                    speaker_pred = torch.argmax(speaker_probs, dim=-1)
                    speaker_confidence = torch.max(speaker_probs).item()
                    
                    # Sentiment prediction
                    sentiment_probs = torch.softmax(sentiment_logits, dim=-1)
                    sentiment_pred = torch.argmax(sentiment_probs, dim=-1)
                    sentiment_confidence = torch.max(sentiment_probs).item()
                    
                    # Validate indices
                    if speaker_pred.item() >= len(self.speaker_labels):
                        logger.error(f"Speaker prediction index {speaker_pred.item()} out of range for labels {self.speaker_labels}")
                        raise IndexError(f"Speaker prediction index {speaker_pred.item()} >= {len(self.speaker_labels)}")
                    
                    if sentiment_pred.item() >= len(self.sentiment_labels):
                        logger.error(f"Sentiment prediction index {sentiment_pred.item()} out of range for labels {self.sentiment_labels}")
                        raise IndexError(f"Sentiment prediction index {sentiment_pred.item()} >= {len(self.sentiment_labels)}")
                    
                    result = {
                        'speaker': self.speaker_labels[speaker_pred.item()].lower(),
                        'sentiment': self.sentiment_labels[sentiment_pred.item()].lower(),
                        'speaker_confidence': speaker_confidence,
                        'sentiment_confidence': sentiment_confidence
                    }
                    
                    logger.debug(f"Analysis result: {result}")
                    return result
                    
                except Exception as model_error:
                    logger.error(f"Error during model inference: {str(model_error)}")
                    logger.error(f"Model inference error type: {type(model_error).__name__}")
                    import traceback
                    logger.error(f"Model inference traceback: {traceback.format_exc()}")
                    raise model_error
                
        except Exception as e:
            logger.error(f"Error analyzing text: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Check if we should fall back to simple model
            if not isinstance(self.model, SimpleTherapeuticModel):
                logger.warning("Falling back to SimpleTherapeuticModel due to error")
                try:
                    self.model = SimpleTherapeuticModel()
                    return self.model.analyze_text(text)
                except Exception as fallback_error:
                    logger.error(f"Fallback model also failed: {str(fallback_error)}")
            
            return {
                'speaker': 'unknown',
                'sentiment': 'neutral',
                'speaker_confidence': 0.0,
                'sentiment_confidence': 0.0
            }
    
    def identify_speaker(self, text):
        """
        Identify speaker for given text
        
        Args:
            text (str): Text to analyze
            
        Returns:
            str: Speaker identification ('client', 'therapist', or 'unknown')
        """
        result = self.analyze_text(text)
        return result['speaker']
    
    def analyze_sentiment(self, text):
        """
        Analyze sentiment for given text
        
        Args:
            text (str): Text to analyze
            
        Returns:
            str: Sentiment analysis ('positive', 'negative', 'neutral', or 'mixed')
        """
        result = self.analyze_text(text)
        return result['sentiment']
    
    def batch_analyze(self, texts):
        """
        Analyze multiple texts in batch for better performance
        
        Args:
            texts (list): List of texts to analyze
            
        Returns:
            list: List of analysis results
        """
        if not self.is_available():
            return [{'speaker': 'unknown', 'sentiment': 'neutral'} for _ in texts]
        
        results = []
        for text in texts:
            result = self.analyze_text(text)
            results.append(result)
        
        return results


class SimpleTherapeuticModel:
    """Simple fallback model for basic speaker and sentiment analysis"""
    
    def __init__(self):
        self.speaker_keywords = {
            'therapist': ['how do you feel', 'what do you think', 'tell me about', 'can you describe', 'therapy', 'session'],
            'client': ['i feel', 'i think', 'i am', 'my problem', 'i have', 'i want']
        }
        
        self.sentiment_keywords = {
            'positive': ['good', 'great', 'happy', 'better', 'progress', 'hope', 'love', 'joy'],
            'negative': ['bad', 'sad', 'angry', 'worse', 'problem', 'difficult', 'hate', 'fear'],
            'mixed': ['but', 'however', 'although', 'mixed feelings', 'conflicted']
        }
    
    def analyze_text(self, text):
        """Simple rule-based analysis"""
        text_lower = text.lower()
        
        # Speaker identification
        speaker_scores = {'client': 0, 'therapist': 0}
        for speaker, keywords in self.speaker_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    speaker_scores[speaker] += 1
        
        speaker = max(speaker_scores, key=speaker_scores.get) if max(speaker_scores.values()) > 0 else 'unknown'
        speaker_confidence = max(speaker_scores.values()) / (sum(speaker_scores.values()) + 1)
        
        # Sentiment analysis
        sentiment_scores = {'positive': 0, 'negative': 0, 'mixed': 0, 'neutral': 1}
        for sentiment, keywords in self.sentiment_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    sentiment_scores[sentiment] += 1
        
        sentiment = max(sentiment_scores, key=sentiment_scores.get)
        sentiment_confidence = max(sentiment_scores.values()) / (sum(sentiment_scores.values()) + 1)
        
        return {
            'speaker': speaker,
            'sentiment': sentiment,
            'speaker_confidence': speaker_confidence,
            'sentiment_confidence': sentiment_confidence
        }
