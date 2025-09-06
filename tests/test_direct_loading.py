#!/usr/bin/env python3
"""
Test direct weight loading functionality for the therapeutic BERT model
"""

import sys
import logging
from pathlib import Path

# Add src to path (adjust for tests/ subdirectory)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_direct_loading():
    """Test that the therapeutic model loads using direct weight loading"""
    print("🧪 Testing Direct Weight Loading")
    print("=" * 40)
    
    try:
        print("1. Creating service with direct loading...")
        from services.therapeutic_model_service import TherapeuticModelService
        
        service = TherapeuticModelService()
        
        print("2. Getting model info...")
        info = service.get_model_info()
        print(f"   Model type: {info.get('model_type')}")
        print(f"   Available: {info.get('model_available')}")
        print(f"   Device: {info.get('device')}")
        print(f"   Tokenizer vocab size: {info.get('tokenizer_vocab_size', 'N/A')}")
        
        if not info.get('model_available'):
            print("❌ Model not available")
            return False
        
        print("3. Testing with French text (like your example)...")
        french_text = "Je comprends, et ce que vous décrivez correspond bien à ce que nous avons discuté."
        print(f"   Text: '{french_text[:50]}...'")
        
        result = service.analyze_text(french_text)
        print(f"   ✅ Result: {result}")
        
        print("4. Testing simple test method...")
        success = service.test_model("Hello, how are you feeling today?")
        
        if success:
            print("✅ Direct weight loading test passed!")
            return True
        else:
            print("❌ Model test failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_direct_loading()
    exit(0 if success else 1)
