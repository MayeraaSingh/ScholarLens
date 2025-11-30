"""
Orchestrator for ScholarLens.

Coordinates all specialized agents to analyze research papers
and generate comprehensive reports. Handles agent execution order,
error recovery, and session management.
"""

import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from src.agents import (
    DocumentExtractorAgent,
    SummaryAgent,
    MethodologyAgent,
    MathAgent,
    CritiqueAgent,
    ImplementationAgent,
    AggregatorAgent
)
from src.memory import SessionManager, get_session_manager
from src.utils import get_logger, config, export_json, export_markdown
from src.tools import parse_pdf


class OrchestratorAgent:
    """
    Main orchestrator that coordinates all specialized agents.
    
    Execution flow:
    1. DocumentExtractor → Parse PDF
    2. Parallel: Summary, Methodology, Math, Critique, Implementation
    3. Aggregator → Final report synthesis
    """
    
    def __init__(
        self,
        session_manager: Optional[SessionManager] = None,
        logger=None,
        enable_parallel: bool = False
    ):
        """
        Initialize orchestrator.
        
        Args:
            session_manager: Session manager instance
            logger: Logger instance
            enable_parallel: Whether to run agents in parallel (future enhancement)
        """
        self.session_manager = session_manager or get_session_manager()
        self.logger = logger or get_logger("OrchestratorAgent", config.LOGS_DIR)
        self.enable_parallel = enable_parallel
        
        # Initialize all agents
        self.logger.info("Initializing agents...")
        self.document_agent = DocumentExtractorAgent(logger=self.logger, config=config)
        self.summary_agent = SummaryAgent(logger=self.logger, config=config)
        self.methodology_agent = MethodologyAgent(logger=self.logger, config=config)
        self.math_agent = MathAgent(logger=self.logger, config=config)
        self.critique_agent = CritiqueAgent(logger=self.logger, config=config)
        self.implementation_agent = ImplementationAgent(logger=self.logger, config=config)
        self.aggregator_agent = AggregatorAgent(logger=self.logger, config=config)
        
        self.logger.info("All agents initialized successfully")
    
    def analyze_paper(
        self,
        pdf_path: str,
        session_id: Optional[str] = None,
        save_outputs: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze a research paper through the full agent pipeline.
        
        Args:
            pdf_path: Path to PDF file
            session_id: Optional session ID (creates new if not provided)
            save_outputs: Whether to save outputs to disk
            
        Returns:
            Final research report dictionary
        """
        start_time = time.time()
        self.logger.info(f"Starting paper analysis: {pdf_path}")
        
        # Validate PDF path
        pdf_path_obj = Path(pdf_path)
        if not pdf_path_obj.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Create or retrieve session
        if session_id is None:
            session_id = self.session_manager.create_session(
                paper_path=str(pdf_path_obj),
                metadata={'started_at': time.time()}
            )
            self.logger.info(f"Created new session: {session_id}")
        else:
            self.logger.info(f"Using existing session: {session_id}")
        
        try:
            # Stage 1: Document Extraction
            self.logger.info("=" * 60)
            self.logger.info("STAGE 1: Document Extraction")
            self.logger.info("=" * 60)
            document_result = self._run_document_extraction(session_id, str(pdf_path_obj))
            
            # Stage 2: Parallel Analysis (sequential for now)
            self.logger.info("=" * 60)
            self.logger.info("STAGE 2: Multi-Agent Analysis")
            self.logger.info("=" * 60)
            analysis_results = self._run_analysis_agents(session_id, document_result)
            
            # Stage 3: Aggregation
            self.logger.info("=" * 60)
            self.logger.info("STAGE 3: Report Aggregation")
            self.logger.info("=" * 60)
            final_report = self._run_aggregation(session_id, analysis_results)
            
            # Update session with final report
            self.session_manager.store_final_report(session_id, final_report)
            
            # Save outputs to disk
            if save_outputs:
                self._save_outputs(pdf_path_obj, final_report)
            
            # Calculate total duration
            total_duration = time.time() - start_time
            self.logger.info("=" * 60)
            self.logger.info(f"✅ Analysis complete! Total duration: {total_duration:.2f}s")
            self.logger.info(f"Session ID: {session_id}")
            self.logger.info("=" * 60)
            
            # Add execution metadata to report
            final_report['execution_metadata'] = {
                'session_id': session_id,
                'total_duration': total_duration,
                'pdf_path': str(pdf_path_obj)
            }
            
            return final_report
            
        except Exception as e:
            self.logger.error(f"Error during analysis: {str(e)}")
            self.session_manager.update_session(session_id, {'status': 'failed'})
            raise
    
    def _run_document_extraction(
        self,
        session_id: str,
        pdf_path: str
    ) -> Dict[str, Any]:
        """
        Run document extraction agent.
        
        Args:
            session_id: Session ID
            pdf_path: Path to PDF
            
        Returns:
            Document extraction result
        """
        self.logger.info(f"📄 Extracting document: {pdf_path}")
        
        result = self.document_agent.run({
            'file_path': pdf_path,
            'session_id': session_id
        })
        
        if result['status'] != 'success':
            raise RuntimeError(f"Document extraction failed: {result.get('errors')}")
        
        # Store document in session
        document = result['result']
        self.session_manager.store_document(session_id, document)
        self.session_manager.store_agent_output(session_id, 'DocumentExtractor', result)
        
        self.logger.info(f"✓ Document extracted: {document.get('title', 'Unknown')}")
        return document
    
    def _run_analysis_agents(
        self,
        session_id: str,
        document: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run all analysis agents (summary, methodology, math, critique, implementation).
        
        Args:
            session_id: Session ID
            document: Extracted document
            
        Returns:
            Dictionary of agent results
        """
        results = {}
        full_text = document.get('full_text', '')
        
        # Summary Agent
        self.logger.info("📝 Generating summaries...")
        summary_result = self.summary_agent.run({
            'document': document,
            'session_id': session_id
        })
        results['Summary'] = summary_result
        self.session_manager.store_agent_output(session_id, 'Summary', summary_result)
        self.logger.info("✓ Summaries generated")
        
        # Methodology Agent
        self.logger.info("🔬 Analyzing methodology...")
        methodology_result = self.methodology_agent.run({
            'document': document,
            'full_text': full_text,
            'session_id': session_id
        })
        results['Methodology'] = methodology_result
        self.session_manager.store_agent_output(session_id, 'Methodology', methodology_result)
        self.logger.info("✓ Methodology analyzed")
        
        # Math Agent
        self.logger.info("🔢 Interpreting equations...")
        math_result = self.math_agent.run({
            'equations': document.get('equations', []),
            'context': full_text,
            'session_id': session_id
        })
        results['Math'] = math_result
        self.session_manager.store_agent_output(session_id, 'Math', math_result)
        num_equations = len(math_result.get('result', {}).get('interpretations', []))
        self.logger.info(f"✓ Interpreted {num_equations} equations")
        
        # Critique Agent
        self.logger.info("🎯 Performing critical analysis...")
        critique_result = self.critique_agent.run({
            'document': document,
            'full_text': full_text,
            'session_id': session_id
        })
        results['Critique'] = critique_result
        self.session_manager.store_agent_output(session_id, 'Critique', critique_result)
        repro_score = critique_result.get('result', {}).get('reproducibility_score', 0)
        self.logger.info(f"✓ Critical analysis complete (reproducibility: {repro_score}/10)")
        
        # Implementation Agent
        self.logger.info("💻 Generating implementation guidance...")
        implementation_result = self.implementation_agent.run({
            'methodology': methodology_result.get('result', {}),
            'algorithms_text': full_text[:3000],  # Pass relevant text
            'document': document,
            'session_id': session_id
        })
        results['Implementation'] = implementation_result
        self.session_manager.store_agent_output(session_id, 'Implementation', implementation_result)
        self.logger.info("✓ Implementation guidance generated")
        
        return results
    
    def _run_aggregation(
        self,
        session_id: str,
        analysis_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run aggregator agent to synthesize final report.
        
        Args:
            session_id: Session ID
            analysis_results: All agent results
            
        Returns:
            Final report
        """
        self.logger.info("📊 Aggregating results into final report...")
        
        # Get all agent outputs from session
        all_outputs = {}
        for agent_name in ['DocumentExtractor', 'Summary', 'Methodology', 'Math', 'Critique', 'Implementation']:
            output = self.session_manager.get_agent_output(session_id, agent_name)
            if output:
                all_outputs[agent_name] = output
        
        # Run aggregator
        aggregator_result = self.aggregator_agent.run({
            'agent_outputs': all_outputs,
            'session_id': session_id
        })
        
        if aggregator_result['status'] != 'success':
            raise RuntimeError(f"Aggregation failed: {aggregator_result.get('errors')}")
        
        self.session_manager.store_agent_output(session_id, 'Aggregator', aggregator_result)
        
        final_report = aggregator_result['result']
        self.logger.info("✓ Final report generated")
        
        return final_report
    
    def _save_outputs(
        self,
        pdf_path: Path,
        report: Dict[str, Any]
    ) -> None:
        """
        Save outputs to disk.
        
        Args:
            pdf_path: Original PDF path
            report: Final report
        """
        # Create output filename based on PDF name
        base_name = pdf_path.stem
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_path = config.get_output_path(f"{base_name}_{timestamp}_report.json")
        export_json(report, json_path, indent=config.OUTPUT_JSON_INDENT)
        self.logger.info(f"💾 Saved JSON report: {json_path}")
        
        # Save Markdown
        markdown_content = report.get('final_markdown', '')
        if markdown_content:
            md_path = config.get_output_path(f"{base_name}_{timestamp}_report.md")
            export_markdown(markdown_content, md_path)
            self.logger.info(f"💾 Saved Markdown report: {md_path}")
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all active sessions.
        
        Returns:
            List of session summaries
        """
        return self.session_manager.list_sessions()
    
    def get_session_report(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get final report for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Final report or None
        """
        session = self.session_manager.get_session(session_id)
        if session:
            return session.final_report
        return None
    
    def clear_sessions(self) -> int:
        """
        Clear all sessions.
        
        Returns:
            Number of sessions cleared
        """
        return self.session_manager.clear_all_sessions()
