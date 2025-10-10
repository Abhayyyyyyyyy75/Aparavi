import streamlit as st
import requests
import tempfile
import os
import time

# -------------------------------
# CONFIGURATION
# -------------------------------
WEBHOOK_URL = "https://eaas.aparavi.com/webhook?type=cpu&token=df25998c-f47f-5785-ac5c-07df6b526263"
API_KEY = "bk6s2661YYtf3Co7g7hIK4q_cBPPVoe_2eGvw4FrUmmVHwM5LbAqrp1FeH9qG7H7"

# -------------------------------
# STREAMLIT UI
# -------------------------------
st.set_page_config(page_title="Aparavi Auto Transcriber", page_icon="🎧", layout="centered")
st.title("🎧 Aparavi Audio/Video Transcription")
st.write("Drop an MP3 or MP4 file — upload progress and transcription will be shown, text displayed automatically.")

uploaded_file = st.file_uploader(
    "🎵 Drop or select your file",
    type=["mp3", "mp4"]
)

if uploaded_file is not None:
    file_ext = uploaded_file.name.split('.')[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    file_size = os.path.getsize(tmp_path)
    st.info(f"File size: {round(file_size / (1024*1024),2)} MB")

    # Preview file
    if file_ext == "mp3":
        st.audio(tmp_path)
    elif file_ext == "mp4":
        st.video(tmp_path)

    st.info("🚀 Uploading file...")

    upload_bar = st.progress(0)
    upload_text = st.empty()

    try:
        headers = {
            "Authorization": API_KEY,
            "Content-Type": "audio/mpeg"
        }

        # Stream file in chunks to show upload progress
        def file_stream(file_path, chunk_size=1024*1024):
            bytes_sent = 0
            with open(file_path, "rb") as f:
                while chunk := f.read(chunk_size):
                    bytes_sent += len(chunk)
                    progress = min(100, int((bytes_sent / file_size) * 100))
                    upload_bar.progress(progress)
                    upload_text.text(f"Uploading... {progress}%")
                    yield chunk
            upload_text.text("Upload complete ✅")

        # Send file to Aparavi webhook
        response = requests.put(WEBHOOK_URL, headers=headers, data=file_stream(tmp_path))

        if response.status_code == 200:
            st.success("✅ File sent successfully!")

            # Extract transcription text
            resp_json = response.json()
            objects = resp_json.get("data", {}).get("objects", {})
            transcript = ""
            if objects:
                for obj in objects.values():
                    texts = obj.get("text", [])
                    transcript += "\n".join(texts)

            if transcript:
                # Simulated transcription progress bar
                st.info("🕒 Generating transcription...")
                trans_bar = st.progress(0)
                for i in range(0, 101, 10):
                    trans_bar.progress(i)
                    time.sleep(0.1)

                st.subheader("📝 Transcribed Text:")
                st.text_area("Your Transcription", transcript, height=300)
            else:
                st.warning("⚠️ No transcription text found in response.")
                st.json(resp_json)

        else:
            st.error(f"❌ Upload failed! Status: {response.status_code}")
            st.text(response.text)

    except Exception as e:
        st.error(f"Error: {str(e)}")

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
