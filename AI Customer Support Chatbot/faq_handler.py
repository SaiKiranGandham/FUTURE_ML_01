import json
import os
from difflib import SequenceMatcher

class FAQHandler:
    def __init__(self):
        self.faqs = self._load_faqs()
        self.similarity_threshold = 0.6
    
    def _load_faqs(self):
        """Load FAQ data from JSON file"""
        try:
            with open("data/faqs.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default FAQs if file not found
            return self._get_default_faqs()
    
    def _get_default_faqs(self):
        """Default FAQ responses"""
        return {
            "business_hours": {
                "questions": [
                    "what are your business hours",
                    "when are you open",
                    "what time do you open",
                    "what time do you close",
                    "hours of operation"
                ],
                "answer": "Our customer support is available Monday through Friday from 9:00 AM to 6:00 PM EST, and Saturday from 10:00 AM to 4:00 PM EST. We're closed on Sundays and major holidays. For urgent issues outside these hours, please email support@company.com.",
                "category": "general"
            },
            "contact_info": {
                "questions": [
                    "how can i contact you",
                    "contact information",
                    "phone number",
                    "email address",
                    "how to reach support"
                ],
                "answer": "You can reach our support team in several ways:\n• Phone: 1-800-SUPPORT (1-800-787-7678)\n• Email: support@company.com\n• Live Chat: Available on our website\n• This chatbot: Available 24/7 for immediate assistance",
                "category": "general"
            },
            "order_tracking": {
                "questions": [
                    "how to track my order",
                    "track order",
                    "order status",
                    "where is my order",
                    "shipping status"
                ],
                "answer": "To track your order:\n1. Log into your account on our website\n2. Go to 'My Orders' section\n3. Click on the order you want to track\n\nAlternatively, you can use the tracking number sent to your email. If you need help finding your tracking information, please provide your order number and I'll assist you.",
                "category": "orders"
            },
            "return_policy": {
                "questions": [
                    "return policy",
                    "how to return",
                    "refund policy",
                    "can i return this",
                    "exchange policy"
                ],
                "answer": "Our return policy allows returns within 30 days of purchase for most items:\n• Items must be in original condition and packaging\n• Original receipt or order confirmation required\n• Some items (personalized, digital downloads) are not returnable\n• Refunds typically process within 5-7 business days\n\nTo start a return, visit our returns portal or contact our support team.",
                "category": "returns"
            },
            "payment_methods": {
                "questions": [
                    "what payment methods do you accept",
                    "payment options",
                    "can i pay with",
                    "accepted payment types"
                ],
                "answer": "We accept the following payment methods:\n• Credit Cards: Visa, MasterCard, American Express, Discover\n• Debit Cards\n• PayPal\n• Apple Pay\n• Google Pay\n• Bank transfers (for large orders)\n\nAll payments are processed securely using industry-standard encryption.",
                "category": "billing"
            },
            "shipping_info": {
                "questions": [
                    "shipping information",
                    "how long does shipping take",
                    "shipping cost",
                    "delivery time",
                    "shipping options"
                ],
                "answer": "Shipping options and timeframes:\n• Standard Shipping: 5-7 business days ($5.99)\n• Express Shipping: 2-3 business days ($12.99)\n• Next Day Delivery: 1 business day ($19.99)\n• Free shipping on orders over $50\n\nShipping times may vary during peak seasons or due to weather conditions.",
                "category": "shipping"
            },
            "password_reset": {
                "questions": [
                    "forgot password",
                    "reset password",
                    "can't login",
                    "password reset",
                    "login problems"
                ],
                "answer": "To reset your password:\n1. Go to our login page\n2. Click 'Forgot Password?'\n3. Enter your email address\n4. Check your email for reset instructions\n5. Follow the link and create a new password\n\nIf you don't receive the email, check your spam folder or contact support for assistance.",
                "category": "account"
            }
        }
    
    def get_faq_response(self, user_message, intent=None):
        """
        Find matching FAQ response for user message
        """
        user_message_lower = user_message.lower()
        best_match = None
        best_score = 0
        
        for faq_id, faq_data in self.faqs.items():
            for question in faq_data["questions"]:
                # Calculate similarity using SequenceMatcher
                similarity = SequenceMatcher(None, user_message_lower, question.lower()).ratio()
                
                # Also check for keyword matches
                keyword_score = self._calculate_keyword_score(user_message_lower, question.lower())
                
                # Combined score
                combined_score = (similarity * 0.7) + (keyword_score * 0.3)
                
                if combined_score > best_score and combined_score >= self.similarity_threshold:
                    best_score = combined_score
                    best_match = faq_data
        
        if best_match:
            return best_match["answer"]
        
        return None
    
    def _calculate_keyword_score(self, user_message, faq_question):
        """Calculate keyword matching score"""
        user_words = set(user_message.split())
        faq_words = set(faq_question.split())
        
        # Remove common stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "i", "you", "he", "she", "it", "we", "they", "my", "your", "his", "her", "its", "our", "their"}
        
        user_words = user_words - stop_words
        faq_words = faq_words - stop_words
        
        if not faq_words:
            return 0
        
        # Calculate intersection score
        intersection = user_words.intersection(faq_words)
        return len(intersection) / len(faq_words)
    
    def search_faqs(self, query, category=None):
        """
        Search FAQs by query and optionally filter by category
        """
        results = []
        
        for faq_id, faq_data in self.faqs.items():
            if category and faq_data.get("category") != category:
                continue
            
            # Check if query matches any question
            for question in faq_data["questions"]:
                if query.lower() in question.lower():
                    results.append({
                        "id": faq_id,
                        "question": question,
                        "answer": faq_data["answer"],
                        "category": faq_data.get("category", "general")
                    })
                    break
        
        return results
    
    def get_categories(self):
        """Get all FAQ categories"""
        categories = set()
        for faq_data in self.faqs.values():
            categories.add(faq_data.get("category", "general"))
        return sorted(list(categories))
    
    def add_faq(self, faq_id, questions, answer, category="general"):
        """Add a new FAQ"""
        self.faqs[faq_id] = {
            "questions": questions,
            "answer": answer,
            "category": category
        }
        
        # Save updated FAQs to file
        try:
            with open("data/faqs.json", "w") as f:
                json.dump(self.faqs, f, indent=2)
        except Exception as e:
            print(f"Error saving FAQs: {e}")
    
    def update_faq(self, faq_id, questions=None, answer=None, category=None):
        """Update an existing FAQ"""
        if faq_id in self.faqs:
            if questions is not None:
                self.faqs[faq_id]["questions"] = questions
            if answer is not None:
                self.faqs[faq_id]["answer"] = answer
            if category is not None:
                self.faqs[faq_id]["category"] = category
            
            # Save updated FAQs to file
            try:
                with open("data/faqs.json", "w") as f:
                    json.dump(self.faqs, f, indent=2)
            except Exception as e:
                print(f"Error saving FAQs: {e}")
