# Story Generator: Workflow & Feature Analysis

This document provides a breakdown of how the application works under the hood, along with a comprehensive list of features currently implemented. Please review the **Feature List** section below and indicate which features you would like to have removed.

## 🔄 How it Works (Workflow)

The application is built using **Streamlit** for the frontend user interface and connects to a locally running **Ollama** instance (running the LLaMA 3 model) for its AI capabilities.

1. **User Input Phase ([app.py](file:///c:/Users/ashok/OneDrive/Desktop/Main-Project/Story_Generator/app.py))**: 
   The user interacts with the Streamlit UI, providing inputs through various tabs (Generate, Characters, Plot Builder, etc.) and adjusting settings in the sidebar (Length, Creativity/Temperature, Language, Templates).
2. **Prompt Construction**:
   When the user triggers an action (like "Generate Story"), the app gathers all relevant session state variables, sidebar settings, and explicit inputs to construct a highly specific structural prompt.
3. **AI Execution ([engine.py](file:///c:/Users/ashok/OneDrive/Desktop/Main-Project/Story_Generator/engine.py) -> [ask_llama](file:///c:/Users/ashok/OneDrive/Desktop/Main-Project/Story_Generator/engine.py#32-55))**:
   The prompt is sent via an HTTP POST request to the local Ollama API endpoint (`http://localhost:11434/api/generate`). 
4. **Display & Post-Processing**:
   The AI's text response is returned to the Streamlit app. It is then rendered in the UI. From here, the user can trigger secondary post-processing features on the text, such as text-to-speech conversion, statistical analysis, or exporting the text into various file formats.
5. **Storage**:
   If the user chooses to save a story, the text and its metadata are written to a local SQLite database (`story_library.db`), from which it can be continually queried in the "Library" tab.

---

## 📋 Comprehensive Feature List

Here is every feature currently built into the application. **Please review this list and let me know which ones you would like removed.**

### 1. Core Generation Settings (Sidebar)
- **Story Length Control**: Short, Medium, Long (with paragraph-enforced constraints).
- **Creativity Level (Temperature)**: Slider to adjust LLaMA's predictability vs. wildness.
- **Output Language Selection**: Translates the output into English, Tamil, Hindi, Spanish, French, German, or Japanese.
- **Quick Templates**: Presets like "Hollywood Action", "Anime Episode", or "Horror Short" that hardcode specific genres/moods.
- **Clear All Stories**: Immediately drops all unsaved stories from the active session.

### 2. Main Generation Capabilities (Generate Tab)
- **Primary Generator**: Generates the main story based on Genre, Main Characters, Mood, and Format (Short Story, Screenplay, Dialogue, etc.).
- **Story Continuation**: Appends a continuation to the currently generated story by feeding the existing output back to the AI.
- **Live Editing**: Text areas allowing users to manually tweak the AI's output before saving or exporting.

### 3. Post-Generation Analysis & Tools
- **Statistical Analysis**: Calculates Word count, Reading time, Sentence count, and Top character name mentions.
- **AI Critic Rating**: Rates the story out of 10 on Creativity, Emotion, and Plot.
- **Emotional Breakdown**: Determines the dominant emotions and provides percentage breakdowns.
- **Voice Narration (gTTS)**: Converts the story text into a downloadable `.mp3` audio file using Google Text-to-Speech.
- **Poster Generation**: Generates an SD (Stable Diffusion) image prompt from the story and fetches an AI-generated image URL via Pollinations.ai.
- **Document Exporter**: Downloads the story as PDF, DOCX, TXT, or Markdown formats.

### 4. Helper Tools & Builders (Tabs)
- **Character Builder**: Dedicated tab to pre-define a character (Name, Age, Personality, Background) that automatically gets deeply injected into prompts on the Generate tab.
- **Genre Recommendation**: A tool where users can describe a raw "idea", and the AI suggests 3-5 suitable genres.
- **Plot Builder**: Generates a standard Hollywood 3-Act structure breakdown based on a central premise, genre, and characters.

### 5. Story Library
- **SQLite Database**: Persistent local storage for saved stories.
- **Library Management**: View past stories, regenerate their audio/PDF exports directly from the library, or delete them.
