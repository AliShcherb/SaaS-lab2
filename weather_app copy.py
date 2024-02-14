from flask import Flask, request, jsonify
import datetime
import requests

app = Flask(__name__)

api_key = ""
my_api_token = ""
openai_token = ""

def generate_clothing_recommendation(location, date, weather_data):
    prompt = f"What would you advise me to wear if I am in {location}, on {date}, and the weather is said to be like this: temperature {weather_data.get('temp', 'N/A')}°C, wind {weather_data.get('windspeed', 'N/A')} kph, humidity {weather_data.get('humidity', 'N/A')}%, description {weather_data.get('description', 'N/A')}?"

    headers = {
        "Authorization": f"Bearer {openai_token}"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    if response.status_code == 200:
        response_json = response.json()
        advice = response_json.get("choices", [{}])[0].get("message", {}).get("content", "Sorry, I couldn't get any advice for you.")
        return advice.strip()
    else:
        return "Failed to retrieve advice from ChatGPT."

def get_weather(location, date):
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/{date}"
    params = {
        "key": api_key,
        "unitGroup": "metric",
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        weather_data = data.get('days', [{}])[0]
        recommendation = generate_clothing_recommendation(location, date, weather_data)
        return {
            "temp_c": weather_data.get("temp"),
            "wind_kph": weather_data.get("windspeed"),
            "pressure_mb": weather_data.get("pressure"),
            "humidity": weather_data.get("humidity"),
            "description": weather_data.get("description"),
            "recommendation": recommendation
        }
    else:
        return {"error": f"Failed to retrieve weather data. Status code: {response.status_code}"}

@app.route('/weather', methods=['POST'])
def weather():
    data = request.get_json()

    required_fields = ['token', 'requester_name', 'location', 'date']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing one or more required fields"}), 400

    if data['token'] != my_api_token:
        return jsonify({"error": "Invalid token"}), 403

    location = data['location']
    date = data['date']

    weather_data = get_weather(location, date)

    if "error" in weather_data:
        return jsonify(weather_data), 500

    response = {
        "requester_name": data['requester_name'],
        "timestamp": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "location": location,
        "date": date,
        "weather": weather_data
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8000', debug=True)
