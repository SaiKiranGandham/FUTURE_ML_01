import streamlit as st
import time
from chatbot import CustomerSupportChatbot
from utils.conversation_manager import ConversationManager

# Initialize chatbot and conversation manager
@st.cache_resource
def initialize_chatbot():
    return CustomerSupportChatbot()

@st.cache_resource
def initialize_conversation_manager():
    return ConversationManager()

def main():
    st.set_page_config(
        page_title="AI Customer Support Chatbot",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 AI Customer Support Chatbot")
    st.markdown("Welcome! I'm here to help you with your questions. Feel free to ask about billing, technical support, product information, or any other concerns.")
    
    # Initialize components
    chatbot = initialize_chatbot()
    conversation_manager = initialize_conversation_manager()
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.conversation_id = conversation_manager.create_conversation()
    
    if "typing" not in st.session_state:
        st.session_state.typing = False
    
    # Display conversation history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "metadata" in message and message["metadata"]:
                    with st.expander("Bot Analysis", expanded=False):
                        metadata = message["metadata"]
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Intent:** {metadata.get('intent', 'Unknown')}")
                            st.write(f"**Confidence:** {metadata.get('confidence', 0):.2f}")
                        with col2:
                            if metadata.get('entities'):
                                st.write("**Entities Found:**")
                                for entity in metadata['entities']:
                                    st.write(f"- {entity['type']}: {entity['value']}")
    
    # Show typing indicator
    if st.session_state.typing:
        with st.chat_message("assistant"):
            st.markdown("🤔 Thinking...")
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Show typing indicator
        st.session_state.typing = True
        st.rerun()
    
    # Process bot response if there's a new user message
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        user_message = st.session_state.messages[-1]["content"]
        
        # Get bot response
        with st.spinner("Processing your request..."):
            try:
                response_data = chatbot.get_response(
                    user_message, 
                    st.session_state.conversation_id,
                    st.session_state.messages[:-1]  # Previous messages for context
                )
                
                # Add response to conversation history
                conversation_manager.add_message(
                    st.session_state.conversation_id,
                    "user",
                    user_message
                )
                conversation_manager.add_message(
                    st.session_state.conversation_id,
                    "assistant",
                    response_data["response"]
                )
                
                # Add bot response to chat history
                bot_message = {
                    "role": "assistant",
                    "content": response_data["response"],
                    "metadata": {
                        "intent": response_data.get("intent"),
                        "confidence": response_data.get("confidence"),
                        "entities": response_data.get("entities", []),
                        "source": response_data.get("source", "AI")
                    }
                }
                st.session_state.messages.append(bot_message)
                
            except Exception as e:
                error_message = {
                    "role": "assistant",
                    "content": f"I apologize, but I'm experiencing technical difficulties. Please try again in a moment. Error: {str(e)}",
                    "metadata": {"source": "Error"}
                }
                st.session_state.messages.append(error_message)
        
        # Remove typing indicator
        st.session_state.typing = False
        st.rerun()
    
    # Sidebar with additional features
    with st.sidebar:
        st.header("Chat Options")
        
        if st.button("🗑️ Clear Conversation"):
            st.session_state.messages = []
            st.session_state.conversation_id = conversation_manager.create_conversation()
            st.rerun()
        
        st.markdown("---")
        st.header("Quick Actions")
        
        quick_actions = [
            "What are your business hours?",
            "How can I track my order?",
            "I need help with billing",
            "Technical support needed",
            "Product information request"
        ]
        
        for action in quick_actions:
            if st.button(action, key=f"quick_{action}"):
                st.session_state.messages.append({"role": "user", "content": action})
                st.rerun()
        
        st.markdown("---")
        st.header("Bot Capabilities")
        st.markdown("""
        **I can help you with:**
        - 📋 Order tracking and status
        - 💳 Billing and payment issues
        - 🔧 Technical support
        - 📦 Product information
        - 🕒 Business hours and contact info
        - 📞 Escalation to human agents
        """)
        
        st.markdown("---")
        st.header("Conversation Stats")
        total_messages = len(st.session_state.messages)
        user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
        bot_messages = len([m for m in st.session_state.messages if m["role"] == "assistant"])
        
        st.metric("Total Messages", total_messages)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Your Messages", user_messages)
        with col2:
            st.metric("Bot Responses", bot_messages)

if __name__ == "__main__":
    main()
