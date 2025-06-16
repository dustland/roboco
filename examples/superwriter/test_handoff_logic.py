#!/usr/bin/env python3
"""
Standalone test for handoff logic
Tests natural language routing without framework dependencies
"""

import re
from typing import Optional, Dict, Any, List


def route_based_on_description(reason: str, context: str, explicit_agent: str = None, available_agents: List[str] = None) -> Dict[str, Any]:
    """Route handoff based on descriptive reason like AG2."""
    if available_agents is None:
        available_agents = ['consultant', 'researcher', 'writer', 'reviewer']
    
    if explicit_agent:
        return {
            'destination_agent': explicit_agent,
            'reason': reason,
            'context': context,
            'routing_method': 'explicit'
        }
    
    # Analyze the full text for intent
    full_text = f"{reason} {context}".lower()
    
    # More intelligent routing based on specific actions and context
    # Order matters - more specific patterns first
    
    # Review and feedback patterns
    if re.search(r'need.*review|ready.*review|for.*review', full_text):
        target = 'reviewer'
    elif re.search(r'review.*complete.*approved|section.*approved|final.*approval', full_text):
        target = 'writer'  # Continue writing after approval
    elif re.search(r'feedback.*provided|revision.*needed|more.*research.*needed', full_text):
        if 'research' in full_text:
            target = 'researcher'
        else:
            target = 'writer'
    
    # Research patterns
    elif re.search(r'begin.*research|start.*research|research.*team.*should|ready.*research', full_text):
        target = 'researcher'
    elif re.search(r'research.*complete.*ready.*writ|research.*sufficient.*writ|ready.*for.*writing', full_text):
        target = 'writer'
    elif re.search(r'research.*complete.*review|research.*done.*review', full_text):
        target = 'reviewer'
    
    # Writing patterns  
    elif re.search(r'begin.*writing|start.*writing|writing.*team|ready.*for.*writing', full_text):
        target = 'writer'
    elif re.search(r'draft.*complete|section.*complete|writing.*done', full_text):
        target = 'reviewer'
    
    # Requirements/planning patterns
    elif re.search(r'requirements.*clear|requirements.*gathered|scope.*defined', full_text):
        target = 'researcher'
    
    # Default patterns based on keywords
    elif any(word in full_text for word in ['research', 'sources', 'investigate', 'data']):
        target = 'researcher'
    elif any(word in full_text for word in ['write', 'draft', 'content', 'document']):
        target = 'writer'
    elif any(word in full_text for word in ['review', 'feedback', 'evaluate', 'quality']):
        target = 'reviewer'
    else:
        print(f"🤔 No clear routing found for: {reason}")
        return None
    
    if target in available_agents:
        print(f"🧠 Natural routing: '{reason[:50]}...' → {target}")
        return {
            'destination_agent': target,
            'reason': reason,
            'context': context,
            'routing_method': 'natural_language'
        }
    
    print(f"🤔 Agent {target} not available for: {reason}")
    return None


def detect_natural_handoff(response: str) -> Optional[Dict[str, Any]]:
    """Detect natural handoff requests based on context and completion signals."""
    response_lower = response.lower()
    
    # Look for completion/transition signals
    handoff_indicators = [
        # Requirements/planning completion  
        r"requirements.*(?:clear|gathered|defined)",
        r"scope.*defined",
        r"ready.*(?:begin|start).*research",
        
        # Research completion patterns
        r"research.*(?:complete|finished|done|sufficient)",
        r"found.*\d+.*sources",
        r"comprehensive.*research",
        
        # Writing completion patterns
        r"(?:section|draft).*(?:complete|finished|done)",
        r"wrote.*section",
        r"full.*report.*compiled",
        
        # Review patterns
        r"need.*review",
        r"ready.*for.*review", 
        r"review.*complete",
        r"feedback.*provided",
        r"more.*research.*needed",
        r"revision.*needed"
    ]
    
    for pattern in handoff_indicators:
        if re.search(pattern, response_lower):
            # Use the entire response as context for better routing
            return route_based_on_description(
                reason=f"Natural completion detected",
                context=response
            )
    
    return None


def test_handoff_routing():
    """Test the natural language handoff routing."""
    print("🧪 Testing Natural Language Handoff Routing")
    print("=" * 60)
    
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
        },
        {
            "response": "Review complete and section approved. Writer can continue with next section using the current research foundation.",
            "expected_agent": "writer",
            "description": "Review approval → Writer continue"
        },
        {
            "response": "This section needs more research on safety statistics. Insufficient data to support the claims made.",
            "expected_agent": "researcher",
            "description": "Review feedback → More research needed"
        }
    ]
    
    print("\n🔍 Testing Handoff Detection:")
    correct = 0
    total = len(test_cases)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['description']}")
        print(f"Input: {test['response'][:100]}...")
        
        handoff = detect_natural_handoff(test["response"])
        
        if handoff:
            detected_agent = handoff.get('destination_agent')
            routing_method = handoff.get('routing_method', 'unknown')
            
            if detected_agent == test["expected_agent"]:
                print(f"✅ PASS: Detected {detected_agent} (method: {routing_method})")
                correct += 1
            else:
                print(f"❌ FAIL: Expected {test['expected_agent']}, Got {detected_agent}")
        else:
            print(f"❌ FAIL: No handoff detected!")
    
    print(f"\n📊 Results: {correct}/{total} tests passed ({correct/total*100:.1f}%)")
    
    if correct == total:
        print("🎉 All tests passed! Natural handoff routing is working correctly.")
    else:
        print("⚠️  Some tests failed. Handoff patterns may need adjustment.")


if __name__ == "__main__":
    test_handoff_routing() 