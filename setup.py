"""
Setup script for ScholarLens - helps configure API keys and test integration
"""
import os
from pathlib import Path

print("=" * 70)
print("ScholarLens Setup")
print("=" * 70)
print()

# Check if .env exists
env_file = Path(".env")
env_example = Path(".env.example")

if not env_file.exists():
    print("⚠️  .env file not found")
    print()
    print("To enable real AI analysis with Google Gemini:")
    print()
    print("1. Get an API key from: https://makersuite.google.com/app/apikey")
    print("2. Copy .env.example to .env")
    print("3. Replace 'your_api_key_here' with your actual API key")
    print()
    
    create = input("Would you like to create .env file now? (y/n): ")
    if create.lower() == 'y':
        if env_example.exists():
            with open(env_example) as f:
                content = f.read()
            
            print()
            api_key = input("Enter your Gemini API key (or press Enter to skip): ")
            
            if api_key:
                content = content.replace("your_api_key_here", api_key)
            
            with open(env_file, "w") as f:
                f.write(content)
            
            print("✅ .env file created!")
            print()
        else:
            print("❌ .env.example not found")
else:
    print("✅ .env file exists")
    print()

# Check current configuration
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if api_key and api_key != "your_api_key_here":
    print("✅ GEMINI_API_KEY is set")
    print(f"   Key: {api_key[:8]}..." if len(api_key) > 8 else "   (too short)")
    print()
    print("🎉 You're ready to use ScholarLens with real AI analysis!")
else:
    print("⚠️  GEMINI_API_KEY not configured")
    print()
    print("   Currently running in PLACEHOLDER MODE:")
    print("   - PDF parsing works")
    print("   - All agents run")
    print("   - LLM calls return mock data")
    print()
    print("   To enable real AI:")
    print("   1. Edit .env file")
    print("   2. Set GEMINI_API_KEY=your_actual_key")

print()
print("=" * 70)
print("Quick Start Commands:")
print("=" * 70)
print()
print("# Test the system:")
print("python test_system.py")
print()
print("# Analyze a paper:")
print("python run.py --pdf data/test_pdfs/your_paper.pdf")
print()
print("# Start web API:")
print("python api/server.py")
print()
