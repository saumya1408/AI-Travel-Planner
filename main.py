from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from typing import TypedDict, List

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for development; adjust for production

# Placeholder for external API initialization (e.g., for AI model)
def initialize_travel_api():
    """
    Initialize connection to a travel planning API or service.
    In the actual implementation, this would use an API key and specific model.
    """
    print("Travel API initialized (placeholder)")
    return None  # Replace with actual API client in private implementation

travel_api = initialize_travel_api()

# Define a simple state structure for managing trip data
class PlannerState(TypedDict):
    city: str
    days: int
    interests: List[str]
    itinerary: str

# Mock itinerary generation (simplified to avoid exposing proprietary logic)
def generate_mock_itinerary(state: PlannerState) -> dict:
    """
    Generate a sample itinerary for the given city and days.
    In the actual implementation, this uses an AI model to create detailed plans.
    """
    try:
        itinerary = f"Sample itinerary for {state['city']}:\n"
        for day in range(1, state['days'] + 1):
            itinerary += f"## Day {day}:\n"
            itinerary += f"- 10:00 AM: Visit a popular landmark in {state['city']}.\n"
            itinerary += f"- 12:00 PM: Lunch at a local restaurant.\n"
            itinerary += f"- 2:00 PM: Explore a cultural site.\n"
            itinerary += f"- 6:00 PM: Dinner and relax.\n"
        return {
            "itinerary": itinerary,
            "locations": [{"name": "Sample Landmark", "lat": 0.0, "lng": 0.0}],
            "language_guide": "Sample phrases in local language.",
            "transport_tips": "Use public transport for cost savings."
        }
    except Exception as e:
        print(f"Error generating itinerary: {str(e)}")
        return {
            "itinerary": "Error generating itinerary.",
            "locations": [],
            "language_guide": "",
            "transport_tips": ""
        }

@app.route("/")
def index():
    """Render the main web page."""
    return render_template("index.html")

@app.route("/generate_itinerary", methods=["POST"])
def generate_itinerary():
    """
    Endpoint to generate a travel itinerary based on user inputs.
    Expects JSON with city, days, and interests.
    """
    try:
        data = request.get_json()
        city = data.get("city", "").strip()
        days = int(data.get("days", 1))
        interests = data.get("interests", "").strip()

        if not city or not interests or days < 1 or days > 7:
            return jsonify({"error": "Invalid input parameters"}), 400

        # Initialize state
        state = {
            "city": city,
            "days": days,
            "interests": [interest.strip() for interest in interests.split(",")],
            "itinerary": ""
        }

        # Generate itinerary (using mock function for public repo)
        result = generate_mock_itinerary(state)
        return jsonify(result)
    except Exception as e:
        print(f"Error in generate_itinerary: {str(e)}")
        return jsonify({"error": "Failed to generate itinerary"}), 500

@app.route("/explain_activity", methods=["POST"])
def explain_activity():
    """
    Endpoint to provide a brief description of a travel activity or location.
    Expects JSON with activity name.
    """
    try:
        data = request.get_json()
        activity = data.get("activity", "").strip()
        if not activity:
            return jsonify({"error": "Activity name required"}), 400

        # Placeholder response (replace with AI-driven description in private code)
        description = f"{activity}: A popular attraction with unique features. Visit early to avoid crowds."
        return jsonify({"description": description})
    except Exception as e:
        print(f"Error in explain_activity: {str(e)}")
        return jsonify({"error": "Failed to explain activity"}), 500

@app.route("/export_pdf", methods=["POST"])
def export_pdf():
    """
    Endpoint to export the itinerary as a PDF.
    Expects JSON with itinerary text and city.
    """
    try:
        data = request.get_json()
        itinerary = data.get("itinerary", "")
        city = data.get("city", "Unknown City")

        if not itinerary:
            return jsonify({"error": "No itinerary provided"}), 400

        # Placeholder for PDF generation (simplified)
        # In actual implementation, use reportlab to create a PDF
        return jsonify({
            "pdf_data": "base64_encoded_pdf_string",  # Mock response
            "filename": f"{city}_itinerary.pdf"
        })
    except Exception as e:
        print(f"Error in export_pdf: {str(e)}")
        return jsonify({"error": "Failed to export PDF"}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
