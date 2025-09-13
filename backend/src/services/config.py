import httpx
import os

async def check_agent_config(agent_id: str):
    """Retrieve and display current agent configuration"""
    
    headers = {
        "Authorization": f"Bearer {os.getenv('RETELL_API_KEY')}",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.retellai.com/v2/agents/{agent_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            config = response.json()
            print("Current Agent Configuration:")
            print(f"Agent ID: {config.get('agent_id')}")
            print(f"LLM Model: {config.get('llm_model')}")
            print("\nFunctions/Tools:")
            
            # Check for functions in different possible locations
            if 'functions' in config:
                for func in config['functions']:
                    print(f"  - {func.get('name')}: {func.get('description')}")
            elif 'tools' in config:
                for tool in config['tools']:
                    print(f"  - {tool.get('name')}: {tool.get('description')}")
            else:
                print("  No functions/tools found!")
            
            return config
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None

# Run this with your agent ID
agent_config = await check_agent_config("agent_56478e9eb6eaf4f70dc9fa4c31")