# Just Travel - Hackathon Submission Guide

## 📝 Project Details

**Project Name:** Just Travel
**Tagline:** Just Travel: The multi-agent AI team for your perfect trip.
**Tracks:** Travel & Tourism, AI Agents, Best Use of Gemini

### 🔗 Project Links
*   **Public Project Link:** [Insert your GitHub Repo URL here]
    *   *Note: Since this is a full-stack application (Next.js + FastAPI) and not just a simple AI Studio prototype, you should submit your **GitHub Repository URL** here if you haven't deployed it to a public server. Judges will likely look at the video and the code.*
*   **Video Demo:** [Insert your YouTube/Vimeo Link here]
*   **GitHub Repo:** [Insert your GitHub Repo URL here]

### Elevator Pitch
"Just Travel is the first multi-agent AI travel companion that moves beyond simple chatbots. Instead of you juggling 20 tabs for flights, hotels, and blogs, our six specialized AI agents work together to research, cross-reference, and build a complete, logistics-proof itinerary in seconds—delivered as an offline-ready PWA."

### Short Description (1-sentence)
Just Travel is a multi-agent AI expert system that plans your entire trip—from finding hidden gems to booking flights—and presents it as a stunning, offline-capable PWA.

## Inspiration
Planning a trip used to mean having **20 tabs open**: Expedia for flights, TripAdvisor for hotels, TikTok for hidden gems, and Google Maps for logistics. Passwords, confirmations, and ideas were scattered everywhere with no clear source of truth.

But the biggest frustration was the lack of personalization. Standard booking sites simply don't care about who you are. **They don't respect your dietary restrictions**, constantly suggesting steakhouses to vegetarians or gluten-heavy spots to those with celiac disease. We realized that finding a restaurant that matches *both* your "romantic vibe" and your dietary needs is incredibly difficult. We wanted to build an AI that handles these nuanced, human constraints—centralizing the entire experience from leaving home to returning, just like a dedicated human agent would.

## What it does
Just Travel is an **AI-Native Travel Agency** on your phone.
1.  **Deep Profiling:** The `Profiler` agent interviews you to understand your psychological travel style.
2.  **Parallel Research:** It spins up three specialist agents simultaneously (`Pathfinder`, `TrendSpotter`, `Concierge`) to scan flight routes, social medial signals, and accommodations.
3.  **Intelligent Synthesis:** The `Optimizer` agent synthesizes all this data into a cohesive day-by-day itinerary, ensuring logic and flow.
4.  **Offline Companion:** The entire app is a **PWA**, meaning your itinerary is fully available offline.

## How we built it
We architected a specific **multi-agent system** to improve results and decrease hallucinations:
*   **Sequential & Parallel Workflows:** We implemented a "Sequential $\rightarrow$ Parallel $\rightarrow$ Sequential" structure. This deterministic workflow ensures the AI stays on track and doesn't get lost in open-ended conversation.
*   **The Models:** We leveraged **Google Gemini 1.5 Pro** for complex reasoning tasks and **Gemini 1.5 Flash** for high-speed, lower-latency operations.
*   **Asynchronous Architecture:** Using Python's `asyncio`, we handle multiple APIs and agents at the same time, drastically reducing wait times.
*   **Thought Signatures:** We utilized a "Thought Signature" attribute, forcing each agent to articulate its reasoning before acting. This significantly improved context retention and decision quality for every agent.
*   **State Management:** We integrated **Redis** to handle caching effectively, allowing us to manage the complex state of a multi-turn conversation without losing context.

## Challenges we ran into
*   **AI Interoperability:** Formatting the output of one AI agent to perfectly fit the strict input requirements of the next agent was one of our biggest hurdles.
*   **Hallucinations & Context:** mitigating AI hallucinations and managing the strict limits of context windows required constant tuning.
*   **Concurrency:** Managing asynchronous agents introduced complex race conditions and API rate limiting challenges that required a robust, resilient architecture.

## Accomplishments that we're proud of
*   **Advanced Cache Handling:** Successfully implementing Redis to manage state and cache, ensuring the app feels snappy.
*   **Structured Workflows:** designing a deterministic agent workflow that minimizes errors while maintaining flexibility.
*   **Offline Design:** Building a widely accessible PWA that looks and feels like a native app, complete with offline mode.

## What we learned
We gained deep insights into **Agentic AI patterns**. We learned that breaking tasks into specific sequential and parallel flows allows for much higher accuracy than a monolithic approach. We mastered the complexities of handling multiple asynchronous API calls and discovered how techniques like "Thought Signatures" can drastically improve an agent's performance. most importantly, we learned how to structure a system where the AI is a reliable tool, not just a creative writer.

## What's next for Just Travel
*   **Real Booking:** Moving from simulation to integration—implementing actual flight and hotel booking capabilities after user confirmation.
*   **AR Tour Guide:** Using the camera to overlay historical facts on landmarks.
*   **Group Planning:** Enabling collaborative itinerary building for groups.

---

## 🎬 Demo Video Script (2-3 Minutes)

**Scene 1: The Problem (0:00 - 0:30)**
*   **Visual:** Show a screen with 20 browser tabs open (Expedia, TripAdvisor, Google Maps, Blogs).
*   **Voiceover:** "Building a travel itinerary is broken. You have flight checkers, hotel finders, and blog posts, but nothing connects them. It takes hours."

**Scene 2: The Solution - Agent Orchestration (0:30 - 1:00)**
*   **Visual:** Switch to Just Travel. Show the "Terminal/Logs" view (if available) or the UI showing "Agents Active". Type: "Plan a romantic 5-day trip to Kyoto in Spring."
*   **Voiceover:** "Meet Just Travel. Instead of a single chatbot, it's a team of 6 specialized AI agents. Watch as the 'Pathfinder' looks for flights, while 'TrendSpotter' scans social media for hidden gems, and the 'Optimizer' checks the weather to ensure your outdoor activities aren't rained out."

**Scene 3: The "Wow" Moment (1:00 - 1:45)**
*   **Visual:** Show the generated itinerary appearing. Scroll through the days. Click on a specific day to see the details.
*   **Voiceover:** "The result isn't just text. It's a complete, logistics-proof itinerary. It knows that the cherry blossoms are blooming, it found a hotel under budget, and it booked a dinner spot that's trending on TikTok right now."

**Scene 4: PWA & Offline (1:45 - 2:15)**
*   **Visual:** Show the app on a mobile view (or actual phone). Turn on "Airplane Mode" and show the itinerary is still loadable.
*   **Voiceover:** "And because travel happens offline, Just Travel is a fully installable PWA. Your plan is cached on your device, so when you land in a new country without data, you still know exactly where to go."

**Scene 5: Architecture & Closing (2:15 - 2:30)**
*   **Visual:** Quick flash of the tech stack logos: Gemini, Next.js, FastAPI, Docker, Neo4j.
*   **Voiceover:** "Built with Google Gemini, Next.js, and Docker. This is Just Travel. Your journey, optimized."

---

## 🛠️ Deployment Instructions

*(Copy this into the README or "Instructions" field)*

### Quick Start (Docker)

Just Travel is fully containerized. To run it locally:

1.  **Clone the repo**
    ```bash
    git clone https://github.com/just-travel-app/repo.git
    cd just-travel-app
    ```

2.  **Configure Keys**
    ```bash
    cp .env.example .env
    # Add your GOOGLE_API_KEY in .env
    ```

3.  **Launch**
    ```bash
    docker-compose up --build
    ```

4.  **Explore**
    - Frontend: `http://localhost:3000`
    - Backend API: `http://localhost:8000`

### Cloud Deployment (Google Cloud)
For production deployment, we recommend **Cloud Run**.
Please refer to the detailed **[DEPLOY_GCP.md](./DEPLOY_GCP.md)** file in the repository for step-by-step instructions on deploying the backend, frontend, and setting up secrets.

### Tech Stack

-   **AI Core:** Google Gemini 1.5 Pro & Flash (via Google GenAI SDK)
-   **Backend:** Python FastAPI, Celery, Redis
-   **Frontend:** Next.js 14, TailwindCSS, Framer Motion
-   **Database:** Neo4j (Graph), SQLite (Application State)
-   **Infrastructure:** Docker, Docker Compose

---

## ✅ Submission Checklist

- [ ] **Public GitHub Repo:** Ensure the repo is public.
- [ ] **README.md:** Ensure the root README is clear (use the provided descriptions).
- [ ] **Video Upload:** Upload the demo video to YouTube/Vimeo.
- [ ] **Keys Removed:** Double-check that no API keys are hardcoded or in git history.
- [ ] **License:** Add an MIT License file.
