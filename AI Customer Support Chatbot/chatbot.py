import os
import json
from openai import OpenAI
from intent_classifier import IntentClassifier
from entity_extractor import EntityExtractor
from faq_handler import FAQHandler

class CustomerSupportChatbot:
    def __init__(self):
        # Initialize OpenAI client
        self.openai_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "your-openai-api-key")
        )
        
        # Initialize components
        self.intent_classifier = IntentClassifier(self.openai_client)
        self.entity_extractor = EntityExtractor(self.openai_client)
        self.faq_handler = FAQHandler()
        
        # Bot personality and guidelines
        self.system_prompt = """
        You are a professional customer support representative for a technology company. 
        You are helpful, empathetic, and solution-oriented. Follow these guidelines:
        
        1. Always be polite and professional
        2. Show empathy for customer concerns
        3. Provide clear, actionable solutions
        4. If you cannot resolve an issue, offer to escalate to a human agent
        5. Ask clarifying questions when needed
        6. Keep responses concise but comprehensive
        7. Use a friendly but professional tone
        
        Available support areas:
        - Billing and payments
        - Technical support
        - Product information
        - Order tracking and shipping
        - Account management
        - General inquiries
        
        If a customer asks about something outside your knowledge, acknowledge it honestly 
        and offer to connect them with the appropriate specialist.
        """
    
    def get_response(self, user_message, conversation_id, conversation_history=None):
        """
        Process user message and generate appropriate response
        """
        try:
            # Step 1: Extract entities from user message
            entities = self.entity_extractor.extract_entities(user_message)
            
            # Step 2: Classify intent
            intent_result = self.intent_classifier.classify_intent(user_message)
            intent = intent_result.get("intent", "general_inquiry")
            confidence = intent_result.get("confidence", 0.0)
            
            # Step 3: Check if this is an FAQ
            faq_response = self.faq_handler.get_faq_response(user_message, intent)
            if faq_response:
                return {
                    "response": faq_response,
                    "intent": intent,
                    "confidence": confidence,
                    "entities": entities,
                    "source": "FAQ"
                }
            
            # Step 4: Generate contextual response using GPT
            response = self._generate_gpt_response(
                user_message, intent, entities, conversation_history
            )
            
            return {
                "response": response,
                "intent": intent,
                "confidence": confidence,
                "entities": entities,
                "source": "AI"
            }
            
        except Exception as e:
            return {
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again in a moment, or feel free to contact our human support team for immediate assistance.",
                "intent": "error",
                "confidence": 0.0,
                "entities": [],
                "source": "Error"
            }
    
    def _generate_gpt_response(self, user_message, intent, entities, conversation_history):
        """
        Generate response using OpenAI GPT with context
        """
        # Build context from conversation history
        context_messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add recent conversation history for context
        if conversation_history:
            for msg in conversation_history[-6:]:  # Last 6 messages for context
                context_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add current user message with intent and entity context
        enhanced_message = f"""
        User message: {user_message}
        
        Detected intent: {intent}
        Extracted entities: {json.dumps(entities, indent=2) if entities else "None"}
        
        Please provide a helpful response as a customer support representative.
        """
        
        context_messages.append({
            "role": "user",
            "content": enhanced_message
        })
        
        # Generate response
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=context_messages,
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def escalate_to_human(self, issue_description, conversation_id):
        """
        Handle escalation to human agent
        """
        escalation_message = f"""
        I understand this requires specialized attention. I'm escalating your case to one of our human specialists who will be better equipped to help you.
        
        Your case details have been noted:
        - Issue: {issue_description}
        - Conversation ID: {conversation_id}
        
        A human agent will contact you within 2 business hours. In the meantime, you can also reach our support team directly at support@company.com or call 1-800-SUPPORT.
        
        Is there anything else I can help you with while you wait?
        """
        return escalation_message
