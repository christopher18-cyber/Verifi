from typing import TypedDict, List, Dict, Any, Optional

class ScamState(TypedDict):
    message: str
    language: str
    rules: Dict[str, Any]
    llm_output: Optional[Dict[str, Any]]
    final: Dict[str, Any]