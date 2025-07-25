<!--
  _____                           _ _   _               _            _             
 |_   _|                         (_) | (_)             | |          | |            
   | | ___ _ __ _ __   ___  _ __  _| |_ _  ___ ___   __| | ___  _ __| |_ ___  ___  
   | |/ _ \ '__| '_ \ / _ \| '_ \| | __| |/ __/ _ \ / _` |/ _ \| '__| __/ _ \/ __| 
   | |  __/ |  | |_) | (_) | | | | | |_| | (_| (_) | (_| | (_) | |  | ||  __/\__ \ 
   \_/\___|_|  | .__/ \___/|_| |_|_|\__|_|\___\___/ \__,_|\___/|_|   \__\___||___/ 
                | |                                                                 
                |_|                                                                 
-->

# ✈️ Travel Itinerary Planner

<p align="center">
  <img src="https://drive.google.com/uc?id=1LBFe4FP5CEsEZwI06s2i2e_2gyVZ06WB" alt="UI Screenshot" width="700" />
</p>

AI-powered web application that transforms **your dream destinations and interests into a perfectly curated day-by-day itinerary**, complete with optimal timings, maps, local culture tips, and dining recommendations – all within seconds.

> “It’s like having a local travel expert in your pocket.”

---

## 📜 Table of Contents
1. [High-Level Overview](#high-level-overview)
2. [Live](#live)
3. [Sample Video](#sample-video)
4. [Architecture](#architecture)
5. [Key Features](#key-features)
6. [Technology Stack](#technology-stack)
7. [Folder Structure](#folder-structure)
8. [Environment Configuration](#environment-configuration)
9. [API Contracts](#api-contracts)
10. [Extensibility Guide](#extensibility-guide)
11. [Contributing](#contributing)
12. [License](#license)

---

## High-Level Overview
The **Travel Itinerary Planner** leverages natural-language generation to craft personalised travel plans.

> **Why did we build this?** Planning a trip often involves juggling dozens of browser tabs—from blog posts and Google Maps to restaurant reviews and subway schedules. We wanted a single hub that understands your preferences and instantly assembles a **logically ordered, culturally rich, and time-efficient** itinerary. By fusing a powerful LLM with real-time geo data, our tool acts as your always-on local guide—saving hours of research while uncovering hidden gems you might otherwise miss. Users specify:

* Destination city or region
* Trip duration (½-day, 1-day, multi-day)
* Personal interests (e.g., art, food, adventure, nightlife)
* Budget preference

A language-model-powered backend (Groq API) analyses the inputs, combines them with live location metadata, then produces:

| Output | Description |
| ------ | ----------- |
| Full schedule | Time-boxed activities with optimal travel times |
| Interactive map | Visual route with distance & ETA |
| Restaurant picks | Trendy & local-favourite eateries |
| Cultural insights | Etiquette, tipping, dress code |
| PDF export | Shareable offline copy |

---

## Live
Access the application here: [Travel Itinerary Planner Live](https://travel-planner-ns7552-daee.onrender.com)

## Sample Video
Watch a short demo of the itinerary planner in action: <a href="https://drive.google.com/file/d/1HETg6D73frIP4TOGp-rKdZ29E7binOMF/view?usp=sharing" target="_blank">Sample Video</a>

---

## Architecture
```mermaid
graph TD
  subgraph "Browser (Client)"
    UI["Tailwind + AlpineJS<br/>Responsive UI"]
  end

  subgraph "Flask API (Backend)"
    API["/api/itinerary"]
    SVC["ItineraryService"]
  end

  subgraph "External Services"
    LLM["Groq LLM"]
  end

  UI -->|JSON| API
  API --> SVC
  SVC -->|Prompt & Context| LLM
  LLM -->|Structured Itinerary| SVC
  SVC --> API
  API -->|REST JSON| UI
```

### Sequence Diagram
```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant BE as Backend
    participant LLM as Groq API

    U->>FE: Enter preferences
    FE->>BE: POST /api/itinerary
    BE->>LLM: GPT-style prompt
    LLM-->>BE: JSON itinerary
    BE-->>FE: 200 OK, itinerary JSON
    FE-->>U: Render timeline & map
```

---

## Key Features
* ✨ **AI-Generated Schedules** – Tailored agendas that maximise sightseeing while minimising transit.
* 🗺 **Dynamic Map** – Leaflet.js renders markers & polylines for each stop.
* 🍽 **Foodie Focus** – Curated cafés, street-food stalls, and Michelin gems.
* 📱 **PWA Ready** – Offline support and “Add to Home Screen”.
* 🌐 **Multilingual** – Outputs available in 20+ languages.
* 🔒 **Secure by Default** – Secrets handled via environment variables; no keys stored client-side.

---

## Technology Stack
| Layer | Tech |
| ----- | ---- |
| Front-End | HTML5, Tailwind CSS, Alpine.js |
| Back-End | Python 3.11, Flask, pydantic |
| AI Engine | Groq LLM (gpt-xlarge-1024) |
| Mapping | Leaflet.js, OpenStreetMap Tiles |
| Styling | DaisyUI theme, HeroIcons |
| Tooling | Pre-commit, Ruff, Black |

---

## Folder Structure
```text
travel-itinerary-ai/
├── backend/
│   ├── main.py          # Flask entry-point
│   ├── services/
│   │   └── itinerary.py # LLM prompt orchestration
│   ├── schemas/
│   │   └── itinerary.py # pydantic models
│   └── config/
│       └── config.json  # (optional) local secrets
├── frontend/
│   ├── index.html
│   ├── assets/
│   └── js/
└── README.md            # ← you are here
```

---

## Environment Configuration
The app relies on two critical variables:

| Variable | Purpose |
| -------- | ------- |
| `GROQ_API_KEY` | Auth token for Groq language model |
| `FLASK_ENV` | `development` or `production` |

1. Create a `.env` file **or** set them in your hosting provider’s dashboard.
2. Keep `backend/config/config.json` out of version control – `.gitignore` already does this.

---

## API Contracts
### POST `/api/itinerary`
| Field | Type | Description |
| ----- | ---- | ----------- |
| `destination` | string | City or region name |
| `days` | int | Number of days (1-14) |
| `interests` | list[string] | e.g. `["culture", "food"]` |
| `budget` | string | `low`, `mid`, `high` |

**Response 200**
```jsonc
{
  "city": "Paris",
  "days": 3,
  "itinerary": [
    {
      "day": 1,
      "schedule": [
        { "time": "09:00", "activity": "Louvre Museum", "type": "sight" },
        { "time": "13:00", "activity": "Lunch at Chez Janou", "type": "food" },
        { "time": "15:00", "activity": "Seine River Cruise", "type": "experience" }
      ]
    }
  ]
}
```

---

## Extensibility Guide
1. **Swap LLM provider** – Implement an `LLMClient` interface under `backend/services/llm.py`.
2. **Add weather awareness** – Integrate Open-Meteo API in `ItineraryService` for season-specific plans.
3. **Persistent user accounts** – Plug in Firebase Auth or Supabase.
4. **CI/CD** – Combine GitHub Actions with Railway triggers for zero-downtime deploys.

---

## Contributing
We welcome pull requests for **bug fixes, new prompts, or UI polish**. Before submitting:
1. Create a descriptive issue and discuss design scope.
2. Adhere to existing code style (Ruff & Black handle formatting).
3. Ensure all unit tests pass (`pytest`).
4. Write clear commit messages.

---

## License
Distributed under the **MIT License**. See `LICENSE` for more information.

---

<p align="center">
  <strong>Bon voyage & happy exploring! 🌍</strong>
</p>
