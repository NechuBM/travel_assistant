import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Storage directory
STORAGE_DIR = Path(__file__).parent.parent / 'assets' / 'conversations'
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def save_conversation(conversation_id: str, conversation_data: Dict) -> None:
    """Save a conversation to a JSON file"""
    file_path = STORAGE_DIR / f"{conversation_id}.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(conversation_data, f, indent=2, ensure_ascii=False)

def load_conversation(conversation_id: str) -> Optional[Dict]:
    """Load a conversation from a JSON file"""
    file_path = STORAGE_DIR / f"{conversation_id}.json"
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def load_all_conversations() -> Dict[str, Dict]:
    """Load all conversations from storage"""
    
    conversations = {}
    if STORAGE_DIR.exists():
        for file_path in STORAGE_DIR.glob("*.json"):
            conversation_id = file_path.stem
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    conversation_data = json.load(f)
                    
                    # Add timestamps if they don't exist (for backward compatibility)
                    if "created_at" not in conversation_data:
                        # Use file modification time as fallback
                        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        conversation_data["created_at"] = mod_time.isoformat()
                    
                    if "updated_at" not in conversation_data:
                        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        conversation_data["updated_at"] = mod_time.isoformat()
                    
                    conversations[conversation_id] = conversation_data
            except Exception as e:
                print(f"Error loading conversation {conversation_id}: {e}")
    return conversations

def delete_conversation(conversation_id: str) -> None:
    """Delete a conversation file"""
    file_path = STORAGE_DIR / f"{conversation_id}.json"
    if file_path.exists():
        file_path.unlink()

