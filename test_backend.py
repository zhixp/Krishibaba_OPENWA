"""
Quick test script for Krishi Baba Backend
Run this to verify everything is working before starting the server
"""
import sys
import os

def test_imports():
    """Test if all dependencies are installed"""
    print("🔍 Testing dependencies...")
    
    try:
        import fastapi
        print("  ✅ FastAPI installed")
    except ImportError:
        print("  ❌ FastAPI missing - run: pip install -r requirements.txt")
        return False
    
    try:
        import aiosqlite
        print("  ✅ aiosqlite installed")
    except ImportError:
        print("  ❌ aiosqlite missing")
        return False
    
    try:
        import yaml
        print("  ✅ PyYAML installed")
    except ImportError:
        print("  ❌ PyYAML missing")
        return False
    
    try:
        import google.generativeai as genai
        print("  ✅ Google Generative AI installed")
    except ImportError:
        print("  ❌ google-generativeai missing")
        return False
    
    return True


def test_env_file():
    """Check if .env file exists"""
    print("\n🔍 Checking environment configuration...")
    
    if os.path.exists('.env'):
        print("  ✅ .env file found")
        return True
    else:
        print("  ⚠️  .env file not found")
        print("     Run: cp .env.example .env")
        print("     Then edit .env and add your GEMINI_API_KEY")
        return False


def test_prompts_file():
    """Check if prompts.yaml exists"""
    print("\n🔍 Checking prompts configuration...")
    
    if os.path.exists('app/core/prompts.yaml'):
        print("  ✅ prompts.yaml found")
        
        # Try loading it
        try:
            import yaml
            with open('app/core/prompts.yaml', 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                num_prompts = len(data.get('prompts', {}))
                print(f"  ✅ Loaded {num_prompts} prompt templates")
            return True
        except Exception as e:
            print(f"  ❌ Error loading prompts: {e}")
            return False
    else:
        print("  ❌ prompts.yaml not found")
        return False


def test_imports_app():
    """Test if app modules can be imported"""
    print("\n🔍 Testing app modules...")
    
    try:
        sys.path.insert(0, os.path.abspath('.'))
        from app.core.config import settings
        print("  ✅ Config module loaded")
        
        from app.core.prompt_manager import prompt_manager
        print(f"  ✅ Prompt manager loaded ({len(prompt_manager.list_prompts())} prompts)")
        
        return True
    except Exception as e:
        print(f"  ❌ Error importing app modules: {e}")
        return False


def main():
    print("=" * 60)
    print("🚜 KRISHI BABA - Backend Test Suite")
    print("=" * 60)
    
    # Change to backend directory
    if os.path.basename(os.getcwd()) != 'backend':
        if os.path.exists('backend'):
            os.chdir('backend')
        else:
            print("\n❌ Please run this script from the project root or backend directory")
            sys.exit(1)
    
    all_tests_passed = True
    
    # Run tests
    all_tests_passed &= test_imports()
    all_tests_passed &= test_env_file()
    all_tests_passed &= test_prompts_file()
    all_tests_passed &= test_imports_app()
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\n🚀 Ready to start the server:")
        print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("\n📚 API Docs will be at:")
        print("   http://localhost:8000/docs")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        print("\nPlease fix the issues above before starting the server.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
