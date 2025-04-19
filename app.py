import streamlit as st
from PIL import Image
import numpy as np
from deepface import DeepFace
import time


# --- Streamlit Setup ---
st.set_page_config(
    page_title="MoodTunes - Emotion-Based Music Recommender",
    layout="centered",
    page_icon="🎶",
    initial_sidebar_state="collapsed"
)

# --- Simplified CSS for Styling ---
st.markdown("""
<style>
:root {
    --primary: #1DB954;        /* Spotify green */
    --primary-light: #1ed760;  /* Lighter green */
    --dark: #191414;          /* Spotify black */
    --light: #FFFFFF;         /* White */
    --gray: #f8f9fa;          /* Light gray background */
    --text: #212529;          /* Dark text */
    --text-light: #6c757d;    /* Lighter text */
    --text-dark: #343a40;     /* Darker text */
    --border: #dee2e6;        /* Light border */
    --red: #dc3545;         /* Red for errors */
    --blue: #007bff;        /* Blue for links */       
}

body {
    background-color: var(--gray);
    color: var(--text);
    font-family: 'Inter', sans-serif;
}

.header {
    text-align: center;
    margin-bottom: 2rem;
}

.header h1 {
    color: var(--primary);
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.header p {
    color: var(--text-light);
    font-size: 1.1rem;
}

.section-title {
    color: var(--light);
    font-weight: 600;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.stRadio > div {
    background-color: var(--dark);
    border-radius: 10px;
    padding: 0.75rem;
}

.stRadio [role=radio][aria-checked=true] {
    background-color: var(--dark );
    color: var(--light);
}

.stButton > button {
    background-color: var(--primary);
    color: var(--dark);
    border-radius: 8px;
    padding: 0.75rem 1.5rem;
    font-weight: 600;
    border: none;
    width: 100%;
    transition: all 0.2s;
}

.stButton > button:hover {
    background-color: var(--primary-light);
    transform: translateY(-1px);
}

.mood-option {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1rem;
    border-radius: 10px;
    background-color: var(--dark);
    cursor: pointer;
    transition: all 0.2s;
    border: 2px solid transparent;
    text-align: center;
}

.mood-option:hover {
    transform: translateY(-3px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.mood-option.selected {
    border-color: var(--primary);
    background-color: rgba(29, 185, 84, 0.1);
}

.mood-emoji {
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

.mood-label {
    font-weight: 500;
}

.playlist-card {
    background-color: var(--light);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.playlist-title {
    color: var(--dark);
    font-weight: 700;
    margin-bottom: 1rem;
}

.song-item {
    display: flex;
    align-items: center;
    padding: 0.75rem;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    background-color: var(--gray);
}

.song-info {
    margin-left: 1rem;
}

.song-title {
    font-weight: 600;
    color: var(--text);
}

.song-artist {
    font-size: 0.9rem;
    color: var(--light);
}

.spotify-btn {
    background-color: var(--dark) !important;
    color: var(--light) !important;
    padding: 0.75rem 1.5rem !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    text-decoration: none !important;
    display: inline-block !important;
    transition: all 0.2s !important;
}

.spotify-btn:hover {
    background-color: var(--primary-light) !important;
    transform: translateY(-1px) !important;
}

.footer {
    text-align: center;
    color: var(--text-light);
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid #dee2e6;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .section {
        padding: 1.25rem;
    }
    
    .mood-option {
        padding: 0.75rem;
    }
    
    .mood-emoji {
        font-size: 1.75rem;
    }
}
</style>
""", unsafe_allow_html=True)

# --- App Header ---
st.markdown("""
<div class="header">
    <h1>MoodTunes</h1>
    <p>Discover the perfect playlist for your mood</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state for mood selection
if 'selected_mood' not in st.session_state:
    st.session_state.selected_mood = None

# --- Language Selection ---
with st.container():
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🌍 Choose Your Language</div>', unsafe_allow_html=True)
    language = st.radio(
        "Select your preferred music language:",
        ["Hindi", "English", "Punjabi"],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# --- Mood Selection ---
with st.container():
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">😊 How Are You Feeling Today?</div>', unsafe_allow_html=True)
    st.markdown("Choose your mood or upload a selfie for automatic detection:")

    moods = {
        "Happy": "😄",
        "Sad": "😢",
        "Angry": "😠",
        "Neutral": "😐",
        "Surprised": "😲",
        "Fear": "😨",
        "Disgust": "🤢"
    }

    cols = st.columns(len(moods))
    
    # Create a radio button for mood selection but hide it visually
    mood_options = list(moods.keys())
    selected_mood_radio = st.radio(
        "Select your mood:",
        mood_options,
        index=mood_options.index(st.session_state.selected_mood.capitalize()) if st.session_state.selected_mood else 0,
        key="mood_radio",
        label_visibility="collapsed",
        horizontal=True
    )
    
    # Update the selected mood in session state
    if selected_mood_radio:
        st.session_state.selected_mood = selected_mood_radio.lower()

    # Display mood options as clickable cards
    for idx, (mood, emoji) in enumerate(moods.items()):
        with cols[idx]:
            is_selected = st.session_state.selected_mood == mood.lower()
            btn_class = "selected" if is_selected else ""
            st.markdown(f"""
                <div class="mood-option {btn_class}" onclick="document.dispatchEvent(new CustomEvent('moodSelected', {{detail: '{mood.lower()}'}}))">
                    <div class="mood-emoji">{emoji}</div>
                    <div class="mood-label">{mood}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <script>
    document.addEventListener('moodSelected', function(e) {
        // Update the radio button selection which will trigger Streamlit to rerun
        const radioButtons = parent.document.querySelectorAll('input[name="mood_radio"]');
        radioButtons.forEach((radio, index) => {
            if (radio.value.toLowerCase() === e.detail) {
                radio.click();
            }
        });
    });
    </script>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Upload Selfie ---
with st.container():
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📸 Or Upload a Selfie for Mood Detection</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload your photo (we'll detect your mood automatically)",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed",
        key="file_uploader"
    )

    detected_emotion = None
    analysis_success = False

    if uploaded_file:
        with st.expander("👀 View Your Photo", expanded=True):
            st.image(uploaded_file, use_column_width=True)

        if st.button("Analyze My Mood", key="analyze_btn"):
            with st.spinner("🔍 Analyzing your mood..."):
                try:
                    progress_bar = st.progress(0)
                    for percent_complete in range(100):
                        time.sleep(0.03)
                        progress_bar.progress(percent_complete + 1)

                    image = Image.open(uploaded_file)
                    image_array = np.array(image)

                    result = DeepFace.analyze(img_path=image_array, actions=['emotion'], enforce_detection=False)
                    detected_emotion = result[0]['dominant_emotion'].lower()
                    analysis_success = True
                    st.session_state.selected_mood = detected_emotion

                    st.balloons()
                    st.success(f"🎉 We detected you're feeling **{detected_emotion.capitalize()}**!")

                except Exception:
                    st.error("⚠️ Oops! We couldn't analyze your photo. Please try another one or select your mood manually.")
                finally:
                    time.sleep(0.5)
                    progress_bar.empty()

    st.markdown('</div>', unsafe_allow_html=True)

# Determine final mood for playlist selection
final_mood = st.session_state.selected_mood if 'selected_mood' in st.session_state else None

# --- Playlist Mapping ---
mood_playlists = {
    "happy": {
        "Hindi": ("Happy Hindi Hits", "https://open.spotify.com/playlist/3bQy66sMaRDIUIsS7UQnuO", [
            ("Pehla Nasha", "Jo Jeeta Wohi Sikandar"),
            ("Senorita", "Zindagi Na Milegi Dobara"),
            ("Badtameez Dil", "Yeh Jawaani Hai Deewani")
        ]),
        "English": ("Feel Good Pop", "https://open.spotify.com/playlist/37i9dQZF1DXdPec7aLTmlC", [
            ("Uptown Funk", "Mark Ronson ft. Bruno Mars"),
            ("Happy", "Pharrell Williams"),
            ("Can't Stop the Feeling", "Justin Timberlake")
        ]),
        "Punjabi": ("Punjabi Party", "https://open.spotify.com/playlist/37i9dQZF1DWVlYsZr6UA2I", [
            ("Lamberghini", "The Doorbeen"),
            ("Naah", "Harrdy Sandhu"),
            ("Proper Patola", "Badshah")
        ])
    },
    "sad": {
        "Hindi": ("Hindi Soulful", "https://open.spotify.com/playlist/37i9dQZF1DXdFesNN9TzXT", [
            ("Tum Hi Ho", "Aashiqui 2"),
            ("Channa Mereya", "Ae Dil Hai Mushkil"),
            ("Kabira", "Yeh Jawaani Hai Deewani")
        ]),
        "English": ("Melancholy Melodies", "https://open.spotify.com/playlist/37i9dQZF1DX7qK8ma5wgG1", [
            ("Someone Like You", "Adele"),
            ("Fix You", "Coldplay"),
            ("The Night We Met", "Lord Huron")
        ]),
        "Punjabi": ("Punjabi Blues", "https://open.spotify.com/playlist/37i9dQZF1DWXQDoWemaZPl", [
            ("Qismat", "Ammy Virk"),
            ("Sakhiyaan", "Maninder Buttar"),
            ("Ishq Da Uda Ada", "Harbhajan Mann")
        ])
    },
    "angry": {
        "Hindi": ("Hindi Rock", "https://open.spotify.com/playlist/41PIf5ZbsXAJn65I1Gxkh0", [
            ("Bhaag DK Bose", "Delhi Belly"),
            ("Aarambh", "Gorky"),
            ("Rock On", "Farhan Akhtar")
        ]),
        "English": ("Rock Anthems", "https://open.spotify.com/playlist/37i9dQZF1DXcF6B6QPhFDv", [
            ("Killing In The Name", "Rage Against The Machine"),
            ("Break Stuff", "Limp Bizkit"),
            ("Bodies", "Drowning Pool")
        ]),
        "Punjabi": ("Punjabi Rock", "https://open.spotify.com/playlist/37i9dQZF1DX0XUsuxWHRQd", [
            ("So High", "Sidhu Moose Wala"),
            ("Horn Blow", "Diljit Dosanjh"),
            ("Jatt Da Muqabala", "Sidhu Moose Wala")
        ])
    },
    "neutral": {
        "Hindi": ("Chill Hindi", "https://open.spotify.com/playlist/2q0A4LXlsu9wU3uGE5JRda", [
            ("Tum Se Hi", "Jab We Met"),
            ("Raabta", "Agent Vinod"),
            ("Tera Ban Jaunga", "Kabir Singh")
        ]),
        "English": ("Chill Vibes", "https://open.spotify.com/playlist/37i9dQZF1DX4WYpdgoIcn6", [
            ("Better Together", "Jack Johnson"),
            ("Lost In Japan", "Shawn Mendes"),
            ("Banana Pancakes", "Jack Johnson")
        ]),
        "Punjabi": ("Punjabi Chill", "https://open.spotify.com/playlist/37i9dQZF1DX0XUsuxWHRQd", [
            ("Ik Tera", "Maninder Buttar"),
            ("Laung Da Lashkara", "Neha Bhasin"),
            ("Kya Baat Ay", "Harrdy Sandhu")
        ])
    },
    "surprised": {
        "Hindi": ("Hindi Upbeat", "https://open.spotify.com/playlist/37i9dQZF1DX0XUsuxWHRQd", [
            ("Gallan Goodiyaan", "Dil Dhadakne Do"),
            ("Balam Pichkari", "Yeh Jawaani Hai Deewani"),
            ("Kar Gayi Chull", "Kapoor & Sons")
        ]),
        "English": ("Upbeat Surprise", "https://open.spotify.com/playlist/37i9dQZF1DXdPec7aLTmlC", [
            ("Happy", "Pharrell Williams"),
            ("Can't Stop the Feeling", "Justin Timberlake"),
            ("Shake It Off", "Taylor Swift")
        ]),
        "Punjabi": ("Punjabi Upbeat", "https://open.spotify.com/playlist/37i9dQZF1DWVlYsZr6UA2I", [
            ("Naah", "Harrdy Sandhu"),
            ("High Rated Gabru", "Guru Randhawa"),
            ("Lahore", "Guru Randhawa")
        ])
    },
    "fear": {
        "Hindi": ("Calming Hindi", "https://open.spotify.com/playlist/37i9dQZF1DX4WYpdgoIcn6", [
            ("Tum Hi Ho", "Aashiqui 2"),
            ("Raabta", "Agent Vinod"),
            ("Tera Ban Jaunga", "Kabir Singh")
        ]),
        "English": ("Calming Melodies", "https://open.spotify.com/playlist/37i9dQZF1DX7qK8ma5wgG1", [
            ("Someone Like You", "Adele"),
            ("Fix You", "Coldplay"),
            ("The Night We Met", "Lord Huron")
        ]),
        "Punjabi": ("Punjabi Soothing", "https://open.spotify.com/playlist/37i9dQZF1DWXQDoWemaZPl", [
            ("Qismat", "Ammy Virk"),
            ("Sakhiyaan", "Maninder Buttar"),
            ("Ishq Da Uda Ada", "Harbhajan Mann")
        ])
    },
    "disgust": {
        "Hindi": ("Hindi Motivational", "https://open.spotify.com/playlist/37i9dQZF1DWZLcGGC0HJbc", [
            ("Bhaag DK Bose", "Delhi Belly"),
            ("Aarambh", "Gorky"),
            ("Rock On", "Farhan Akhtar")
        ]),
        "English": ("Motivational Rock", "https://open.spotify.com/playlist/37i9dQZF1DXcF6B6QPhFDv", [
            ("Killing In The Name", "Rage Against The Machine"),
            ("Break Stuff", "Limp Bizkit"),
            ("Bodies", "Drowning Pool")
        ]),
        "Punjabi": ("Punjabi Motivational", "https://open.spotify.com/playlist/37i9dQZF1DX0XUsuxWHRQd", [
            ("So High", "Sidhu Moose Wala"),
            ("Horn Blow", "Diljit Dosanjh"),
            ("Jatt Da Muqabala", "Sidhu Moose Wala")
        ])
    }
}

# Show playlist based on final mood and language
if final_mood and language:
    playlists = mood_playlists.get(final_mood, None)
    if playlists:
        playlist_name, playlist_url, songs = playlists.get(language, (None, None, None))
        if playlist_name:
            st.markdown('<div class="section playlist-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="playlist-title">{playlist_name}</div>', unsafe_allow_html=True)
            st.markdown(f'<a href="{playlist_url}" target="_blank" class="spotify-btn">Open on Spotify</a>', unsafe_allow_html=True)
            
            st.markdown('<div style="margin-top: 1.5rem;">', unsafe_allow_html=True)
            for idx, (title, artist) in enumerate(songs, 1):
                st.markdown(f"""
                <div class="song-item">
                    <div>{idx}.</div>
                    <div class="song-info">
                        <div class="song-title">{title}</div>
                        <div class="song-artist">{artist}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Sorry, no playlist found for your selection.")
    else:
        st.info("Sorry, no playlist found for your mood.")
else:
    st.info("Please select your mood or upload a selfie to get music recommendations.")

# --- Footer ---
st.markdown("""
<div class="footer">
    <p>Made with ❤️ by MoodTunes Team</p>
</div>
""", unsafe_allow_html=True)