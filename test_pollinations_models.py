"""
Test all Pollinations models with different prompts to find which work best
"""

import requests
import os
import time
import urllib.parse
import uuid
import hashlib
from PIL import Image

# Test folder
TEST_FOLDER = "test_pollination_images"
os.makedirs(TEST_FOLDER, exist_ok=True)

POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt/"

# All available Pollinations models
MODELS_TO_TEST = [
    'flux',
    'flux-realism', 
    'flux-anime',
    'flux-3d',
    'turbo',
    'flux-pro',
    'flux-dev',
    'midjourney',
    'dall-e-3',
    'stable-diffusion-xl'
]

# Test prompts - from simple to complex
TEST_PROMPTS = [
    # Simple prompt
    "A man kneeling in a forest",
    
    # Your problematic prompt (original)
    "Arjun kneeling before Drona, a stern-faced warrior instructor, in a serene forest setting., Epic scale, vibrant colors reflecting Indian mythology, with a focus on natural landscapes and evocative lighting., professional quality",
    
    # Cleaned version of your prompt
    "Arjun kneeling before Drona in a forest setting, natural lighting, professional quality",
    
    # Very simple version
    "Young warrior kneeling before instructor in forest",
    
    # Abstract test
    "Epic scale mythology with evocative lighting"
]

def test_single_model_prompt(model, prompt, test_name):
    """Test a single model with a single prompt"""
    
    print(f"\n[TESTING] Model: {model} | Test: {test_name}")
    print(f"Prompt: {prompt[:80]}...")
    
    # Generate unique seed
    unique_string = f"{prompt}_{model}_{time.time()}_{uuid.uuid4().hex}"
    seed_hash = hashlib.md5(unique_string.encode()).hexdigest()
    seed = int(seed_hash[:8], 16)
    
    # Build parameters
    params = {
        'width': 1024,
        'height': 576,
        'model': model,
        'seed': seed,
        'nologo': 'true',
        'nofeed': 'true',
        'safe': 'true'
    }
    
    # Add model-specific parameters
    if model in ['flux', 'flux-realism', 'flux-pro', 'flux-dev']:
        params['enhance'] = 'true'
    
    encoded_prompt = urllib.parse.quote(prompt)
    param_string = "&".join([f"{k}={v}" for k, v in params.items()])
    full_url = f"{POLLINATIONS_BASE_URL}{encoded_prompt}?{param_string}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cache-Control': 'no-cache',
            'X-Request-ID': f"{uuid.uuid4().hex}_{model}"
        }
        
        response = requests.get(full_url, timeout=60, headers=headers)
        
        if response.status_code != 200:
            print(f"[FAILED] HTTP {response.status_code}")
            return {
                'model': model,
                'test_name': test_name,
                'status': 'failed',
                'error': f"HTTP {response.status_code}",
                'file_path': None
            }
        
        # Check content
        content_type = response.headers.get('content-type', '').lower()
        if 'image' not in content_type and 'octet-stream' not in content_type:
            print(f"[FAILED] Invalid content type: {content_type}")
            return {
                'model': model,
                'test_name': test_name,
                'status': 'failed',
                'error': f"Invalid content type: {content_type}",
                'file_path': None
            }
        
        # Save image
        filename = f"{test_name}_{model}_{seed}.png"
        filepath = os.path.join(TEST_FOLDER, filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        # Validate image
        try:
            with Image.open(filepath) as img:
                width, height = img.size
                img.verify()
            
            file_size = os.path.getsize(filepath)
            
            if file_size < 1024:  # Less than 1KB
                print(f"[FAILED] Image too small: {file_size} bytes")
                return {
                    'model': model,
                    'test_name': test_name,
                    'status': 'failed',
                    'error': f"Image too small: {file_size} bytes",
                    'file_path': filepath
                }
            
            print(f"[SUCCESS] Generated: {filename} ({width}x{height}, {file_size/1024:.1f}KB)")
            return {
                'model': model,
                'test_name': test_name,
                'status': 'success',
                'file_path': filepath,
                'file_size': file_size,
                'dimensions': f"{width}x{height}",
                'seed_used': seed
            }
            
        except Exception as e:
            print(f"[FAILED] Image validation failed: {e}")
            return {
                'model': model,
                'test_name': test_name,
                'status': 'failed',
                'error': f"Image validation failed: {e}",
                'file_path': filepath
            }
        
    except requests.exceptions.Timeout:
        print(f"[FAILED] Timeout")
        return {
            'model': model,
            'test_name': test_name,
            'status': 'failed',
            'error': 'Timeout',
            'file_path': None
        }
    except Exception as e:
        print(f"[FAILED] Error: {e}")
        return {
            'model': model,
            'test_name': test_name,
            'status': 'failed',
            'error': str(e),
            'file_path': None
        }

def run_all_tests():
    """Run tests for all models and prompts"""
    
    print("=" * 80)
    print("POLLINATIONS MODEL TESTING")
    print("=" * 80)
    
    all_results = []
    
    for i, prompt in enumerate(TEST_PROMPTS):
        test_name = f"test_{i+1}"
        print(f"\n{'='*60}")
        print(f"TEST {i+1}: {prompt[:50]}...")
        print(f"{'='*60}")
        
        for model in MODELS_TO_TEST:
            result = test_single_model_prompt(model, prompt, test_name)
            all_results.append(result)
            
            # Small delay between requests
            time.sleep(2)
    
    # Generate summary
    print(f"\n{'='*80}")
    print("SUMMARY RESULTS")
    print(f"{'='*80}")
    
    # Group by model
    model_stats = {}
    for result in all_results:
        model = result['model']
        if model not in model_stats:
            model_stats[model] = {'success': 0, 'failed': 0, 'total': 0}
        
        model_stats[model]['total'] += 1
        if result['status'] == 'success':
            model_stats[model]['success'] += 1
        else:
            model_stats[model]['failed'] += 1
    
    print("\nMODEL PERFORMANCE:")
    print("-" * 50)
    for model, stats in model_stats.items():
        success_rate = (stats['success'] / stats['total']) * 100
        print(f"{model:15} | {stats['success']:2}/{stats['total']} successes ({success_rate:5.1f}%)")
    
    # Group by test
    print("\nTEST PERFORMANCE:")
    print("-" * 50)
    test_stats = {}
    for result in all_results:
        test = result['test_name']
        if test not in test_stats:
            test_stats[test] = {'success': 0, 'failed': 0, 'total': 0}
        
        test_stats[test]['total'] += 1
        if result['status'] == 'success':
            test_stats[test]['success'] += 1
        else:
            test_stats[test]['failed'] += 1
    
    for i, prompt in enumerate(TEST_PROMPTS):
        test_name = f"test_{i+1}"
        stats = test_stats.get(test_name, {'success': 0, 'total': 0})
        success_rate = (stats['success'] / stats['total']) * 100 if stats['total'] > 0 else 0
        print(f"{test_name:8} | {stats['success']:2}/{stats['total']} successes ({success_rate:5.1f}%) | {prompt[:40]}")
    
    # Show successful images
    print(f"\nSUCCESSFUL IMAGES GENERATED:")
    print("-" * 50)
    successful_results = [r for r in all_results if r['status'] == 'success']
    for result in successful_results:
        print(f"{result['model']:15} | {result['test_name']:8} | {os.path.basename(result['file_path'])}")
    
    # Save detailed results to JSON
    import json
    results_file = os.path.join(TEST_FOLDER, "test_results.json")
    with open(results_file, 'w') as f:
        json.dump({
            'test_prompts': TEST_PROMPTS,
            'models_tested': MODELS_TO_TEST,
            'detailed_results': all_results,
            'model_stats': model_stats,
            'test_stats': test_stats,
            'total_tests': len(all_results),
            'successful_tests': len(successful_results)
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: {results_file}")
    print(f"Images saved to: {TEST_FOLDER}/")
    print(f"\nTotal tests run: {len(all_results)}")
    print(f"Successful generations: {len(successful_results)}")
    
    return all_results

if __name__ == "__main__":
    print("Starting Pollinations model testing...")
    print(f"Test folder: {os.path.abspath(TEST_FOLDER)}")
    
    results = run_all_tests()
    
    print("\n" + "="*80)
    print("TESTING COMPLETE!")
    print("="*80)
    print(f"Check the '{TEST_FOLDER}' folder for generated images")
    print("Compare the images to see which models work best for your use case")