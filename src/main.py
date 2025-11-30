"""
Main entry point for ScholarLens.

Command-line interface for analyzing research papers.
"""

import sys
import argparse
from pathlib import Path

from src.orchestrator import OrchestratorAgent
from src.utils import config, main_logger, get_logger
from src.memory import get_session_manager


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='ScholarLens - AI-powered research paper analyzer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a single paper
  python main.py --pdf paper.pdf
  
  # Analyze with specific session
  python main.py --pdf paper.pdf --session abc123
  
  # List all sessions
  python main.py --list-sessions
  
  # Clear all sessions
  python main.py --clear-sessions
  
  # Get report for a session
  python main.py --get-report abc123
"""
    )
    
    parser.add_argument(
        '--pdf',
        type=str,
        help='Path to PDF file to analyze'
    )
    
    parser.add_argument(
        '--session',
        type=str,
        help='Session ID to use (creates new if not provided)'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save outputs to disk'
    )
    
    parser.add_argument(
        '--list-sessions',
        action='store_true',
        help='List all active sessions'
    )
    
    parser.add_argument(
        '--get-report',
        type=str,
        metavar='SESSION_ID',
        help='Get report for a specific session'
    )
    
    parser.add_argument(
        '--clear-sessions',
        action='store_true',
        help='Clear all sessions'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        help=f'Output directory (default: {config.OUTPUTS_DIR})'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Configure logging level
    config.LOG_LEVEL = args.log_level
    logger = get_logger("main", config.LOGS_DIR)
    
    # Print banner
    print_banner()
    
    # Validate environment
    if not config.validate_environment():
        logger.warning("⚠️  Environment validation failed. LLM features will be limited.")
        print("\n⚠️  WARNING: GEMINI_API_KEY not set. LLM features will use placeholders.")
        print("Set environment variable: export GEMINI_API_KEY=your_key_here\n")
    
    # Update output directory if provided
    if args.output_dir:
        config.OUTPUTS_DIR = Path(args.output_dir)
        config.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize orchestrator
    try:
        session_manager = get_session_manager()
        orchestrator = OrchestratorAgent(session_manager=session_manager, logger=logger)
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        print(f"\n❌ Error: Failed to initialize ScholarLens: {e}")
        return 1
    
    # Handle different commands
    try:
        # List sessions
        if args.list_sessions:
            sessions = orchestrator.list_sessions()
            print(f"\n📋 Active Sessions ({len(sessions)}):\n")
            if not sessions:
                print("No active sessions.")
            else:
                for session in sessions:
                    print(f"  • {session['session_id']}")
                    print(f"    Paper: {session['paper_path']}")
                    print(f"    Status: {session['status']}")
                    print(f"    Created: {session['created_at']}")
                    print()
            return 0
        
        # Get report for session
        if args.get_report:
            report = orchestrator.get_session_report(args.get_report)
            if report:
                print(f"\n📊 Report for session {args.get_report}:\n")
                print(report.get('final_markdown', 'No markdown available'))
            else:
                print(f"\n❌ No report found for session: {args.get_report}")
            return 0
        
        # Clear sessions
        if args.clear_sessions:
            count = orchestrator.clear_sessions()
            print(f"\n🗑️  Cleared {count} sessions")
            return 0
        
        # Analyze paper
        if args.pdf:
            pdf_path = Path(args.pdf)
            
            if not pdf_path.exists():
                print(f"\n❌ Error: PDF file not found: {pdf_path}")
                return 1
            
            print(f"\n🚀 Starting analysis of: {pdf_path.name}\n")
            
            # Run analysis
            report = orchestrator.analyze_paper(
                pdf_path=str(pdf_path),
                session_id=args.session,
                save_outputs=not args.no_save
            )
            
            # Print summary
            print("\n" + "=" * 80)
            print("📊 ANALYSIS SUMMARY")
            print("=" * 80)
            
            metadata = report.get('metadata', {})
            print(f"\n📄 Title: {metadata.get('title', 'Unknown')}")
            print(f"👥 Authors: {', '.join(metadata.get('authors', ['Unknown']))}")
            print(f"📖 Pages: {metadata.get('num_pages', 0)}")
            print(f"📐 Equations: {metadata.get('num_equations', 0)}")
            
            # Print TL;DR
            summaries = report.get('summaries', {})
            tldr = summaries.get('tldr', '')
            if tldr:
                print(f"\n💡 TL;DR:\n{tldr}")
            
            # Print reproducibility score
            critique = report.get('critique', {})
            repro_score = critique.get('reproducibility_score', 0)
            print(f"\n🔬 Reproducibility Score: {repro_score}/10")
            
            # Print output paths
            if not args.no_save:
                print(f"\n💾 Outputs saved to: {config.OUTPUTS_DIR}")
            
            exec_meta = report.get('execution_metadata', {})
            duration = exec_meta.get('total_duration', 0)
            print(f"\n⏱️  Total Duration: {duration:.2f} seconds")
            print(f"🆔 Session ID: {exec_meta.get('session_id', 'Unknown')}")
            
            print("\n" + "=" * 80)
            print("✅ Analysis complete!")
            print("=" * 80 + "\n")
            
            return 0
        
        # No command provided
        print("\n❌ Error: No command provided. Use --help for usage information.")
        return 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
        logger.info("Analysis interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1


def print_banner():
    """Print application banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███████╗ ██████╗██╗  ██╗ ██████╗ ██╗      █████╗ ██████╗  ║
║   ██╔════╝██╔════╝██║  ██║██╔═══██╗██║     ██╔══██╗██╔══██╗ ║
║   ███████╗██║     ███████║██║   ██║██║     ███████║██████╔╝ ║
║   ╚════██║██║     ██╔══██║██║   ██║██║     ██╔══██║██╔══██╗ ║
║   ███████║╚██████╗██║  ██║╚██████╔╝███████╗██║  ██║██║  ██║ ║
║   ╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ║
║                                                               ║
║              LENS - AI Research Paper Analyzer               ║
║                   Multi-Agent Analysis System                ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)


if __name__ == '__main__':
    sys.exit(main())
