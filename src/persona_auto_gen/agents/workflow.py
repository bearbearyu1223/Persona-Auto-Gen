"""Main LangGraph workflow for persona data generation."""

from typing import Dict, List, Any, TypedDict
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
import json
import logging

from ..config import Config
from .nodes import (
    ProfileAnalysisNode,
    DataGenerationNode, 
    ValidationNode,
    ReflectionNode,
    OutputNode
)

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """State object passed between workflow nodes."""
    config: Config
    user_profile: Dict[str, Any]
    events: List[str]
    analysis: Dict[str, Any]
    generated_data: Dict[str, Any]
    validation_results: Dict[str, Any]
    reflection_results: Dict[str, Any]
    output_path: str
    errors: List[str]
    current_step: str


class PersonaWorkflow:
    """Main workflow orchestrator using LangGraph."""
    
    def __init__(self, config: Config):
        self.config = config
        self.graph = self._create_workflow()
        
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""
        workflow = StateGraph(WorkflowState)
        
        # Initialize nodes
        profile_node = ProfileAnalysisNode(self.config)
        generation_node = DataGenerationNode(self.config)
        validation_node = ValidationNode(self.config)
        reflection_node = ReflectionNode(self.config)
        output_node = OutputNode(self.config)
        
        # Add nodes to the graph
        workflow.add_node("analyze_profile", profile_node.run)
        workflow.add_node("generate_data", generation_node.run)
        workflow.add_node("validate_data", validation_node.run)
        workflow.add_node("reflect_quality", reflection_node.run)
        workflow.add_node("package_output", output_node.run)
        
        # Define the workflow flow
        workflow.set_entry_point("analyze_profile")
        workflow.add_edge("analyze_profile", "generate_data")
        workflow.add_edge("generate_data", "validate_data")
        
        # Conditional edge for validation results
        workflow.add_conditional_edges(
            "validate_data",
            self._should_regenerate,
            {
                "regenerate": "generate_data",
                "continue": "reflect_quality"
            }
        )
        
        workflow.add_edge("reflect_quality", "package_output")
        workflow.add_edge("package_output", END)
        
        return workflow.compile()
    
    def _should_regenerate(self, state: WorkflowState) -> str:
        """Decide whether to regenerate data based on validation results."""
        validation_results = state.get("validation_results", {})
        
        # Check if there are critical validation errors
        for app_name, results in validation_results.items():
            if results.get("critical_errors", 0) > 0:
                logger.warning(f"Critical validation errors found in {app_name}, regenerating...")
                return "regenerate"
        
        # Check if too many validation errors overall
        total_errors = sum(
            results.get("total_errors", 0) 
            for results in validation_results.values()
        )
        
        if total_errors > self.config.max_validation_errors:
            logger.warning(f"Too many validation errors ({total_errors}), regenerating...")
            return "regenerate"
            
        return "continue"
    
    def run(self, user_profile: Dict[str, Any], events: List[str]) -> Dict[str, Any]:
        """Run the complete workflow."""
        logger.info("Starting persona data generation workflow")
        
        # Initialize state
        initial_state: WorkflowState = {
            "config": self.config,
            "user_profile": user_profile,
            "events": events,
            "analysis": {},
            "generated_data": {},
            "validation_results": {},
            "reflection_results": {},
            "output_path": "",
            "errors": [],
            "current_step": "initialize"
        }
        
        try:
            # Run the workflow
            final_state = self.graph.invoke(initial_state)
            
            logger.info(f"Workflow completed successfully. Output saved to: {final_state['output_path']}")
            
            return {
                "success": True,
                "output_path": final_state["output_path"],
                "generated_data": final_state["generated_data"],
                "validation_results": final_state["validation_results"],
                "reflection_results": final_state["reflection_results"],
                "errors": final_state["errors"]
            }
            
        except Exception as e:
            logger.error(f"Workflow failed with error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "output_path": "",
                "generated_data": {},
                "validation_results": {},
                "reflection_results": {},
                "errors": [str(e)]
            }
    
    async def arun(self, user_profile: Dict[str, Any], events: List[str]) -> Dict[str, Any]:
        """Run the workflow asynchronously."""
        logger.info("Starting async persona data generation workflow")
        
        initial_state: WorkflowState = {
            "config": self.config,
            "user_profile": user_profile,
            "events": events,
            "analysis": {},
            "generated_data": {},
            "validation_results": {},
            "reflection_results": {},
            "output_path": "",
            "errors": [],
            "current_step": "initialize"
        }
        
        try:
            final_state = await self.graph.ainvoke(initial_state)
            
            logger.info(f"Async workflow completed successfully. Output saved to: {final_state['output_path']}")
            
            return {
                "success": True,
                "output_path": final_state["output_path"],
                "generated_data": final_state["generated_data"],
                "validation_results": final_state["validation_results"],
                "reflection_results": final_state["reflection_results"],
                "errors": final_state["errors"]
            }
            
        except Exception as e:
            logger.error(f"Async workflow failed with error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "output_path": "",
                "generated_data": {},
                "validation_results": {},
                "reflection_results": {},
                "errors": [str(e)]
            }