#!/usr/bin/env python3
"""
Hospital Management System Multi-Agent Startup Script
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main startup function"""
    print("🏥 Hospital Management System Multi-Agent Server")
    print("=" * 50)
    
    try:
        # Import and run the multi-agent server
        from multi_agent_server import mcp, orchestrator, MULTI_AGENT_AVAILABLE, DATABASE_AVAILABLE
        
        print(f"🗃️  Database: {'✅ Connected' if DATABASE_AVAILABLE else '❌ Not available'}")
        print(f"🤖 Multi-Agent System: {'✅ Active' if MULTI_AGENT_AVAILABLE else '❌ Not available'}")
        
        if MULTI_AGENT_AVAILABLE and orchestrator:
            print(f"🔧 Agents Loaded: {len(orchestrator.agents)}")
            for agent_name, agent in orchestrator.agents.items():
                print(f"   • {agent.agent_name} ({len(agent.get_tools())} tools)")
            
            print(f"📋 Total Tools: {len(orchestrator.get_tools())}")
        
        print("\n🚀 Starting server on http://0.0.0.0:8000")
        print("📡 Available endpoints:")
        print("   • GET  /health - Health check")
        print("   • GET  /tools/list - List all tools")
        print("   • POST /tools/call - Execute tools")
        print("\n" + "=" * 50)
        
        # Start the server
        if __name__ == "__main__":
            import uvicorn
            from multi_agent_server import mcp
            
            # Get the SSE app from FastMCP
            app = mcp.sse_app()
            uvicorn.run(app, host="0.0.0.0", port=8000)
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Please ensure all dependencies are installed:")
        print("   pip install fastmcp sqlalchemy psycopg2-binary")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Startup Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
