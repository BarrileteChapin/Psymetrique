#!/usr/bin/env python3
"""
Simple debug script for therapeutic model - isolated testing
"""

import sys
import logging
from pathlib import Path

# Add src to path (adjust for tests/ subdirectory)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def debug_model_simple():
    """Simple debug test without complex dependencies"""
    print("🔧 Simple Model Debug")
    print("=" * 30)
    
    try:
        print("1. Testing basic imports...")
        import torch
        from transformers import AutoTokenizer, AutoConfig, DistilBertModel
        print("   ✅ PyTorch and transformers imported")
        
        print("2. Checking model files...")
        model_path = Path(__file__).parent.parent / "src" / "Model"
        print(f"   Model path: {model_path}")
        print(f"   Exists: {model_path.exists()}")
        
        if model_path.exists():
            files = list(model_path.glob("*"))
            for file in files:
                print(f"   - {file.name} ({file.stat().st_size} bytes)")
        
        print("3. Testing tokenizer loading...")
        try:
            tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
            print(f"   ✅ Tokenizer loaded, vocab size: {len(tokenizer)}")
        except Exception as e:
            print(f"   ❌ Tokenizer failed: {e}")
            return False
        
        print("4. Testing config loading...")
        try:
            config = AutoConfig.from_pretrained(str(model_path), local_files_only=True)
            print(f"   ✅ Config loaded: {config.model_type}")
        except Exception as e:
            print(f"   ❌ Config failed: {e}")
            return False
        
        print("5. Testing model instantiation...")
        try:
            model = DistilBertModel(config)
            model.resize_token_embeddings(len(tokenizer))
            print(f"   ✅ Model created with {sum(p.numel() for p in model.parameters())} parameters")
        except Exception as e:
            print(f"   ❌ Model creation failed: {e}")
            return False
        
        print("6. Testing weight loading...")
        try:
            from safetensors.torch import load_file
            state_dict = load_file(str(model_path / "model.safetensors"))
            print(f"   ✅ Weights loaded, {len(state_dict)} tensors")
            
            # Try loading into model
            missing, unexpected = model.load_state_dict(state_dict, strict=False)
            print(f"   Missing keys: {len(missing)}")
            print(f"   Unexpected keys: {len(unexpected)}")
            
        except Exception as e:
            print(f"   ❌ Weight loading failed: {e}")
            return False
        
        print("7. Testing simple inference...")
        try:
            model.eval()
            inputs = tokenizer("Hello world", return_tensors="pt")
            with torch.no_grad():
                outputs = model(**inputs)
            print(f"   ✅ Inference successful, output shape: {outputs.last_hidden_state.shape}")
        except Exception as e:
            print(f"   ❌ Inference failed: {e}")
            return False
        
        print("\n✅ Simple debug completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = debug_model_simple()
    exit(0 if success else 1)
