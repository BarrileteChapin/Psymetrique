#!/usr/bin/env python3
"""
Quick test to verify the therapeutic model fixes
"""

import sys
import logging
from pathlib import Path

# Add src to path (adjust for tests/ subdirectory)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set up logging to see debug info
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_user_pattern():
    """Test using the exact pattern the user described as working"""
    print("\n🔬 Testing User's Working Pattern")
    print("-" * 40)
    
    try:
        from services.therapeutic_model_service import TherapeuticModelService
        
        service = TherapeuticModelService()
        
        if not service.is_available():
            print("❌ Service not available")
            return False
        
        # Test the user's exact pattern
        test_text = "I feel really anxious about this session."
        print(f"Testing: '{test_text}'")
        
        # Use the new simple test method
        success = service.create_simple_test(test_text)
        return success
        
    except Exception as e:
        print(f"❌ User pattern test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🧪 Quick Model Test")
    print("=" * 30)
    
    try:
        from services.therapeutic_model_service import TherapeuticModelService
        
        print("1. Creating service...")
        service = TherapeuticModelService()
        
        print("2. Getting model info...")
        info = service.get_model_info()
        print(f"   Model type: {info.get('model_type')}")
        print(f"   Available: {info.get('model_available')}")
        print(f"   Device: {info.get('device')}")
        print(f"   Speaker labels: {info.get('speaker_labels')}")
        print(f"   Sentiment labels: {info.get('sentiment_labels')}")
        
        if not info.get('model_available'):
            print("❌ Model not available, stopping test")
            return False
        
        print("3. Testing analysis...")
        test_texts = [
            "I feel really good today.",
            "How are you feeling about this?",
            "This is difficult for me."
        ]
        
        for i, text in enumerate(test_texts, 1):
            print(f"\n   Test {i}: '{text}'")
            try:
                result = service.analyze_text(text)
                print(f"   ✅ Result: {result}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                return False
        
        # Test user's pattern
        if not test_user_pattern():
            return False
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
