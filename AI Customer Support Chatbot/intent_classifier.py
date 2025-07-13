import json
import os

class IntentClassifier:
    def __init__(self, openai_client):
        self.openai_client = openai_client
        
        # Load predefined intents
        self.intents = self._load_intents()
    
    def _load_intents(self):
        """Load intent definitions from JSON file"""
        try:
            with open("data/intents.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default intents if file not found
            return {
                "billing": {
                    "description": "Questions about billing, payments, charges, refunds",
                    "examples": ["billing issue", "payment problem", "refund request", "charge inquiry"]
                },
                "technical_support": {
                    "description": "Technical problems, troubleshooting, setup issues",
                    "examples": ["not working", "error message", "setup help", "technical problem"]
                },
                "product_info": {
                    "description": "Questions about products, features, specifications",
                    "examples": ["product details", "features", "specifications", "compatibility"]
                },
                "order_tracking": {
                    "description": "Order status, shipping, delivery questions",
                    "examples": ["track order", "shipping status", "delivery time", "order status"]
                },
                "account_management": {
                    "description": "Account settings, password, profile changes",
                    "examples": ["change password", "account settings", "profile update", "login issues"]
                },
                "general_inquiry": {
                    "description": "General questions, business hours, contact information",
                    "examples": ["business hours", "contact info", "general question", "help"]
                },
                "complaint": {
                    "description": "Customer complaints, dissatisfaction, issues",
                    "examples": ["complaint", "unhappy", "disappointed", "problem with service"]
                }
            }
    
    def classify_intent(self, user_message):
        """
        Classify user intent using OpenAI GPT
        """
        try:
            # Create intent classification prompt
            intent_list = list(self.intents.keys())
            intent_descriptions = {
                intent: data["description"] 
                for intent, data in self.intents.items()
            }
            
            prompt = f"""
            Classify the following customer message into one of these intents and provide a confidence score.
            
            Available intents:
            {json.dumps(intent_descriptions, indent=2)}
            
            Customer message: "{user_message}"
            
            Please respond with JSON in this exact format:
            {{
                "intent": "intent_name",
                "confidence": 0.95,
                "reasoning": "Brief explanation of why this intent was chosen"
            }}
            
            Choose the most appropriate intent from the list above.
            """
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert intent classification system for customer support. Analyze customer messages and classify them accurately."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate intent exists
            if result["intent"] not in self.intents:
                result["intent"] = "general_inquiry"
                result["confidence"] = 0.5
            
            # Ensure confidence is between 0 and 1
            result["confidence"] = max(0.0, min(1.0, result["confidence"]))
            
            return result
            
        except Exception as e:
            print(f"Intent classification error: {e}")
            return {
                "intent": "general_inquiry",
                "confidence": 0.5,
                "reasoning": "Fallback due to classification error"
            }
    
    def get_intent_info(self, intent):
        """Get detailed information about an intent"""
        return self.intents.get(intent, {})
    
    def add_intent(self, intent_name, description, examples):
        """Add a new intent to the classifier"""
        self.intents[intent_name] = {
            "description": description,
            "examples": examples
        }
        
        # Save updated intents to file
        try:
            with open("data/intents.json", "w") as f:
                json.dump(self.intents, f, indent=2)
        except Exception as e:
            print(f"Error saving intents: {e}")
