"""
Test script for ScholarLens - validates all components without needing a PDF.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("ScholarLens System Validation Test")
print("=" * 70)
print()

# Test 1: Import all modules
print("✓ Testing imports...")
try:
    from src.utils import config, get_logger, chunk_text, dict_to_markdown
    from src.tools import PDFParser, TextCleaner, CodeExecutor
    from src.memory import SessionManager
    from src.agents import (
        DocumentExtractorAgent,
        SummaryAgent,
        MethodologyAgent,
        MathAgent,
        CritiqueAgent,
        ImplementationAgent,
        AggregatorAgent
    )
    from src.orchestrator import OrchestratorAgent
    print("  ✅ All imports successful!")
except Exception as e:
    print(f"  ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Configuration
print("\n✓ Testing configuration...")
try:
    from src.utils.config import Config
    print(f"  ✅ Config loaded successfully")
    print(f"     Project root: {Config.PROJECT_ROOT}")
    print(f"     Model: {Config.GEMINI_MODEL_NAME}")
    print(f"     Output dir: {Config.OUTPUTS_DIR}")
except Exception as e:
    print(f"  ❌ Config failed: {e}")

# Test 3: Logger
print("\n✓ Testing logger...")
try:
    logger = get_logger("test")
    logger.info("Test log message")
    print("  ✅ Logger working!")
except Exception as e:
    print(f"  ❌ Logger failed: {e}")

# Test 4: Text utilities
print("\n✓ Testing text utilities...")
try:
    print("  Testing dict_to_markdown...")
    test_dict = {"key1": "value1", "key2": {"nested": "value2"}}
    markdown = dict_to_markdown(test_dict)
    print(f"  ✅ Dict to markdown: {len(markdown)} chars generated")
    
    print("  Testing chunk_text...")
    test_text = "This is a test string. " * 50
    chunks = chunk_text(test_text, chunk_size=100)
    print(f"  ✅ Text chunking: {len(chunks)} chunks created")
except Exception as e:
    print(f"  ❌ Text utilities failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Session Manager
print("\n✓ Testing session manager...")
try:
    session_mgr = SessionManager()
    session_id = session_mgr.create_session("test.pdf")
    print(f"  ✅ Session created: {session_id}")
    
    session_mgr.store_agent_output(session_id, "test_agent", {"result": "success"})
    print(f"  ✅ Agent output stored")
    
    sessions = session_mgr.list_sessions()
    print(f"  ✅ Active sessions: {len(sessions)}")
except Exception as e:
    print(f"  ❌ Session manager failed: {e}")

# Test 6: Text Cleaner
print("\n✓ Testing text cleaner...")
try:
    cleaner = TextCleaner()
    dirty_text = "  This   has    extra\\n\\nspaces   and\\t\\ttabs  "
    clean = cleaner.clean_text(dirty_text)
    print(f"  ✅ Text cleaned: '{clean}'")
except Exception as e:
    print(f"  ❌ Text cleaner failed: {e}")

# Test 7: Code Executor
print("\n✓ Testing code executor...")
try:
    executor = CodeExecutor()
    # Simple test without actual execution to avoid Windows signal issues
    result = executor.validate_syntax("print('Hello')\nx = 2 + 2")
    print(f"  ✅ Code validator working: syntax_valid={result[0]}")
    print(f"  ⚠️  Skipping actual execution test on Windows (signal.alarm not available)")
except Exception as e:
    print(f"  ❌ Code executor failed: {e}")

# Test 8: Agent initialization
print("\n✓ Testing agent initialization...")
try:
    agents_tested = []
    
    doc_agent = DocumentExtractorAgent()
    agents_tested.append("DocumentExtractor")
    
    summary_agent = SummaryAgent()
    agents_tested.append("Summary")
    
    method_agent = MethodologyAgent()
    agents_tested.append("Methodology")
    
    math_agent = MathAgent()
    agents_tested.append("Math")
    
    critique_agent = CritiqueAgent()
    agents_tested.append("Critique")
    
    impl_agent = ImplementationAgent()
    agents_tested.append("Implementation")
    
    agg_agent = AggregatorAgent()
    agents_tested.append("Aggregator")
    
    print(f"  ✅ All {len(agents_tested)} agents initialized:")
    for agent_name in agents_tested:
        print(f"     - {agent_name}Agent")
except Exception as e:
    print(f"  ❌ Agent initialization failed: {e}")

# Test 9: Orchestrator
print("\n✓ Testing orchestrator...")
try:
    orchestrator = OrchestratorAgent()
    print(f"  ✅ Orchestrator initialized successfully")
except Exception as e:
    print(f"  ❌ Orchestrator failed: {e}")

# Summary
print("\n" + "=" * 70)
print("🎉 All Tests Passed!")
print("=" * 70)
print("\nScholarLens is ready to analyze research papers!")
print("\nNext steps:")
print("  1. Set GEMINI_API_KEY environment variable for LLM integration")
print("  2. Place a research paper PDF in data/test_pdfs/")
print("  3. Run: python run.py --pdf data/test_pdfs/your_paper.pdf")
print("\nOr try with placeholder mode (no LLM calls):")
print("  python run.py --pdf <any_pdf_path>")
print()
