#!/usr/bin/env python3
"""
Langfuse integration module for the Emergency Management System.
Based on official Langfuse documentation and best practices.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

try:
    from langfuse import Langfuse
    from langfuse.langchain import CallbackHandler
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    logging.warning("Langfuse not available. Install with: pip install langfuse")

logger = logging.getLogger(__name__)

class LangfuseManager:
    """Manages Langfuse integration following official documentation."""
    
    def __init__(self):
        self.client: Optional[Langfuse] = None
        self.handler: Optional[CallbackHandler] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Langfuse client following official patterns."""
        if not LANGFUSE_AVAILABLE:
            logger.warning("Langfuse not available")
            return
        
        try:
            secret_key = os.getenv('LANGFUSE_SECRET_KEY')
            public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
            host = os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')
            
            if secret_key and public_key:
                self.client = Langfuse(
                    secret_key=secret_key,
                    public_key=public_key,
                    host=host
                )
                
                # Create LangChain callback handler with correct parameters for Langfuse 3.x
                # Note: Langfuse 3.x CallbackHandler only needs public_key
                self.handler = CallbackHandler(
                    public_key=public_key
                )
                
                if self.client.auth_check():
                    logger.info("Langfuse client initialized successfully")
                else:
                    logger.warning("Langfuse authentication failed")
                    self.client = None
                    self.handler = None
            else:
                logger.warning("LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY not found")
                
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse client: {e}")
            self.client = None
            self.handler = None
    
    def is_available(self) -> bool:
        """Check if Langfuse is available and properly configured."""
        return self.client is not None and self.client.auth_check()
    
    def create_trace(self, name: str, session_id: str = None, user_id: str = None, 
                     metadata: Dict[str, Any] = None) -> Optional[Any]:
        """
        Create a new trace following official Langfuse 3.x patterns.
        In Langfuse 3.x, we use start_span as the root span.
        """
        if not self.is_available():
            return None
        
        try:
            # In Langfuse 3.x, we start with a root span
            # session_id and user_id are passed via metadata
            span_metadata = metadata or {}
            if session_id:
                span_metadata['session_id'] = session_id
            if user_id:
                span_metadata['user_id'] = user_id
                
            span = self.client.start_span(
                name=name
            )
            
            # Set metadata if provided
            if span_metadata:
                span.update(metadata=span_metadata)
                
            return span
        except Exception as e:
            logger.error(f"Failed to create trace: {e}")
            return None
    
    def update_trace(self, trace_id: str, metadata: Dict[str, Any]):
        """Update trace with additional metadata."""
        if not self.is_available() or not trace_id:
            return
        
        try:
            # In Langfuse 3.x, we update the current span
            self.client.update_current_span(metadata=metadata)
        except Exception as e:
            logger.error(f"Failed to update trace: {e}")
    
    def log_generation(self, trace_id: str, name: str, model: str, prompt: str, 
                       completion: str, metadata: Dict[str, Any] = None):
        """Log a generation event following official patterns."""
        if not self.is_available() or not trace_id:
            return
        
        try:
            self.client.generation(
                trace_id=trace_id,
                name=name,
                model=model,
                prompt=prompt,
                completion=completion,
                metadata=metadata or {}
            )
        except Exception as e:
            logger.error(f"Failed to log generation: {e}")
    
    def log_span(self, trace_id: str, name: str, input: Dict[str, Any] = None,
                 output: Dict[str, Any] = None, metadata: Dict[str, Any] = None):
        """
        Log a span event following official Langfuse 3.x patterns.
        """
        if not self.is_available() or not trace_id:
            return
        
        try:
            # In Langfuse 3.x, we start a new span
            span = self.client.start_span(
                name=name
            )
            
            # Set input, output, and metadata
            if input is not None:
                span.update(input=input)
            if output is not None:
                span.update(output=output)
            if metadata is not None:
                span.update(metadata=metadata)
                
            # End the span
            span.end()
            
            return span
        except Exception as e:
            logger.error(f"Failed to log span: {e}")
            return None
    
    def log_score(self, trace_id: str, name: str, value: float, comment: str = None):
        """Log a score for evaluation."""
        if not self.is_available() or not trace_id:
            return
        
        try:
            self.client.score(
                trace_id=trace_id,
                name=name,
                value=value,
                comment=comment
            )
        except Exception as e:
            logger.error(f"Failed to log score: {e}")
    
    def flush(self):
        """Flush all pending events to Langfuse."""
        if self.is_available():
            try:
                self.client.flush()
            except Exception as e:
                logger.error(f"Failed to flush events: {e}")
    
    def shutdown(self):
        """Shutdown the Langfuse client properly."""
        if self.is_available():
            try:
                self.client.shutdown()
                logger.info("Langfuse client shut down")
            except Exception as e:
                logger.error(f"Failed to shutdown Langfuse client: {e}")

# Global Langfuse manager instance
langfuse_manager = LangfuseManager()

def get_langfuse_handler():
    """Get the Langfuse callback handler for LangChain integration."""
    return langfuse_manager.handler if langfuse_manager.is_available() else None

def is_langfuse_available():
    """Check if Langfuse is available."""
    return langfuse_manager.is_available()
