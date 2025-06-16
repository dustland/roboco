#!/usr/bin/env python3
"""
Simple test for SuperWriter handoff system
Tests the natural language handoff routing
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import agentx
from agentx.core.team import Team
from agentx.core.orchestrator import Orchestrator


async def test_natural_handoffs():
    """Test natural language handoff routing."""
    print("🧪 Testing Natural Language Handoffs")
    print("=" * 50)
    
    # Initialize
    agentx.initialize()
    
    # Load team
    config_path = Path(__file__).parent / "config" / "team.yaml"
    team = Team.from_config(str(config_path))
    orchestrator = Orchestrator(team, max_rounds=10)
    
    print(f"✅ Loaded team: {team.name}")
    print(f"👥 Agents: {list(team.agents.keys())}")
    
    # Test handoff detection directly
    test_cases = [
        {
            "response": "Requirements are now clear and comprehensive. Research team should begin investigating Tesla's autonomous driving capabilities.",
            "expected_agent": "researcher",
            "description": "Consultant completion → Researcher"
        },
        {
            "response": "Comprehensive research complete on Tesla FSD technology. Found 25 high-quality sources covering technical capabilities, market analysis, and regulatory challenges. Ready for quality review and validation.",
            "expected_agent": "reviewer", 
            "description": "Research completion → Reviewer"
        },
        {
            "response": "Research phase complete with 30 validated sources. All major topics covered. Writing team can now begin drafting with comprehensive source material available.",
            "expected_agent": "writer",
            "description": "Research sufficient → Writer"
        },
        {
            "response": "Section draft completed on Tesla's technical architecture. Need review and feedback before proceeding to next section.",
            "expected_agent": "reviewer",
            "description": "Writing completion → Reviewer"
        }
    ]
    
    print("\n🔍 Testing Handoff Detection:")
    for i, test in enumerate(test_cases, 1):
        handoff = orchestrator._detect_handoff_request(test["response"])
        
        if handoff:
            detected_agent = handoff.get('destination_agent')
            routing_method = handoff.get('routing_method', 'unknown')
            
            if detected_agent == test["expected_agent"]:
                print(f"✅ Test {i}: {test['description']}")
                print(f"   Detected: {detected_agent} (method: {routing_method})")
            else:
                print(f"❌ Test {i}: {test['description']}")
                print(f"   Expected: {test['expected_agent']}, Got: {detected_agent}")
        else:
            print(f"❌ Test {i}: {test['description']}")
            print(f"   No handoff detected!")
        print()
    
    print("🎉 Natural handoff testing complete!")


if __name__ == "__main__":
    asyncio.run(test_natural_handoffs()) 