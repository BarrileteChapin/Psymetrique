# Tests

This directory contains test scripts for the therapeutic BERT model.

## Test Scripts

### `quick_test.py`
Quick validation test for basic model functionality.
```bash
cd tests
python quick_test.py
```

### `test_direct_loading.py` 
Tests the direct weight loading functionality with French text examples.
```bash
cd tests
python test_direct_loading.py
```

### `test_model.py`
Comprehensive test covering model files, multilingual support, and various text samples.
```bash
cd tests
python test_model.py
```

### `test_offline.py`
Verifies the model works completely offline without any Hugging Face Hub access.
```bash
cd tests
python test_offline.py
```

### `debug_model_simple.py`
Low-level debugging script for isolated component testing.
```bash
cd tests
python debug_model_simple.py
```

## Running All Tests

To run all tests sequentially:
```bash
cd tests
python quick_test.py && python test_direct_loading.py && python test_model.py && python test_offline.py
```

## Expected Results

All tests should pass with:
- ✅ Model loads successfully using direct weight loading
- ✅ No fallback to SimpleTherapeuticModel
- ✅ Reasonable predictions for speaker identification and sentiment analysis
- ✅ Multi-language support (English, French, Spanish)
- ✅ Complete offline functionality
