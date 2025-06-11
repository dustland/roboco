#!/usr/bin/env python3
"""
SuperWriter Production Demo

Demonstrates the complete SuperWriter workflow for creating publication-quality research documents
with intelligent memory integration and iterative improvement.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from roboco.core.team_builder import TeamBuilder
from roboco.memory.manager import MemoryManager
from roboco.config.models import MemoryConfig


def print_header(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"📝 {title}")
    print('='*60)


def print_step(step: str, description: str):
    """Print a formatted step."""
    print(f"\n{step}. {description}")
    print("-" * 40)


async def demo_superwriter_workflow():
    """Demonstrate the complete SuperWriter research document workflow."""
    print_header("SuperWriter Production Demo")
    
    # Check for required API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable is required")
        print("   Set your OpenAI API key to run this demo")
        return False
    
    if not os.getenv("SERPAPI_KEY"):
        print("⚠️  Warning: SERPAPI_KEY not found - web search will be limited")
        print("   Set your SERP API key for full research capabilities")
    
    try:
        print_step("1", "Initializing SuperWriter Team")
        
        # Initialize team builder
        config_path = Path(__file__).parent / "config"
        team_builder = TeamBuilder(str(config_path))
        
        # Build the SuperWriter team
        team_config_path = config_path / "team.yaml"
        team = team_builder.build_team(str(team_config_path))
        
        print(f"✓ SuperWriter team initialized")
        print(f"  - Agents: {len(team.agents)}")
        for name, agent in team.agents.items():
            print(f"    • {name} ({type(agent).__name__})")
        print(f"  - Tools: {len(team.tools)}")
        for name in team.tools.keys():
            print(f"    • {name}")
        
        print_step("2", "Memory System Integration")
        
        # Initialize memory manager for the team
        memory_config = MemoryConfig()
        memory_config.vector_store = {
            "provider": "chroma",
            "config": {
                "collection_name": "superwriter_research",
                "path": "./workspace/memory_db"
            }
        }
        
        memory_manager = MemoryManager(memory_config)
        team.memory_manager = memory_manager
        
        print("✓ Mem0 memory system integrated")
        print("  - Intelligent research storage and retrieval")
        print("  - Multi-agent knowledge sharing")
        print("  - Iterative improvement tracking")
        
        print_step("3", "Document Generation Workflow")
        
        # Define a comprehensive research document task
        document_task = """
Create a comprehensive 3000-word research document on "The Future of AI-Human Collaboration in Knowledge Work".

The document should include:

1. **Executive Summary** (300 words)
   - Key trends and findings
   - Main conclusions and recommendations

2. **Current State Analysis** (800 words)
   - Current AI collaboration tools and platforms
   - Adoption rates and market trends
   - Key players and technologies

3. **Future Trends and Predictions** (1000 words)
   - Emerging technologies and capabilities
   - Expected developments in the next 2-5 years
   - Expert predictions and industry insights

4. **Challenges and Opportunities** (600 words)
   - Technical and social challenges
   - Economic implications
   - Opportunities for innovation

5. **Recommendations and Conclusions** (300 words)
   - Strategic recommendations for organizations
   - Key takeaways and action items

QUALITY REQUIREMENTS:
- Minimum 15 authoritative sources
- Proper citations and references
- Data-driven analysis with statistics
- Professional, publication-ready quality
- Clear structure and logical flow
- Industry expert perspectives and quotes

The document should be suitable for publication in a business or technology journal.
"""
        
        print("Task defined:")
        print("📋 Research Document: 'The Future of AI-Human Collaboration in Knowledge Work'")
        print("📊 Target: 3000 words, 15+ sources, publication quality")
        print("🎯 Sections: Executive Summary, Analysis, Trends, Challenges, Recommendations")
        
        # Execute the collaborative workflow
        print("\n🚀 Starting collaborative document creation...")
        print("   This will demonstrate the full research-write-review-iterate cycle")
        
        # Start the collaboration
        result = await team.run(document_task)
        
        print_step("4", "Collaboration Results")
        
        if result.success:
            print("✅ Document creation completed successfully!")
            print(f"\n📈 Collaboration Summary:")
            print(f"   • Participants: {', '.join(result.participants)}")
            print(f"   • Messages exchanged: {len(result.chat_history)}")
            print(f"   • Workflow: {result.summary}")
            
            # Display conversation highlights
            if result.chat_history:
                print(f"\n💬 Key Collaboration Moments:")
                
                # Show first few and last few messages to demonstrate workflow
                for i, msg in enumerate(result.chat_history[:3]):
                    print(f"   {i+1}. {msg['name']}: {msg['content'][:100]}...")
                
                if len(result.chat_history) > 6:
                    print("   ... (workflow continues with research, writing, review) ...")
                
                for i, msg in enumerate(result.chat_history[-3:], len(result.chat_history)-2):
                    print(f"   {i}. {msg['name']}: {msg['content'][:100]}...")
            
            # Check memory system for research artifacts
            print_step("5", "Research Memory Analysis")
            
            try:
                # Search for research memories
                research_memories = memory_manager.search_memory(
                    query="AI collaboration research findings sources",
                    limit=10
                )
                
                print(f"✓ Research artifacts in memory: {len(research_memories)}")
                
                if research_memories:
                    print("\n📚 Stored Research:")
                    for i, memory in enumerate(research_memories[:5], 1):
                        content_preview = memory['content'][:120].replace('\n', ' ')
                        print(f"   {i}. {content_preview}...")
                
                # Search for document drafts
                draft_memories = memory_manager.search_memory(
                    query="document draft sections writing",
                    limit=5
                )
                
                if draft_memories:
                    print(f"\n📝 Document drafts stored: {len(draft_memories)}")
                
            except Exception as e:
                print(f"⚠️  Memory analysis error: {e}")
            
            print_step("6", "Production Quality Assessment")
            
            # Analyze the final conversation for quality indicators
            final_content = result.chat_history[-1]['content'] if result.chat_history else ""
            
            quality_indicators = {
                "length": len(final_content.split()),
                "sections": final_content.count('#') + final_content.count('**'),
                "citations": final_content.count('[') + final_content.count('('),
                "data_points": final_content.count('%') + final_content.count('statistics') + final_content.count('data'),
            }
            
            print("📊 Quality Metrics:")
            print(f"   • Content length: {quality_indicators['length']} words")
            print(f"   • Structured sections: {quality_indicators['sections']}")
            print(f"   • Citations/references: {quality_indicators['citations']}")
            print(f"   • Data points: {quality_indicators['data_points']}")
            
            # Save the final document
            workspace_dir = Path("./workspace")
            workspace_dir.mkdir(exist_ok=True)
            
            output_file = workspace_dir / "ai_collaboration_research_document.md"
            with open(output_file, 'w') as f:
                f.write("# The Future of AI-Human Collaboration in Knowledge Work\n\n")
                f.write("*Generated by SuperWriter Professional*\n\n")
                f.write("## Collaboration Log\n\n")
                for msg in result.chat_history:
                    f.write(f"**{msg['name']}:** {msg['content']}\n\n---\n\n")
            
            print(f"\n💾 Document saved to: {output_file}")
            
        else:
            print("❌ Document creation failed")
            if result.error_message:
                print(f"   Error: {result.error_message}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main demo function."""
    print("🚀 SuperWriter Production Demo")
    print("Creating publication-quality research documents with AI collaboration")
    
    # Check workspace
    workspace = Path("./workspace")
    workspace.mkdir(exist_ok=True)
    
    # Run the demo
    success = await demo_superwriter_workflow()
    
    # Summary
    print_header("Demo Complete")
    
    if success:
        print("🎉 SuperWriter demo completed successfully!")
        print("\n✅ Capabilities Demonstrated:")
        print("   • Multi-agent collaborative research")
        print("   • Intelligent memory integration (Mem0)")
        print("   • Publication-quality document generation")
        print("   • Iterative research-write-review workflow")
        print("   • Professional structure and citations")
        
        print("\n📁 Generated Files:")
        print("   • Research document: ./workspace/ai_collaboration_research_document.md")
        print("   • Memory database: ./workspace/memory_db/")
        
        print("\n🔧 Production Features:")
        print("   • Comprehensive research with authoritative sources")
        print("   • Structured document organization")
        print("   • Quality review and iterative improvement")
        print("   • Memory-powered knowledge management")
        print("   • Professional formatting and citations")
        
    else:
        print("❌ Demo encountered errors")
        print("\n🔧 Troubleshooting:")
        print("   • Ensure OPENAI_API_KEY is set")
        print("   • Set SERPAPI_KEY for web search")
        print("   • Check network connectivity")
        print("   • Verify all dependencies are installed")
    
    print("\n📖 Next Steps:")
    print("   • Customize agent prompts for your domain")
    print("   • Add specialized research tools")
    print("   • Integrate with your document workflow")
    print("   • Scale to larger research teams")


if __name__ == "__main__":
    asyncio.run(main()) 