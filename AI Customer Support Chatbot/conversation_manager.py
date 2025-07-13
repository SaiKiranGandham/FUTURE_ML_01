import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class ConversationManager:
    def __init__(self):
        self.conversations = {}
        self.max_conversation_age = timedelta(hours=24)  # Auto-cleanup after 24 hours
    
    def create_conversation(self) -> str:
        """Create a new conversation and return its ID"""
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = {
            "id": conversation_id,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "messages": [],
            "context": {},
            "user_info": {},
            "satisfaction_score": None,
            "escalated": False,
            "resolved": False
        }
        return conversation_id
    
    def add_message(self, conversation_id: str, role: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Add a message to the conversation"""
        if conversation_id not in self.conversations:
            return False
        
        message = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }
        
        self.conversations[conversation_id]["messages"].append(message)
        self.conversations[conversation_id]["last_activity"] = datetime.now()
        
        return True
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get conversation by ID"""
        return self.conversations.get(conversation_id)
    
    def get_messages(self, conversation_id: str, limit: Optional[int] = None) -> List[Dict]:
        """Get messages from a conversation"""
        if conversation_id not in self.conversations:
            return []
        
        messages = self.conversations[conversation_id]["messages"]
        if limit:
            return messages[-limit:]
        return messages
    
    def update_context(self, conversation_id: str, context_updates: Dict) -> bool:
        """Update conversation context"""
        if conversation_id not in self.conversations:
            return False
        
        self.conversations[conversation_id]["context"].update(context_updates)
        self.conversations[conversation_id]["last_activity"] = datetime.now()
        return True
    
    def set_user_info(self, conversation_id: str, user_info: Dict) -> bool:
        """Set user information for the conversation"""
        if conversation_id not in self.conversations:
            return False
        
        self.conversations[conversation_id]["user_info"].update(user_info)
        return True
    
    def escalate_conversation(self, conversation_id: str, reason: str = None) -> bool:
        """Mark conversation as escalated to human agent"""
        if conversation_id not in self.conversations:
            return False
        
        self.conversations[conversation_id]["escalated"] = True
        self.conversations[conversation_id]["escalation_reason"] = reason
        self.conversations[conversation_id]["escalation_time"] = datetime.now()
        
        # Add system message about escalation
        self.add_message(
            conversation_id,
            "system",
            f"Conversation escalated to human agent. Reason: {reason or 'User request'}",
            {"type": "escalation", "reason": reason}
        )
        
        return True
    
    def resolve_conversation(self, conversation_id: str, satisfaction_score: Optional[int] = None) -> bool:
        """Mark conversation as resolved"""
        if conversation_id not in self.conversations:
            return False
        
        self.conversations[conversation_id]["resolved"] = True
        self.conversations[conversation_id]["resolved_at"] = datetime.now()
        
        if satisfaction_score is not None:
            self.conversations[conversation_id]["satisfaction_score"] = satisfaction_score
        
        return True
    
    def get_conversation_summary(self, conversation_id: str) -> Optional[Dict]:
        """Get a summary of the conversation"""
        if conversation_id not in self.conversations:
            return None
        
        conversation = self.conversations[conversation_id]
        messages = conversation["messages"]
        
        # Count messages by role
        message_counts = {}
        for message in messages:
            role = message["role"]
            message_counts[role] = message_counts.get(role, 0) + 1
        
        # Extract intents from bot messages
        intents = []
        for message in messages:
            if message["role"] == "assistant" and "metadata" in message:
                intent = message["metadata"].get("intent")
                if intent and intent not in intents:
                    intents.append(intent)
        
        # Calculate conversation duration
        duration = None
        if messages:
            start_time = messages[0]["timestamp"]
            end_time = messages[-1]["timestamp"]
            duration = (end_time - start_time).total_seconds()
        
        return {
            "conversation_id": conversation_id,
            "created_at": conversation["created_at"],
            "last_activity": conversation["last_activity"],
            "duration_seconds": duration,
            "message_count": len(messages),
            "message_counts": message_counts,
            "intents_discussed": intents,
            "escalated": conversation["escalated"],
            "resolved": conversation["resolved"],
            "satisfaction_score": conversation["satisfaction_score"],
            "user_info": conversation["user_info"]
        }
    
    def cleanup_old_conversations(self) -> int:
        """Remove conversations older than max_conversation_age"""
        current_time = datetime.now()
        to_remove = []
        
        for conv_id, conversation in self.conversations.items():
            if current_time - conversation["last_activity"] > self.max_conversation_age:
                to_remove.append(conv_id)
        
        for conv_id in to_remove:
            del self.conversations[conv_id]
        
        return len(to_remove)
    
    def get_active_conversations(self) -> List[Dict]:
        """Get all active conversations (not resolved and recent)"""
        current_time = datetime.now()
        active = []
        
        for conversation in self.conversations.values():
            if (not conversation["resolved"] and 
                current_time - conversation["last_activity"] < self.max_conversation_age):
                active.append(self.get_conversation_summary(conversation["id"]))
        
        return active
    
    def export_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Export conversation data for analysis or handoff"""
        if conversation_id not in self.conversations:
            return None
        
        conversation = self.conversations[conversation_id].copy()
        
        # Convert datetime objects to ISO format for JSON serialization
        conversation["created_at"] = conversation["created_at"].isoformat()
        conversation["last_activity"] = conversation["last_activity"].isoformat()
        
        if "escalation_time" in conversation:
            conversation["escalation_time"] = conversation["escalation_time"].isoformat()
        
        if "resolved_at" in conversation:
            conversation["resolved_at"] = conversation["resolved_at"].isoformat()
        
        for message in conversation["messages"]:
            message["timestamp"] = message["timestamp"].isoformat()
        
        return conversation
    
    def search_conversations(self, query: str, limit: int = 10) -> List[Dict]:
        """Search conversations by message content"""
        results = []
        query_lower = query.lower()
        
        for conversation in self.conversations.values():
            # Search in message content
            found = False
            for message in conversation["messages"]:
                if query_lower in message["content"].lower():
                    found = True
                    break
            
            if found:
                results.append(self.get_conversation_summary(conversation["id"]))
                if len(results) >= limit:
                    break
        
        return results
