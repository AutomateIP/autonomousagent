"""LangGraph-based agent core logic."""

import logging
from typing import Dict, List, Any, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.llm_provider import LLMProvider
from src.mcp_client import MCPManager

logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    """State definition for the agent."""
    messages: List[Dict[str, Any]]
    tools: List[Dict[str, Any]]
    system_prompt: str
    task_complete: bool
    iteration_count: int
    max_iterations: int
    pending_tool_calls: List[Dict[str, Any]]
    final_response: str
    error: str


class Agent:
    """LangGraph-based autonomous agent."""
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        mcp_manager: MCPManager,
        system_prompt: str,
        max_iterations: int = 10,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        """
        Initialize the agent.
        
        Args:
            llm_provider: LLM provider instance
            mcp_manager: MCP manager instance
            system_prompt: System prompt for the agent
            max_iterations: Maximum iterations to prevent infinite loops
            temperature: Temperature for LLM responses
            max_tokens: Maximum tokens for LLM responses
        """
        self.llm = llm_provider
        self.mcp = mcp_manager
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("reasoning", self._reasoning_node)
        workflow.add_node("execute_tools", self._tool_execution_node)
        workflow.add_node("respond", self._response_node)
        
        # Set entry point
        workflow.set_entry_point("reasoning")
        
        # Add conditional edges based on LLM decisions
        workflow.add_conditional_edges(
            "reasoning",
            self._route_after_reasoning,
            {
                "execute_tools": "execute_tools",
                "respond": "respond",
                "end": END
            }
        )
        
        # After tool execution, go back to reasoning
        workflow.add_edge("execute_tools", "reasoning")
        
        # After responding, end
        workflow.add_edge("respond", END)
        
        # Compile the workflow
        # Note: To increase recursion limit, use config={'recursion_limit': 50} when calling ainvoke
        return workflow.compile()
    
    def _reasoning_node(self, state: AgentState) -> AgentState:
        """
        Reasoning node: LLM decides what to do next.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        logger.info(f"Reasoning node - Iteration {state['iteration_count']}/{state['max_iterations']}")
        
        # Check iteration limit
        if state['iteration_count'] >= state['max_iterations']:
            logger.warning("Max iterations reached, forcing completion")
            state['task_complete'] = True
            return state
        
        try:
            # Get LLM response with tools
            response = self.llm.chat(
                messages=state['messages'],
                system_prompt=state['system_prompt'],
                tools=state['tools'],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            logger.info(f"LLM stop reason: {response['stop_reason']}")
            
            # Add assistant message to history (OpenAI format for LiteLLM)
            assistant_message = {
                "role": "assistant",
                "content": ""
            }

            # Add text content
            for content_block in response['content']:
                if content_block.get('type') == 'text':
                    assistant_message['content'] = content_block.get('text', '')

            # Add tool calls if any (OpenAI format)
            if response['tool_calls']:
                import json
                assistant_message['tool_calls'] = []
                for tool_call in response['tool_calls']:
                    assistant_message['tool_calls'].append({
                        "id": tool_call['id'],
                        "type": "function",
                        "function": {
                            "name": f"{tool_call['server']}_{tool_call['name']}",
                            "arguments": json.dumps(tool_call['arguments'])
                        }
                    })

            state['messages'].append(assistant_message)
            
            # Store tool calls in state for execution
            state['pending_tool_calls'] = response['tool_calls']
            
            # Check if task is complete
            if response['stop_reason'] == 'end_turn':
                state['task_complete'] = True
            elif response['stop_reason'] == 'tool_use':
                state['task_complete'] = False
            
            state['iteration_count'] += 1
            
            logger.debug(f"Reasoning complete. Tool calls: {len(response['tool_calls'])}")
            
        except Exception as e:
            logger.error(f"Error in reasoning node: {e}")
            state['task_complete'] = True
            state['error'] = str(e)
        
        return state
    
    async def _tool_execution_node(self, state: AgentState) -> AgentState:
        """
        Tool execution node: Execute tools requested by LLM.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        logger.info(f"Executing {len(state.get('pending_tool_calls', []))} tool(s)")
        
        tool_results = []
        
        for tool_call in state.get('pending_tool_calls', []):
            try:
                logger.info(f"Calling tool {tool_call['name']} on server {tool_call['server']}")
                
                # Execute tool via MCP
                result = await self.mcp.call_tool(
                    server_name=tool_call['server'],
                    tool_name=tool_call['name'],
                    arguments=tool_call['arguments']
                )
                
                # Format result for LiteLLM (OpenAI format)
                if result['success']:
                    tool_result = {
                        "role": "tool",
                        "tool_call_id": tool_call['id'],
                        "content": str(result['result'])
                    }
                else:
                    tool_result = {
                        "role": "tool",
                        "tool_call_id": tool_call['id'],
                        "content": f"Error: {result.get('error', 'Unknown error')}"
                    }

                tool_results.append(tool_result)
                
            except Exception as e:
                logger.error(f"Error executing tool {tool_call['name']}: {e}")
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tool_call['id'],
                    "content": f"Error executing tool: {str(e)}"
                })
        
        # Add tool results to messages (each as a separate message in OpenAI format)
        if tool_results:
            state['messages'].extend(tool_results)
        
        # Clear pending tool calls
        state['pending_tool_calls'] = []
        
        return state
    
    def _response_node(self, state: AgentState) -> AgentState:
        """
        Response node: Generate final response.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        logger.info("Generating final response")
        
        # Debug: log the messages structure
        logger.debug(f"Total messages: {len(state['messages'])}")
        for i, msg in enumerate(state['messages']):
            logger.debug(f"Message {i}: role={msg.get('role')}, content type={type(msg.get('content'))}")
            if msg.get('role') == 'assistant':
                logger.debug(f"Assistant message content: {msg.get('content')}")
        
        # Extract the final text response
        final_response = ""
        for message in reversed(state['messages']):
            if message['role'] == 'assistant':
                content = message.get('content', '')
                logger.debug(f"Processing assistant content: {content}")

                # Content should be a string in OpenAI format
                if isinstance(content, str) and content:
                    final_response = content
                    logger.debug(f"Found text response: {final_response[:100] if len(final_response) > 100 else final_response}")
                    break
        
        logger.info(f"Extracted response length: {len(final_response)}")
        state['final_response'] = final_response
        return state
    
    def _route_after_reasoning(self, state: AgentState) -> str:
        """
        Route to next node based on LLM decision.
        
        Args:
            state: Current agent state
            
        Returns:
            Next node name
        """
        # Check for errors
        if state.get('error'):
            return "respond"
        
        # Check if task is complete
        if state.get('task_complete', False):
            return "respond"
        
        # Check if there are tool calls to execute
        if state.get('pending_tool_calls'):
            return "execute_tools"
        
        # Default to responding
        return "respond"
    
    async def run(self, task: str) -> str:
        """
        Run the agent on a task.
        
        Args:
            task: Task description
            
        Returns:
            Agent's response
        """
        logger.info("Starting agent execution")
        
        # Get all available tools
        tools = self.mcp.get_all_tools()
        logger.info(f"Agent has access to {len(tools)} tools")
        
        # Initialize state
        initial_state = {
            "messages": [
                {
                    "role": "user",
                    "content": task
                }
            ],
            "tools": tools,
            "system_prompt": self.system_prompt,
            "task_complete": False,
            "iteration_count": 0,
            "max_iterations": self.max_iterations,
            "pending_tool_calls": []
        }
        
        # Run the graph with increased recursion limit for complex workflows
        final_state = await self.graph.ainvoke(
            initial_state,
            config={"recursion_limit": 50}
        )
        
        # Extract final response
        final_response = final_state.get('final_response', '')
        
        if not final_response:
            final_response = "Task completed but no response generated."
        
        logger.info("Agent execution completed")
        
        # Log usage stats if available
        total_input_tokens = 0
        total_output_tokens = 0
        iterations = final_state.get('iteration_count', 0)
        
        logger.info(f"Total iterations: {iterations}")
        
        return final_response
