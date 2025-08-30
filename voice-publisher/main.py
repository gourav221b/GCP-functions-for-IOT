import functions_framework
import json
import google.generativeai as genai
from google.cloud import pubsub_v1
from flask import jsonify
import os

PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
 
pubsub_publisher = pubsub_v1.PublisherClient()
topic_path = pubsub_publisher.topic_path(PROJECT_ID, 'rectangle-commands') # update this with the topic id you create

# Get the API key from a secure environment variable
api_key = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

@functions_framework.http
def process_voice_command(request):
    """Processes a voice command, parses it with Gemini, and publishes to Pub/Sub."""
    # Set up CORS headers for the web app
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    if request.method == 'OPTIONS':
        return ('', 204, headers)
    
    try:
        request_json = request.get_json(silent=True)
        text_command = request_json.get('command_text')
        
        if not text_command:
            return jsonify({'error': 'No command_text provided'}), 400

        # The prompt to guide Gemini's output
        prompt = (
            f"Parse the following command for a 2D animated rectangle. "
            f"Output a JSON array of simple movement commands: 'up', 'down', 'left', 'right'. "
            f"For 'jump', use 'up' and 'down'. For 'move left', use 'left'. For 'twice', double the command. "
            f"Example 1: 'jump twice' -> {{\"commands\": [\"up\", \"down\", \"up\", \"down\"]}} "
            f"Example 2: 'move right' -> {{\"commands\": [\"right\"]}} "
            f"Command to parse: '{text_command}'"
        )

        response = model.generate_content(prompt)
        
        # The API returns the JSON inside a block, so we'll need to parse it
        gemini_output_str = response.text.replace('`', '').replace('json', '').strip()
        commands = json.loads(gemini_output_str)['commands']
        
        # Publish each command individually to Pub/Sub
        for command in commands:
            message_data = json.dumps({'command': command}).encode('utf-8')
            pubsub_publisher.publish(topic_path, message_data)

        return jsonify({'status': 'commands published', 'commands': commands}), 200, headers

    except Exception as e:
        return jsonify({'error': str(e)}), 500, headers
