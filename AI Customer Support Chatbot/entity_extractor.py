import json
import re
from datetime import datetime

class EntityExtractor:
    def __init__(self, openai_client):
        self.openai_client = openai_client
        
        # Define regex patterns for common entities
        self.patterns = {
            "order_number": r'\b(?:order|order\s*#|order\s*number)[:\s]*([A-Z0-9]{6,})\b',
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            "product_id": r'\b(?:product|item|sku)[:\s]*([A-Z0-9]{3,})\b',
            "amount": r'\$?\d+(?:\.\d{2})?',
            "date": r'\b(?:today|tomorrow|yesterday|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b'
        }
    
    def extract_entities(self, text):
        """
        Extract entities using both regex patterns and OpenAI
        """
        entities = []
        
        # First, extract using regex patterns
        regex_entities = self._extract_with_regex(text)
        entities.extend(regex_entities)
        
        # Then, use OpenAI for more complex entity extraction
        try:
            ai_entities = self._extract_with_ai(text)
            entities.extend(ai_entities)
        except Exception as e:
            print(f"AI entity extraction error: {e}")
        
        # Remove duplicates and return
        return self._deduplicate_entities(entities)
    
    def _extract_with_regex(self, text):
        """Extract entities using regex patterns"""
        entities = []
        
        for entity_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if entity_type in ["order_number", "product_id"]:
                    value = match.group(1) if match.groups() else match.group(0)
                else:
                    value = match.group(0)
                
                entities.append({
                    "type": entity_type,
                    "value": value.strip(),
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.9,
                    "source": "regex"
                })
        
        return entities
    
    def _extract_with_ai(self, text):
        """Extract entities using OpenAI GPT"""
        prompt = f"""
        Extract relevant entities from this customer support message. Focus on:
        - Product names or models
        - Account numbers or IDs
        - Transaction amounts
        - Dates and times
        - Customer names
        - Technical terms or error codes
        - Location information
        
        Customer message: "{text}"
        
        Respond with JSON in this format:
        {{
            "entities": [
                {{
                    "type": "entity_type",
                    "value": "extracted_value",
                    "confidence": 0.95
                }}
            ]
        }}
        
        Only extract entities that are clearly present in the text. If no entities are found, return an empty entities array.
        """
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert entity extraction system for customer support. Extract relevant entities accurately from customer messages."
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
        ai_entities = []
        
        for entity in result.get("entities", []):
            ai_entities.append({
                "type": entity["type"],
                "value": entity["value"],
                "confidence": min(1.0, max(0.0, entity.get("confidence", 0.8))),
                "source": "ai"
            })
        
        return ai_entities
    
    def _deduplicate_entities(self, entities):
        """Remove duplicate entities, preferring higher confidence scores"""
        unique_entities = {}
        
        for entity in entities:
            key = f"{entity['type']}_{entity['value'].lower()}"
            
            if key not in unique_entities or entity['confidence'] > unique_entities[key]['confidence']:
                unique_entities[key] = entity
        
        return list(unique_entities.values())
    
    def validate_entity(self, entity_type, value):
        """Validate extracted entity values"""
        validators = {
            "email": self._validate_email,
            "phone": self._validate_phone,
            "order_number": self._validate_order_number,
            "amount": self._validate_amount
        }
        
        validator = validators.get(entity_type)
        if validator:
            return validator(value)
        
        return True  # Default to valid for unknown types
    
    def _validate_email(self, email):
        """Validate email format"""
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _validate_phone(self, phone):
        """Validate phone number format"""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        return len(digits) in [10, 11]  # US phone numbers
    
    def _validate_order_number(self, order_number):
        """Validate order number format"""
        return len(order_number) >= 6 and order_number.isalnum()
    
    def _validate_amount(self, amount):
        """Validate monetary amount"""
        try:
            float(amount.replace('$', ''))
            return True
        except ValueError:
            return False
