"""
Text chunking utilities for ScholarLens.

Handles splitting long documents into manageable chunks while preserving
context through overlap and section-aware splitting.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""
    content: str
    chunk_id: int
    start_pos: int
    end_pos: int
    section: Optional[str] = None
    token_count: Optional[int] = None


class TextChunker:
    """Handles text chunking with various strategies."""
    
    def __init__(
        self,
        chunk_size: int = 8000,
        overlap: int = 500,
        min_chunk_size: int = 100
    ):
        """
        Initialize text chunker.
        
        Args:
            chunk_size: Maximum size of each chunk in approximate tokens
            overlap: Number of tokens to overlap between chunks
            min_chunk_size: Minimum size for a chunk to be considered valid
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Uses simple word-based heuristic (1 token ≈ 0.75 words).
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Simple approximation: split by whitespace and multiply by factor
        words = len(text.split())
        return int(words * 1.33)  # ~0.75 words per token
    
    def chunk_by_tokens(self, text: str) -> List[TextChunk]:
        """
        Chunk text by approximate token count with overlap.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of TextChunk objects
        """
        chunks = []
        words = text.split()
        
        # Approximate words per chunk (chunk_size tokens * 0.75)
        words_per_chunk = int(self.chunk_size * 0.75)
        overlap_words = int(self.overlap * 0.75)
        
        start_idx = 0
        chunk_id = 0
        
        while start_idx < len(words):
            # Get chunk with overlap
            end_idx = min(start_idx + words_per_chunk, len(words))
            chunk_words = words[start_idx:end_idx]
            chunk_text = ' '.join(chunk_words)
            
            # Calculate character positions (approximate)
            start_pos = sum(len(w) + 1 for w in words[:start_idx])
            end_pos = start_pos + len(chunk_text)
            
            # Create chunk
            chunk = TextChunk(
                content=chunk_text,
                chunk_id=chunk_id,
                start_pos=start_pos,
                end_pos=end_pos,
                token_count=self.estimate_tokens(chunk_text)
            )
            chunks.append(chunk)
            
            # Move to next chunk with overlap
            start_idx = end_idx - overlap_words
            chunk_id += 1
            
            # Prevent infinite loop on small texts
            if start_idx >= len(words) - overlap_words:
                break
        
        return chunks
    
    def chunk_by_sections(
        self,
        text: str,
        sections: Optional[List[Dict[str, Any]]] = None
    ) -> List[TextChunk]:
        """
        Chunk text by sections (if provided), otherwise by tokens.
        
        Args:
            text: Input text
            sections: List of section dictionaries with 'title', 'start', 'end'
            
        Returns:
            List of TextChunk objects
        """
        if not sections:
            return self.chunk_by_tokens(text)
        
        chunks = []
        chunk_id = 0
        
        for section in sections:
            section_title = section.get('title', 'Unknown')
            start = section.get('start', 0)
            end = section.get('end', len(text))
            
            section_text = text[start:end]
            section_tokens = self.estimate_tokens(section_text)
            
            # If section is small enough, keep as single chunk
            if section_tokens <= self.chunk_size:
                chunk = TextChunk(
                    content=section_text,
                    chunk_id=chunk_id,
                    start_pos=start,
                    end_pos=end,
                    section=section_title,
                    token_count=section_tokens
                )
                chunks.append(chunk)
                chunk_id += 1
            else:
                # Split large sections into sub-chunks
                sub_chunks = self.chunk_by_tokens(section_text)
                for sub_chunk in sub_chunks:
                    chunk = TextChunk(
                        content=sub_chunk.content,
                        chunk_id=chunk_id,
                        start_pos=start + sub_chunk.start_pos,
                        end_pos=start + sub_chunk.end_pos,
                        section=section_title,
                        token_count=sub_chunk.token_count
                    )
                    chunks.append(chunk)
                    chunk_id += 1
        
        return chunks
    
    def chunk_by_paragraphs(self, text: str) -> List[TextChunk]:
        """
        Chunk text by paragraphs, grouping them to meet chunk size.
        
        Args:
            text: Input text
            
        Returns:
            List of TextChunk objects
        """
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        chunk_id = 0
        current_chunk = []
        current_tokens = 0
        current_start = 0
        
        for para in paragraphs:
            para_tokens = self.estimate_tokens(para)
            
            # If adding this paragraph exceeds chunk size, save current chunk
            if current_tokens + para_tokens > self.chunk_size and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunk = TextChunk(
                    content=chunk_text,
                    chunk_id=chunk_id,
                    start_pos=current_start,
                    end_pos=current_start + len(chunk_text),
                    token_count=current_tokens
                )
                chunks.append(chunk)
                chunk_id += 1
                
                # Start new chunk with overlap (keep last paragraph)
                if len(current_chunk) > 1:
                    overlap_para = current_chunk[-1]
                    current_chunk = [overlap_para, para]
                    current_tokens = self.estimate_tokens(overlap_para) + para_tokens
                    current_start += len('\n\n'.join(current_chunk[:-2])) + 2
                else:
                    current_chunk = [para]
                    current_tokens = para_tokens
                    current_start += len(chunk_text) + 2
            else:
                current_chunk.append(para)
                current_tokens += para_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunk = TextChunk(
                content=chunk_text,
                chunk_id=chunk_id,
                start_pos=current_start,
                end_pos=current_start + len(chunk_text),
                token_count=current_tokens
            )
            chunks.append(chunk)
        
        return chunks
    
    def get_chunk_context(
        self,
        chunks: List[TextChunk],
        chunk_id: int,
        context_window: int = 1
    ) -> str:
        """
        Get context around a specific chunk (includes adjacent chunks).
        
        Args:
            chunks: List of all chunks
            chunk_id: ID of the target chunk
            context_window: Number of chunks to include on each side
            
        Returns:
            Combined text with context
        """
        if not chunks or chunk_id >= len(chunks):
            return ""
        
        start_idx = max(0, chunk_id - context_window)
        end_idx = min(len(chunks), chunk_id + context_window + 1)
        
        context_chunks = chunks[start_idx:end_idx]
        return '\n\n'.join(chunk.content for chunk in context_chunks)
    
    def reconstruct_text(self, chunks: List[TextChunk]) -> str:
        """
        Reconstruct original text from chunks (removes overlap).
        
        Args:
            chunks: List of TextChunk objects
            
        Returns:
            Reconstructed text
        """
        if not chunks:
            return ""
        
        # Sort chunks by chunk_id
        sorted_chunks = sorted(chunks, key=lambda x: x.chunk_id)
        
        # For simplicity, join with newlines (overlap removal is approximate)
        return '\n\n'.join(chunk.content for chunk in sorted_chunks)


def chunk_text(
    text: str,
    chunk_size: int = 8000,
    overlap: int = 500,
    strategy: str = "tokens"
) -> List[TextChunk]:
    """
    Convenience function to chunk text with specified strategy.
    
    Args:
        text: Input text
        chunk_size: Maximum chunk size in tokens
        overlap: Overlap between chunks in tokens
        strategy: Chunking strategy ('tokens', 'paragraphs')
        
    Returns:
        List of TextChunk objects
    """
    chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)
    
    if strategy == "paragraphs":
        return chunker.chunk_by_paragraphs(text)
    else:
        return chunker.chunk_by_tokens(text)
