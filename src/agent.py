"""Main entry point for the autonomous agent."""

import asyncio
import logging
import sys

from src.config import Config
from src.mcp_client import create_mcp_manager
from src.llm_provider import create_llm_provider
from src.agent_core import Agent

logger = logging.getLogger(__name__)


async def main_async():
    """Async main function."""
    try:
        # Load configuration
        config = Config()
        config.setup_logging()
        
        logger.info("=== Autonomous Agent Starting ===")
        
        # Load prompts
        system_prompt = config.load_system_prompt()
        task_prompt = config.load_agent_prompt()
        
        logger.info(f"Task: {task_prompt[:100]}...")
        
        # Load MCP configuration
        mcp_config = config.load_mcp_config()
        
        # Get LLM configuration
        llm_config = config.get_llm_config()
        
        # Initialize LLM provider
        logger.info(f"Initializing LLM provider: {llm_config['provider']} - {llm_config['model']}")
        llm = create_llm_provider(
            provider=llm_config['provider'],
            model=llm_config['model'],
            api_key=llm_config['api_key']
        )
        
        # Initialize MCP manager and connect to all servers
        async with create_mcp_manager(mcp_config) as mcp_manager:
            # Get agent configuration
            max_iterations = config.get_max_iterations()
            
            # Create agent
            agent = Agent(
                llm_provider=llm,
                mcp_manager=mcp_manager,
                system_prompt=system_prompt,
                max_iterations=max_iterations,
                temperature=llm_config['temperature'],
                max_tokens=llm_config['max_tokens']
            )
            
            # Run agent
            result = await agent.run(task_prompt)
            
            # Output result
            logger.info("=== Agent Result ===")
            logger.debug(f"Result type: {type(result)}, length: {len(result) if result else 0}")
            print("\n" + "="*80)
            print("AGENT RESPONSE:")
            print("="*80)
            print(result if result else "No response generated")
            print("="*80 + "\n")
            
            logger.info("=== Agent Completed Successfully ===")
            return 0
            
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


def main():
    """Main entry point."""
    try:
        exit_code = asyncio.run(main_async())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
