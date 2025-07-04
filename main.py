

from flask import Flask, render_template, request, jsonify
import os
import requests
from typing import TypedDict, Annotated, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from flask_cors import CORS
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import io
import base64

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for simplicity; adjust for production

# Retrieve the Groq API key from environment variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

# Define the LLM with error handling
try:
    llm = ChatGroq(
        temperature=0,
        groq_api_key=GROQ_API_KEY,
        model_name="llama-3.3-70b-versatile"
    )
    print("ChatGroq initialized successfully")
except Exception as e:
    print(f"Error initializing ChatGroq: {e}")
    from langchain_groq import ChatGroq
    ChatGroq.model_rebuild()
    llm = ChatGroq(
        temperature=0,
        groq_api_key=GROQ_API_KEY,
        model_name="llama-3.3-70b-versatile"
    )

# Define the itinerary prompt with explicit multi-day and language guide structure
itinerary_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful travel assistant. Create a {days}-day trip itinerary for {city} based on the user's preferences:
- Interests: {interests}
- Travel Type: {travel_type}
- Budget: {budget}
- Travel Companions: {companions}
- Pace: {pace}
- Season: {season}
- Trip Vibe: {vibe}
- Food Preferences: {food_preferences}
- Must Include Spots: {must_include}
- Must Avoid Spots: {must_avoid}
- Include Breaks: {include_breaks}

For each day, provide a section labeled '## Day X:' (where X is the day number from 1 to {days}) with a bulleted list of activities, including specific times (starting at {start_time} and ending at {end_time}) and specific locations. 

For each activity, also suggest local transportation method (walk, metro, taxi, bus) and estimated travel time/cost.

Ensure each day's section is separated and complete. After all days, include a separate section labeled '## **Local Language Guide**' with exactly 5 useful phrases in the primary local language of {city} (e.g., greetings, thank you, directions, asking for help, and a common question). 

Also include a section '## **Local Transportation Tips**' with general advice about getting around {city}.

Return the response in plain text with clear section headers."""),
    ("human", "Create a {days}-day itinerary for my trip."),
])

# Activity explainer prompt
activity_explainer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a knowledgeable travel guide. Provide a brief, engaging 2-3 sentence explanation about the following place or activity. Include one interesting fact or tip."),
    ("human", "Tell me about: {activity}")
])

# Mock location database with approximate coordinates for common places
mock_locations_base = {
    "Ahmedabad": [
        {"id": "1", "name": "Sabarmati Ashram", "lat": 23.0606, "lng": 72.5809, "cost": "$5", "duration": "2 hours"},
        {"id": "2", "name": "Kankaria Lake", "lat": 23.0062, "lng": 72.6022, "cost": "$3", "duration": "1.5 hours"},
        {"id": "3", "name": "Manek Chowk", "lat": 23.0241, "lng": 72.5871, "cost": "$10", "duration": "2 hours"},
        {"id": "4", "name": "Adalaj Stepwell", "lat": 23.1159, "lng": 72.5814, "cost": "$2", "duration": "1 hour"},
        {"id": "5", "name": "Sidi Saiyyed Mosque", "lat": 23.0275, "lng": 72.5805, "cost": "Free", "duration": "45 minutes"},
    ],
    "Paris": [
        {"id": "6", "name": "Eiffel Tower", "lat": 48.8584, "lng": 2.2945, "cost": "$25", "duration": "2 hours"},
        {"id": "7", "name": "Louvre Museum", "lat": 48.8606, "lng": 2.3376, "cost": "$20", "duration": "3 hours"},
        {"id": "8", "name": "Notre-Dame", "lat": 48.8529, "lng": 2.3500, "cost": "Free", "duration": "1 hour"},
    ],
    "Kerala": [
        {"id": "9", "name": "Fort Kochi", "lat": 9.9617, "lng": 76.2427, "cost": "$8", "duration": "3 hours"},
        {"id": "10", "name": "Lulu Mall Kochi", "lat": 9.9677, "lng": 76.3050, "cost": "$15", "duration": "2 hours"},
        {"id": "11", "name": "Marine Drive Kochi", "lat": 9.9667, "lng": 76.2600, "cost": "Free", "duration": "1 hour"},
    ],
    "Mumbai": [
        {"id": "12", "name": "Marine Drive", "lat": 18.9388, "lng": 72.8355, "cost": "Free", "duration": "1.5 hours"},
        {"id": "13", "name": "Gateway of India", "lat": 18.9220, "lng": 72.8347, "cost": "Free", "duration": "1 hour"},
        {"id": "14", "name": "Colaba Causeway", "lat": 18.9185, "lng": 72.8328, "cost": "$12", "duration": "2 hours"},
    ]
}

# Mock activity descriptions
mock_activity_descriptions = {
    "1": "Sabarmati Ashram: A historic site where Mahatma Gandhi lived.",
    "2": "Kankaria Lake: A recreational spot with a lakefront promenade.",
    "3": "Manek Chowk: A bustling night market famous for Gujarati food.",
    "4": "Adalaj Stepwell: A 15th-century stepwell with intricate carvings.",
    "5": "Sidi Saiyyed Mosque: Known for its iconic jali work.",
    "6": "Eiffel Tower: Iconic landmark with stunning city views.",
    "7": "Louvre Museum: World-famous art museum.",
    "8": "Notre-Dame: Historic cathedral with Gothic architecture.",
    "9": "Fort Kochi: Historic area with colonial charm.",
    "10": "Lulu Mall Kochi: Large shopping mall with diverse stores.",
    "11": "Marine Drive Kochi: Scenic waterfront promenade.",
    "12": "Marine Drive: Iconic Mumbai promenade along the sea.",
    "13": "Gateway of India: Historic monument and tourist spot.",
    "14": "Colaba Causeway: Vibrant shopping and food street.",
}

class PlannerState(TypedDict):
    messages: Annotated[List[HumanMessage | AIMessage], "The messages in the conversation"]
    city: str
    days: int
    interests: List[str]
    start_time: str
    end_time: str
    travel_type: str
    budget: str
    companions: str
    pace: str
    season: str
    vibe: str
    food_preferences: List[str]
    must_include: str
    must_avoid: str
    include_breaks: bool
    itinerary: str
    language_guide: str

def input_city(city: str, days: int, state: PlannerState) -> PlannerState:
    return {
        **state,
        "city": city,
        "days": days,
        "messages": state["messages"] + [HumanMessage(content=city)],
    }

def input_interests(interests: str, state: PlannerState) -> PlannerState:
    return {
        **state,
        "interests": [interest.strip() for interest in interests.split(",")],
        "messages": state["messages"] + [HumanMessage(content=interests)],
    }

def input_times(start_time: str, end_time: str, state: PlannerState) -> PlannerState:
    return {
        **state,
        "start_time": start_time,
        "end_time": end_time,
        "messages": state["messages"] + [HumanMessage(content=f"Start time: {start_time}, End time: {end_time}")],
    }

def input_personalization(data: dict, state: PlannerState) -> PlannerState:
    return {
        **state,
        "travel_type": data.get("travel_type", ""),
        "budget": data.get("budget", "Mid"),
        "companions": data.get("companions", ""),
        "pace": data.get("pace", "Medium"),
        "season": data.get("season", ""),
        "vibe": data.get("vibe", ""),
        "food_preferences": [pref.strip() for pref in data.get("food_preferences", "").split(",") if pref.strip()],
        "must_include": data.get("must_include", ""),
        "must_avoid": data.get("must_avoid", ""),
        "include_breaks": data.get("include_breaks", False),
        "messages": state["messages"] + [HumanMessage(content=str(data))],
    }

def extract_locations_from_itinerary(itinerary: str, city: str) -> List[dict]:
    locations = []
    base_locations = mock_locations_base.get(city, [])
    itinerary_lines = itinerary.split("\n")
    seen_locations = set()

    for line in itinerary_lines:
        line = line.strip()
        if "*" in line and any(loc["name"] in line for loc in base_locations):
            for loc in base_locations:
                if loc["name"] in line and loc["name"] not in seen_locations:
                    locations.append(loc)
                    seen_locations.add(loc["name"])
                    break
    return locations if locations else base_locations[:3]  # Return up to 3 default locations if none matched

def create_itinerary(state: PlannerState) -> dict:
    try:
        print(f"Generating itinerary for {state['city']} with {state['days']} days")
        
        response = llm.invoke(itinerary_prompt.format_messages(
            city=state["city"],
            days=state["days"],
            interests=", ".join(state["interests"]),
            start_time=state["start_time"],
            end_time=state["end_time"],
            travel_type=state["travel_type"] or "General",
            budget=state["budget"],
            companions=state["companions"] or "None",
            pace=state["pace"],
            season=state["season"] or "Any",
            vibe=state["vibe"] or "General",
            food_preferences=", ".join(state["food_preferences"]) or "None",
            must_include=state["must_include"] or "None",
            must_avoid=state["must_avoid"] or "None",
            include_breaks="Yes" if state["include_breaks"] else "No"
        ))
        itinerary_text = response.content
        print(f"Raw LLM response: {itinerary_text}")  # Debug the full response

        # Split into days and language guide with improved parsing
        itinerary_lines = itinerary_text.split("\n")
        day_sections = []
        current_day = []
        capturing_language_guide = False
        capturing_transport_tips = False

        for line in itinerary_lines:
            line = line.strip()
            if line.startswith("## Day") and line[6:].strip().split(":")[0].isdigit():
                if current_day:
                    day_sections.append("\n".join(current_day))
                current_day = [line.replace("## ", "")]
            elif line == "## **Local Language Guide**":
                if current_day:
                    day_sections.append("\n".join(current_day))
                current_day = []
                capturing_language_guide = True
                capturing_transport_tips = False
            elif line == "## **Local Transportation Tips**":
                if current_day and capturing_language_guide:
                    day_sections.append("\n".join(current_day))
                current_day = []
                capturing_language_guide = False
                capturing_transport_tips = True
            elif (capturing_language_guide or capturing_transport_tips) and line:
                current_day.append(line)
            elif current_day and line:
                current_day.append(line)

        if current_day:
            day_sections.append("\n".join(current_day))

        # Assign sections
        itinerary = "\n".join(day_sections[:-2]) if len(day_sections) > 2 else "\n".join(day_sections[:-1]) if len(day_sections) > 1 else "\n".join(day_sections)
        language_guide = day_sections[-2] if len(day_sections) > 1 and "## **Local Language Guide**" in itinerary_text else ""
        transport_tips = day_sections[-1] if len(day_sections) > 0 and "## **Local Transportation Tips**" in itinerary_text else ""

        print(f"Parsed itinerary: {itinerary}")
        print(f"Parsed language guide: {language_guide}")
        print(f"Parsed transport tips: {transport_tips}")

        # Extract locations from itinerary
        locations = extract_locations_from_itinerary(itinerary, state["city"])

        state["itinerary"] = itinerary
        state["language_guide"] = language_guide
        state["messages"] += [AIMessage(content=itinerary_text)]
        
        return {
            "itinerary": itinerary if itinerary else "No itinerary generated.",
            "locations": locations,
            "language_guide": language_guide if language_guide else "No language guide available.",
            "transport_tips": transport_tips if transport_tips else "No transportation tips available."
        }
    except Exception as e:
        print(f"Error in create_itinerary: {str(e)}")
        return {
            "itinerary": "Error generating itinerary.",
            "locations": mock_locations_base.get(state["city"], []),
            "language_guide": "Error generating language guide.",
            "transport_tips": "Error generating transportation tips."
        }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate_itinerary", methods=["POST"])
def generate_itinerary():
    try:
        data = request.get_json()
        city = data.get("city", "").strip()
        days = int(data.get("days", 1))
        interests = data.get("interests", "").strip()
        start_time = data.get("start_time", "10:00").strip()
        end_time = data.get("end_time", "22:00").strip()

        if not city or not interests or not start_time or not end_time or days < 1 or days > 7:
            return jsonify({"error": "City, interests, start time, end time, and valid days (1-7) are required"}), 400

        # Initialize state
        state = {
            "messages": [],
            "city": "",
            "days": 1,
            "interests": [],
            "start_time": "",
            "end_time": "",
            "travel_type": "",
            "budget": "Mid",
            "companions": "",
            "pace": "Medium",
            "season": "",
            "vibe": "",
            "food_preferences": [],
            "must_include": "",
            "must_avoid": "",
            "include_breaks": False,
            "itinerary": "",
            "language_guide": ""
        }

        # Process inputs
        state = input_city(city, days, state)
        state = input_interests(interests, state)
        state = input_times(start_time, end_time, state)
        state = input_personalization(data, state)

        # Generate itinerary
        result = create_itinerary(state)
        print("Generated itinerary response:", result)
        return jsonify(result)
    except Exception as e:
        print(f"Error in generate_itinerary: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/explain_activity", methods=["POST"])
def explain_activity():
    try:
        data = request.get_json()
        activity_name = data.get("activity", "").strip()
        if not activity_name:
            return jsonify({"error": "Activity name is required"}), 400
        
        # Use AI to explain the activity
        response = llm.invoke(activity_explainer_prompt.format_messages(activity=activity_name))
        description = response.content
        
        return jsonify({"description": description})
    except Exception as e:
        print(f"Error in explain_activity: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/export_pdf", methods=["POST"])
def export_pdf():
    try:
        data = request.get_json()
        itinerary_text = data.get("itinerary", "")
        city = data.get("city", "Unknown City")
        days = data.get("days", 1)
        
        if not itinerary_text:
            return jsonify({"error": "No itinerary to export"}), 400
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = Paragraph(f"Travel Itinerary for {city} - {days} Days", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Content
        for line in itinerary_text.split('\n'):
            if line.strip():
                if line.startswith('Day'):
                    p = Paragraph(line, styles['Heading2'])
                else:
                    p = Paragraph(line, styles['Normal'])
                story.append(p)
                story.append(Spacer(1, 6))
        
        doc.build(story)
        buffer.seek(0)
        
        # Encode to base64
        pdf_data = base64.b64encode(buffer.getvalue()).decode()
        
        return jsonify({"pdf_data": pdf_data, "filename": f"{city}_itinerary.pdf"})
    except Exception as e:
        print(f"Error in export_pdf: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


