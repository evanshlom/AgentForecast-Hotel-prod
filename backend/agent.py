import os
from datetime import datetime, timedelta
import anthropic
import json
import re

class ForecastAgent:
    def __init__(self):
        self.client = anthropic.Client(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        self.conversation_history = []
    
    def process_message(self, message, current_forecast=None):
        """Process user message and return adjustments with detailed explanation"""
        self.conversation_history.append({"role": "user", "content": message})
        
        # Build conversation context
        conversation_context = ""
        if len(self.conversation_history) > 1:
            conversation_context = "Previous conversation:\n"
            for msg in self.conversation_history[:-1]:  # All except the current message
                conversation_context += f"{msg['role'].capitalize()}: {msg['content']}\n"
            conversation_context += "\nIf there were previous modifications discussed, acknowledge them with 'In addition to previous changes to the forecast, ' before your response.\n\n"
        
        prompt = f"""You are an AI assistant for Wynn Resort Las Vegas operations forecasting. 
    Analyze the user's message about hotel operations and provide recommendations.

    {conversation_context}User message: "{message}"
    Today's date: {datetime.now().date()}
    Forecast period: Next 168 hours (7 days)

    Parse the user's intent for modifications to:
    - rooms (occupancy percentage)
    - cleaning (staff needed)  
    - security (staff needed)

    Examples:
    - "Big UFC fight this Saturday" → Increase rooms to 95%, security +40%, cleaning +25%
    - "Convention Monday morning" → Cleaning +30% (10am-2pm), rooms 85%+
    - "Pool party season starting" → Cleaning +50% afternoons, security +20%

    Return ONLY valid JSON in this format:
    {{
        "response": "Natural language explanation of the changes and reasoning",
        "modifications": [
            {{
                "material": "rooms|cleaning|security",
                "type": "percentage|absolute|set",
                "value": number,
                "start_date": "YYYY-MM-DD",
                "end_date": "YYYY-MM-DD",
                "reason": "brief operational reason"
            }}
        ]
    }}

    If no modifications needed, return empty modifications array."""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Extract JSON from response
            text = response.content[0].text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group())
                
                # Convert material to metric for compatibility
                for mod in result.get('modifications', []):
                    if 'material' in mod:
                        mod['metric'] = mod.pop('material')
                    
                    # Convert date strings to date objects
                    if 'start_date' in mod:
                        mod['start_date'] = datetime.strptime(mod['start_date'], '%Y-%m-%d').date()
                    if 'end_date' in mod:
                        mod['end_date'] = datetime.strptime(mod['end_date'], '%Y-%m-%d').date()
                
                self.conversation_history.append({"role": "assistant", "content": result['response']})
                return result
         
        except Exception as e:
            print(f"Agent error: {e}")
        
        # Fallback response
        fallback = {
            "response": "I understand you're asking about Wynn resort operations. Could you be more specific about what changes you'd like to make to the forecast?",
            "modifications": []
        }
        self.conversation_history.append({"role": "assistant", "content": fallback['response']})
        return fallback

# Demo function for standalone testing
def demo_agent():
    """Interactive chat with the agent"""
    # Check for API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("Error: ANTHROPIC_API_KEY not set!")
        print("Please run: export ANTHROPIC_API_KEY='your-key-here'")
        return
    
    agent = ForecastAgent()
    
    print("Wynn Resort Forecast Agent - Interactive Demo")
    print("=" * 60)
    print("Chat with the agent about resort operations.")
    print("Examples: 'Big UFC fight this Saturday', 'Convention next Monday'")
    print("Type 'quit' to exit\n")
    
    while True:
        try:
            message = input("You: ").strip()
            
            if message.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not message:
                continue
            
            result = agent.process_message(message)
            print(f"\nAgent: {result['response']}")
            
            if result['modifications']:
                print("\nPlanned Adjustments:")
                for mod in result['modifications']:
                    print(f"  - {mod['metric']}: {mod['type']} by {mod['value']}")
                    print(f"    Period: {mod['start_date']} to {mod['end_date']}")
                    if 'time_range' in mod:
                        print(f"    Hours: {mod['time_range']}")
                    print(f"    Reason: {mod['reason']}")
            
            print()  # Extra line for readability
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    demo_agent()