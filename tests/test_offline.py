#!/usr/bin/env python3
"""
Test script to verify the therapeutic model works completely offline
by setting HF_HUB_OFFLINE=1 to prevent any hub access
"""

import os
import sys
import logging

# Force offline mode - this will cause errors if any hub access is attempted
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

# Add src to path (adjust for tests/ subdirectory)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_offline_loading():
    """Test that the model loads and works completely offline"""
    print("🔒 Testing Offline-Only Loading (HF_HUB_OFFLINE=1)")
    print("=" * 50)
    
    try:
        print("1. Importing service (should not access hub)...")
        from services.therapeutic_model_service import TherapeuticModelService
        
        print("2. Creating service instance...")
        service = TherapeuticModelService()
        
        print("3. Checking if model loaded successfully...")
        if not service.is_available():
            print("❌ Model not available")
            return False
            
        print("4. Testing analysis...")
        result = service.analyze_text("Hello, how are you feeling today?")
        print(f"   Result: {result}")
        
        print("5. Testing French text...")
        result_fr = service.analyze_text("Je me sens bien aujourd'hui, merci.")
        print(f"   French result: {result_fr}")
        
        print("✅ Offline test passed! Model works without hub access.")
        return True
        
    except Exception as e:
        print(f"❌ Offline test failed: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_offline_loading()
    if success:
        print("\n🎉 Your model is truly self-contained and offline!")
    else:
        print("\n⚠️  Model still has hub dependencies that need to be resolved.")
    
    sys.exit(0 if success else 1)
