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
        '''Proces user message and return adjustments with detailed explanation'''
        result=0
        return result
    
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
                print("material":  {mod["material"]}) 
                print("type": {mod["type"]})
                print("value": {mod["value"]} )
                print("start_date": {mod["start_date"]})
                print("end_date": {mod["end_date"]} )
                print("reason": {mode["reason"]})

if __name__ == "__main__":
    demo_chatbot()