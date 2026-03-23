import streamlit as st
import urllib.parse
from engine import (
    ask_llama, create_pdf, create_docx, create_txt,
    recommend_genre, text_to_audio, GTTS_LANG_CODES,
    save_story, get_all_stories, delete_story,
    rate_story, analyze_story_stats, generate_plot
)

# ─────────────────────────────────────────────────────────────────────────────
# Page config & CSS
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Story & Script Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.4rem; font-weight: 800;
        background: linear-gradient(90deg, #e052a0, #f15c41);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header { color: #888; font-size: 1rem; margin-bottom: 1.5rem; }
    .stTextArea textarea { font-family: 'Courier New', monospace; font-size: 0.93rem; }
    div[data-testid="stDownloadButton"] > button { border-radius: 6px; font-size: 0.85rem; }
    section[data-testid="stSidebar"] { min-width: 300px; }
    .metric-box {
        background: #1e1e2e; padding: 10px; border-radius: 8px; text-align: center;
        border: 1px solid #333; margin-bottom: 10px;
    }
    .metric-val { font-size: 1.5rem; font-weight: bold; color: #e052a0; }
    .metric-label { font-size: 0.8rem; color: #999; text-transform: uppercase; }
</style>
<style>
    /* Hide the sidebar collapse control button */
    [data-testid="collapsedControl"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🎬 AI Story Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Powered by LLaMA 3 via Ollama — generate, analyse, and export cinematic stories.</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Session state defaults
# ─────────────────────────────────────────────────────────────────────────────
defaults = {
    "history":          [],
    "char_name":        "",
    "char_age":         "",
    "char_personality": "",
    "char_background":  "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar – Settings
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    st.divider()

    length_option = st.selectbox(
        "📏 Story Length",
        ["Short (~200 words)", "Medium (~500 words)", "Long (~1000 words)"],
    )
    length_mapping = {
        "Short (~200 words)": (200, 500, "Write 3 to 4 paragraphs. Keep it concise but complete."),
        "Medium (~500 words)": (500, 1500, "Write at least 6 to 8 long, detailed paragraphs. Take time to describe the setting, character motives, and build the scene steadily without rushing."),
        "Long (~1000 words)": (1000, 3000, "Write a very long, highly detailed story containing at least 15 to 20 long paragraphs. You must use extensive descriptions, prolonged dialogue scenes, and elaborate pacing. Thoroughly explore the characters' thoughts and heavily detail their actions. Do not rush the ending!"),
    }
    target_words, max_tokens, length_instruction = length_mapping[length_option]

    temperature = st.slider(
        "🌡️ Creativity Level", min_value=0.0, max_value=1.0, value=0.7, step=0.1,
        help="Low = logical & structured. High = wild & creative.",
    )
    st.divider()

    language = st.selectbox(
        "🌐 Output Language",
        ["English", "Tamil", "Hindi"],
    )
    st.divider()

    st.markdown("**Session**")
    if st.button("🗑️ Clear All Stories", use_container_width=True):
        st.session_state.history = []
        st.rerun()

    st.divider()
    st.caption("AI Story Studio v5.0\nBuilt with Streamlit + Ollama (LLaMA 3)")

# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab_gen, tab_char, tab_genre, tab_plot, tab_lib = st.tabs([
    "✨ Generate", "🧑 Characters", "💡 Ideas", "🗺️ Plot Builder", "📚 Library"
])

# ══════════════════════════ TAB 1 : Generate ══════════════════════════════════
with tab_gen:
    tpl_genre, tpl_mood, tpl_format = None, None, None

    GENRES = ["Romance", "Horror", "Sci-Fi", "Fantasy", "Comedy", "Thriller", "Action", "Mystery"]
    MOODS  = ["Happy", "Sad", "Dark", "Inspirational", "Suspenseful", "Mysterious", "Romantic"]
    FORMATS = ["Short Story", "Movie Scene", "Dialogue"]

    col1, col2 = st.columns(2)
    with col1:
        genre      = st.selectbox("🎭 Genre", GENRES,
                                  index=GENRES.index(tpl_genre) if tpl_genre else 0)
        characters = st.text_input("🧑‍🤝‍🧑 Main Characters (comma separated)", "Arjun, Maya")
    with col2:
        mood         = st.selectbox("🎨 Mood", MOODS,
                                    index=MOODS.index(tpl_mood) if tpl_mood else 0)
        content_type = st.selectbox("📝 Format", FORMATS,
                                    index=FORMATS.index(tpl_format) if tpl_format else 0)

    # Character builder injection banner
    char_block = ""
    if st.session_state.get("char_name"):
        char_block = (
            f"\nCharacter Details:\n"
            f"  Name: {st.session_state.char_name}\n"
            f"  Age: {st.session_state.char_age}\n"
            f"  Personality: {st.session_state.char_personality}\n"
            f"  Background: {st.session_state.char_background}\n"
        )
        st.success(f"🧑 Character profile active: **{st.session_state.char_name}**")

    lang_instruction = (
        "" if language == "English"
        else f"\nIMPORTANT: Write the entire story in **{language}** language only.\n"
    )

    st.divider()
    if st.button("✨ Generate Story", type="primary", use_container_width=True):
        prompt = f"""You are an expert creative writer and screenwriter.

Task: Write a {content_type.lower()}.
Genre: {genre}
Mood: {mood}
Main Characters: {characters}{char_block}
Target length: STRICTLY over {target_words} words.
{length_instruction}
{lang_instruction}
Instructions:
- For "Movie Scene", "Screenplay", or "Anime Episode" use standard screenplay formatting.
- Write engaging, emotionally resonant content with meaningful dialogue.
- Return ONLY the story/scene text — no preamble or meta-commentary.
"""
        with st.spinner("⏳ Generating your story… this may take a moment."):
            output = ask_llama(prompt, temperature=temperature, max_tokens=max_tokens)

        if output.startswith("ERROR:"):
            st.error(output.replace("ERROR: ", ""))
        else:
            st.session_state.history.append({
                "output": output,
                "genre": genre, "characters": characters,
                "content_type": content_type, "language": language,
            })

    # ── Results ───────────────────────────────────────────────────────────────
    if st.session_state.history:
        st.divider()
        st.subheader("📖 Generated Stories")

    for idx, entry in enumerate(reversed(st.session_state.history)):
        result_num = len(st.session_state.history) - idx
        raw_output = entry["output"]
        g    = entry.get("genre", "")
        ch   = entry.get("characters", "")
        ct   = entry.get("content_type", "")
        lang = entry.get("language", "English")

        with st.expander(f"✨ Result {result_num} — {ct} | {g} | {lang}", expanded=(idx == 0)):

            edited = st.text_area(
                "✏️ Edit your story before downloading or analyzing:",
                value=raw_output, height=350, key=f"edit_{idx}",
            )

            # ── Action row 1: Continue / Analyze / Save / Copy ─────────────
            a1, a2, a3, a4 = st.columns(4)
            
            # Continue Story
            if a1.button("➕ Continue", key=f"cont_{idx}", use_container_width=True):
                cont_prompt = f"""You are an expert creative writer.
Continue this {ct.lower()} naturally from where it left off.
Genre: {g} | Characters: {ch}
Write the next portion (strictly at least {target_words} words).
{length_instruction}
Expand on details and do not rush.
{'Write in ' + lang + ' language.' if lang != 'English' else ''}
Return ONLY the continuation — no preamble.

--- EXISTING STORY ---
{edited}
--- CONTINUE ---
"""
                with st.spinner("⏳ Continuing story…"):
                    cont = ask_llama(cont_prompt, temperature=temperature, max_tokens=max_tokens)
                if cont.startswith("ERROR:"):
                    st.error(cont.replace("ERROR: ", ""))
                else:
                    combined = edited + "\n\n---\n\n" + cont
                    st.session_state.history.append({
                        "output": combined, "genre": g,
                        "characters": ch, "content_type": ct, "language": lang,
                    })
                    st.rerun()

            # Analyze (Stats, Emotions, Rating)
            analyze_holder = st.empty()
            if a2.button("📊 Analyze", key=f"analyze_{idx}", use_container_width=True):
                with analyze_holder.container():
                    st.markdown("### 📊 AI Story Analysis")
                    with st.spinner("Calculating statistics and analyzing semantics..."):
                        
                        # Stats
                        stats = analyze_story_stats(edited)
                        s1, s2, s3 = st.columns(3)
                        s1.markdown(f'<div class="metric-box"><div class="metric-val">{stats["word_count"]}</div><div class="metric-label">Words</div></div>', unsafe_allow_html=True)
                        s2.markdown(f'<div class="metric-box"><div class="metric-val">{stats["reading_time"]}m</div><div class="metric-label">Read Time</div></div>', unsafe_allow_html=True)
                        s3.markdown(f'<div class="metric-box"><div class="metric-val">{stats["sentence_count"]}</div><div class="metric-label">Sentences</div></div>', unsafe_allow_html=True)
                        
                        st.write("**Top Name Mentions:** " + ", ".join([f"{n} ({c})" for n,c in stats["top_mentions"]]))
                        
                        st.divider()
                        
                        st.markdown("**🌟 AI Critic Rating**")
                        rating_res = rate_story(edited)
                        st.info(rating_res)

                    if st.button("Close Analysis", key=f"close_an_{idx}"):
                        pass # Streamlit handles the rerun and clears the holder

            # Save to Library
            if a3.button("💾 Save", key=f"save_{idx}", use_container_width=True):
                title = f"{ct} — {g} #{result_num}"
                save_story(title, edited, genre=g, characters=ch,
                           content_type=ct, language=lang)
                st.success(f"✅ Saved to Story Library as: **{title}**")

            # Copy story
            if a4.button("📋 Copy", key=f"copy_{idx}", use_container_width=True):
                st.code(edited, language="")
                st.caption("Select all and copy (Ctrl+A then Ctrl+C).")

            # ── Voice Narration ───────────────────────────────────────────
            st.markdown("**🔊 Voice Narration**")
            if st.button("🎙️ Generate Audio", key=f"audio_{idx}", use_container_width=False):
                lang_code = GTTS_LANG_CODES.get(lang, "en")
                try:
                    with st.spinner("🔊 Generating narration… (This might take a minute)"):
                        audio_bytes = text_to_audio(edited, lang_code=lang_code)
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button(
                        "⬇️ Download Audio (.mp3)", data=audio_bytes,
                        file_name=f"story_{result_num}.mp3", mime="audio/mpeg",
                        key=f"dl_audio_{idx}",
                    )
                except Exception as e:
                    st.error(f"Audio generation failed: {e}\n\nMake sure you have an internet connection.")

            st.divider()

            # ── Download row ──────────────────────────────────────────────
            st.markdown("**⬇️ Export Document**")
            dl1, dl2, dl3 = st.columns(3)

            pdf_path = create_pdf(edited, genre=g, characters=ch, content_type=ct)
            with open(pdf_path, "rb") as f:
                dl1.download_button("📄 PDF", data=f, file_name=f"story_{result_num}.pdf",
                                    mime="application/pdf", key=f"pdf_{idx}",
                                    use_container_width=True)
            try:
                docx_path = create_docx(edited, genre=g, characters=ch, content_type=ct)
                with open(docx_path, "rb") as f:
                    dl2.download_button("📝 DOCX", data=f, file_name=f"story_{result_num}.docx",
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                        key=f"docx_{idx}", use_container_width=True)
            except ImportError:
                dl2.caption("DOCX unavailable")

            txt_path = create_txt(edited, genre=g, characters=ch, content_type=ct)
            with open(txt_path, "r", encoding="utf-8") as f:
                dl3.download_button("📃 TXT", data=f.read(), file_name=f"story_{result_num}.txt",
                                    mime="text/plain", key=f"txt_{idx}", use_container_width=True)

# ══════════════════════════ TAB 2 : Character Builder ═════════════════════════
with tab_char:
    st.subheader("🧑 Character Builder")
    st.caption("Build a character profile — it will be injected into your next story automatically.")

    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Character Name", value=st.session_state.char_name, placeholder="e.g. Arjun")
        age  = st.text_input("Age", value=st.session_state.char_age, placeholder="e.g. 28")
    with c2:
        personality = st.text_input("Personality Traits", value=st.session_state.char_personality,
                                    placeholder="e.g. brave, sarcastic, kind-hearted")
        background  = st.text_area("Background / Backstory", value=st.session_state.char_background,
                                   placeholder="e.g. Former soldier who lost his memory…", height=100)

    s1, s2 = st.columns(2)
    if s1.button("💾 Save Character", type="primary", use_container_width=True):
        st.session_state.char_name        = name
        st.session_state.char_age         = age
        st.session_state.char_personality = personality
        st.session_state.char_background  = background
        st.success(f"✅ Character **{name}** saved! Switch to Generate tab to use them.")
    if s2.button("🗑️ Clear Character", use_container_width=True):
        for k in ["char_name", "char_age", "char_personality", "char_background"]:
            st.session_state[k] = ""
        st.rerun()

    if st.session_state.char_name:
        st.divider()
        st.markdown(f"""
| Field | Value |
|---|---|
| Name | {st.session_state.char_name} |
| Age | {st.session_state.char_age or '—'} |
| Personality | {st.session_state.char_personality or '—'} |
| Background | {st.session_state.char_background or '—'} |
""")


# ══════════════════════════ TAB 3 : Genre Recommendation ══════════════════════
with tab_genre:
    st.subheader("💡 Genre Recommendation")
    st.caption("Describe your story idea and the AI will suggest the best genres.")

    idea = st.text_area(
        "📝 Describe your story idea",
        placeholder="e.g. A soldier wakes up in a world where technology has been erased…",
        height=120,
    )
    if st.button("🔍 Suggest Genres", type="primary", use_container_width=True):
        if not idea.strip():
            st.warning("Please enter a story idea first.")
        else:
            with st.spinner("🤔 Analysing your idea…"):
                suggestions = recommend_genre(idea)
            if suggestions.startswith("ERROR:"):
                st.error(suggestions.replace("ERROR: ", ""))
            else:
                st.markdown("### 🎯 Suggested Genres")
                st.markdown(suggestions)

# ══════════════════════════ TAB 4 : Plot Builder ══════════════════════════════
with tab_plot:
    st.subheader("🗺️ AI Plot Builder")
    st.caption("Generate a solid 3-Act structure before you start writing.")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        plot_genre = st.selectbox("Genre (Plot)", ["Sci-Fi", "Fantasy", "Action", "Romance", "Thriller", "Horror", "Mystery"])
        plot_chars = st.text_input("Main Characters", "Arjun, Maya", key="plot_chars")
    with col_p2:
        plot_theme = st.text_area("Central Premise / Theme", "A race against time to stop an ancient evil from waking up.", height=110)
        
    if st.button("🗺️ Generate Plot Outline", type="primary", use_container_width=True):
        with st.spinner("Structuring your epic saga..."):
            plot_outline = generate_plot(plot_genre, plot_chars, plot_theme)
        
        if plot_outline.startswith("ERROR:"):
            st.error(plot_outline.replace("ERROR: ", ""))
        else:
            st.markdown("### 📜 Your 3-Act Structure")
            st.info(plot_outline)


# ══════════════════════════ TAB 5 : Story Library ═════════════════════════════
with tab_lib:
    st.subheader("📚 Story Library")
    st.caption("All stories you have saved are stored here in a local SQLite database.")

    if st.button("🔄 Refresh Library", use_container_width=False):
        st.rerun()

    stories = get_all_stories()
    if not stories:
        st.info("No stories saved yet. Generate a story and click **💾 Save** to add it here.")
    else:
        st.markdown(f"**{len(stories)} story/stories saved**")
        st.divider()
        for story in stories:
            with st.expander(
                f"📖 {story['title']}  ·  {story['genre']}  ·  {story['language']}  ·  🕐 {story['saved_at']}",
                expanded=False
            ):
                st.text_area("Story Text", value=story["text"], height=200,
                             key=f"lib_txt_{story['id']}", disabled=False)

                lc1, lc2, lc3 = st.columns(3)

                # PDF download from library
                pdf_path = create_pdf(story["text"], genre=story["genre"],
                                      characters=story.get("characters",""),
                                      content_type=story.get("content_type",""))
                with open(pdf_path, "rb") as f:
                    lc1.download_button("📄 PDF", data=f,
                                        file_name=f"saved_{story['id']}.pdf",
                                        mime="application/pdf",
                                        key=f"lib_pdf_{story['id']}",
                                        use_container_width=True)

                # Voice narration from library
                if lc2.button("🔊 Narrate", key=f"lib_audio_{story['id']}",
                              use_container_width=True):
                    lang_code = GTTS_LANG_CODES.get(story.get("language","English"), "en")
                    try:
                        with st.spinner("🔊 Generating narration…"):
                            audio_bytes = text_to_audio(story["text"], lang_code=lang_code)
                        st.audio(audio_bytes, format="audio/mp3")
                    except Exception as e:
                        st.error(f"Audio failed: {e}")

                # Delete
                if lc3.button("🗑️ Delete", key=f"lib_del_{story['id']}",
                              use_container_width=True):
                    delete_story(story["id"])
                    st.success("Story deleted.")
                    st.rerun()
