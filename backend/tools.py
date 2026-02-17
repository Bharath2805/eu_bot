import os
from tavily import TavilyClient

# Initialize Tavily client
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

# Allowed web search domains (ONLY these 3 official EU URLs)
ALLOWED_SEARCH_DOMAINS = [
    "eur-lex.europa.eu",
    "ai-act-service-desk.ec.europa.eu",
    "digital-strategy.ec.europa.eu"
]

def search_web_restricted(query: str):
    """Search web using Tavily, restricted to allowed domains only"""
    if not tavily_client:
        return {"error": "Tavily API key not configured"}
        
    try:
        print(f"🌐 Web search query: {query}")
        print(f"   Restricted to domains: {ALLOWED_SEARCH_DOMAINS}")
        
        # Search with domain restriction
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            include_domains=ALLOWED_SEARCH_DOMAINS,
            max_results=5
        )
        
        results = []
        for result in response.get('results', []):
            results.append({
                "title": result.get('title', ''),
                "url": result.get('url', ''),
                "content": result.get('content', ''),
                "score": result.get('score', 0)
            })
        
        print(f"   Found {len(results)} results from allowed domains")
        return {
            "results": results,
            "query": query
        }
    except Exception as e:
        print(f"Web search error: {str(e)}")
        return {"results": [], "query": query, "error": str(e)}

# Tool Definitions
TOOLS = [
    {
        "type": "file_search",
        "file_search": {
            "max_num_results": 5
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "MANDATORY TOOL: You MUST use this for ALL compliance questions. Search official EU AI Act sources (eur-lex.europa.eu, ai-act-service-desk.ec.europa.eu, digital-strategy.ec.europa.eu) for up-to-date information. Use this AFTER file_search for EVERY compliance question - NO EXCEPTIONS.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant information"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "classify_risk",
            "description": "Classify an AI system's risk level according to the EU AI Act. Returns a structured JSON object with risk level, reasoning, and relevant articles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "system_description": {
                        "type": "string",
                        "description": "Description of the AI system to classify"
                    },
                    "features": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Key features of the AI system"
                    }
                },
                "required": ["system_description"]
            }
        }
    }
]

def classify_risk(system_description: str, features: list = None):
    """
    Mock risk classification logic.
    In a real scenario, this would use a more complex logic or another LLM call 
    specifically designed for classification with a deterministic prompt.
    For now, we return a structured placeholder.
    """
    # Simple keyword-based heuristic for the mockup
    description_lower = system_description.lower()
    
    if any(keyword in description_lower for keyword in ["biometric", "police", "surveillance", "safety component", "education", "employment"]):
         return {
            "risk_level": "High Risk",
            "reasoning": "The system falls under high-risk categories (e.g., biometrics, critical infrastructure, education, employment) as defined in Annex III of the EU AI Act.",
            "relevant_articles": ["Article 6", "Annex III"],
            "obligations": [
                "Risk management system (Art. 9)",
                "Data governance (Art. 10)",
                "Technical documentation (Art. 11)",
                "Record keeping (Art. 12)",
                "Transparency (Art. 13)",
                "Human oversight (Art. 14)",
                "Accuracy, robustness, cybersecurity (Art. 15)"
            ]
        }
    elif any(keyword in description_lower for keyword in ["chatbot", "deepfake", "emotion recognition", "manipulation"]):
        return {
            "risk_level": "Limited Risk", 
            "reasoning": "The system triggers transparency obligations (e.g., chatbots, emotion recognition, deep fakes) under Article 50.",
            "relevant_articles": ["Article 50"],
            "obligations": [
                "Transparency obligations (Art. 50): Inform users they are interacting with an AI system."
            ]
        }
    elif any(keyword in description_lower for keyword in ["spam", "game", "filter", "inventory"]):
        return {
            "risk_level": "Minimal Risk",
            "reasoning": "The system does not fall into prohibited, high-risk, or limited risk categories. It is free to use.",
            "relevant_articles": ["Article 69 (Voluntary Codes of Conduct)"],
            "obligations": [
                "No broad obligations, but voluntary codes of conduct are encouraged."
            ]
    }
    else:
         return {
            "risk_level": "Unclassified / Minimal Risk",
            "reasoning": "Based on the description properly provided, no specific high-risk or limited-risk criteria were matched.",
            "relevant_articles": [],
            "obligations": []
        }
