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
        '''Process user message and return adjustments with detailed explanation'''
        self.conversation_history.append({'role':'user', 'content':message})

        conversation_context = ""
        if len(self.conversation_history) > 1:
            conversation_context = "Previous conversation:\n"
            for msg in self.conversation_history[:-1]: # For all previous messages from user AND agent
                conversation_context += f"{msg['role'].capitalize()}: {msg['content']}\n" # role: User/Agent
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
            - "Big UFC fight this Saturday" --> Increase rooms to 95%, security +40%, cleaning +25%
            - "Convention Monday morning" --> Cleaning +30% (10am-2pm), rooms +85%
            - "Pool party season starting" --> Cleaning +50% afternoons, security +20%

            Return ONLY valid JSON in this format:
            {{
                "response": "Natural language explanation of the changes and reasoning",
                "modifications": [
                    {{
                        "metric": "rooms|cleaning|security",
                        "type": "percentage|absolute|set",
                        "value": number,
                        "start_date": "YYYY-MM-DD",
                        "end_date": "YYYY-MM-DD",
                        "reason": "brief operational reason"
                    }}]
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

            ## Extract JSON

            # For checking if response is expected format
            text = response.content[0].text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            
            if json_match:
                # Parse json string into Python Dict
                result = json.loads(json_match.group())

                # Convo history is a list of dicts
                self.conversation_history.append({"role":"assistant", "content":result['response']})
        
                return result # if result does not exist then function continues to fallback response
            
        except Exception as e:
            print(f"Agent error: {e}")
            error_response = {
                "response": "There was an error during your last message. Please try again.",
                "modifications": []
            }
            self.conversation_history.append({"role":"assistant", "content":result['response']})
            return error_response
        
        # Fallback response
        fallback = {
             "response": "I didn't return the expected JSON format. Please try rephrasing your request.",
            "modifications": []
        }
        self.conversation_history.append({"role":"assistant", "content":result['response']})
        return fallback


def demo_chatbot():
    '''Interactive chat with agent without connection to forecast'''
    # Check for API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("Error: api key not set!")
        return
    
    agent = ForecastAgent()

    print("AGENT DEMO")

    while True:
        message = input("You: ")

        result = agent.process_message(message)
        print(f"Bot: {result['response']}")

        # Since the demo is not connected to a forecast, we'll retrieve the would-be forecast modifs:
        if result['modifications']:
            print("Would-be Modifications")
            for mod in result['modifications']:
                print("metric":  {mod["metric"]}) 
                print("type": {mod["type"]})
                print("value": {mod["value"]} )
                print("start_date": {mod["start_date"]})
                print("end_date": {mod["end_date"]} )
                print("reason": {mode["reason"]})

if __name__ == "__main__":
    demo_chatbot()