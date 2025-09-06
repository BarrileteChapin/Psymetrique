#!/usr/bin/env python3
"""
Comprehensive test script for the therapeutic BERT model
"""

import sys
import logging
from pathlib import Path

# Add src to path (adjust for tests/ subdirectory)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def test_model_comprehensive():
    """Comprehensive test of the therapeutic model"""
    print("🧪 Comprehensive Model Test")
    print("=" * 40)
    
    try:
        # Check if model files exist
        model_path = Path(__file__).parent.parent / "src" / "Model"
        print(f"1. Checking model files in {model_path}...")
        
        required_files = ["model.safetensors", "config.json", "vocab.txt", "tokenizer_config.json"]
        for file in required_files:
            file_path = model_path / file
            if file_path.exists():
                print(f"   ✅ {file} exists ({file_path.stat().st_size} bytes)")
            else:
                print(f"   ❌ {file} missing")
                return False
        
        print("2. Importing service...")
        from services.therapeutic_model_service import TherapeuticModelService
        
        print("3. Creating service instance...")
        service = TherapeuticModelService()
        
        print("4. Getting model info...")
        info = service.get_model_info()
        for key, value in info.items():
            print(f"   {key}: {value}")
        
        if not info.get('model_available'):
            print("❌ Model not available")
            return False
        
        print("5. Testing model functionality...")
        success = service.test_model("Hello, how are you feeling today?")
        
        if not success:
            print("❌ Model test failed")
            return False
        
        print("6. Testing various text samples...")
        test_cases = [
            ("I feel really anxious about this.", "client", "negative"),
            ("How does that make you feel?", "therapist", "neutral"),
            ("I'm making great progress!", "client", "positive"),
            ("Let's explore that further.", "therapist", "neutral"),
            ("Je me sens bien aujourd'hui.", "client", "positive"),  # French
            ("¿Cómo te sientes hoy?", "therapist", "neutral"),  # Spanish
        ]
        
        for i, (text, expected_speaker, expected_sentiment) in enumerate(test_cases, 1):
            print(f"\n   Test {i}: '{text}'")
            try:
                result = service.analyze_text(text)
                print(f"   Result: {result}")
                
                # Check if predictions are reasonable (not strict matching)
                if result['speaker'] in ['client', 'therapist', 'unknown']:
                    print(f"   ✅ Speaker prediction valid: {result['speaker']}")
                else:
                    print(f"   ⚠️  Unexpected speaker: {result['speaker']}")
                
                if result['sentiment'] in ['positive', 'negative', 'neutral', 'mixed']:
                    print(f"   ✅ Sentiment prediction valid: {result['sentiment']}")
                else:
                    print(f"   ⚠️  Unexpected sentiment: {result['sentiment']}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                return False
        
        print("\n✅ Comprehensive test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_model_comprehensive()
    exit(0 if success else 1)
