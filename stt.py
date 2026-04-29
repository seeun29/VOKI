import os
import io
import numpy as np
import sounddevice as sd
import soundfile as sf
import collections
import webrtcvad
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SAMPLE_RATE = 16000
FRAME_DURATION = 30     
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION / 1000)  
SILENCE_THRESHOLD = 30   
MAX_DURATION = 10    

vad = webrtcvad.Vad(2)   # 0~3, 숫자 클수록 민감도 낮음


def record_until_silence() -> np.ndarray:
    """말이 끝나면 자동으로 녹음 종료"""
    print("🎙️ 말씀하세요... (말이 끝나면 자동으로 멈춥니다)")

    frames = []
    silence_count = 0
    speech_detected = False
    ring_buffer = collections.deque(maxlen=10)  # 말 시작 감지용 버퍼

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
        max_frames = int(MAX_DURATION * 1000 / FRAME_DURATION)

        for _ in range(max_frames):
            frame, _ = stream.read(FRAME_SIZE)
            frame_bytes = frame.tobytes()

            try:
                is_speech = vad.is_speech(frame_bytes, SAMPLE_RATE)
            except Exception:
                is_speech = False

            ring_buffer.append((frame, is_speech))

            if not speech_detected:
                # 말 시작 감지: 버퍼의 절반 이상이 음성이면 시작
                num_voiced = len([f for f, s in ring_buffer if s])
                if num_voiced > ring_buffer.maxlen * 0.5:
                    speech_detected = True
                    frames.extend([f for f, s in ring_buffer])
                    print("🔴 음성 감지됨, 녹음 중...")
            else:
                frames.append(frame)
                if not is_speech:
                    silence_count += 1
                else:
                    silence_count = 0

                # 묵음이 일정 시간 이상 지속되면 종료
                if silence_count > SILENCE_THRESHOLD:
                    print("✅ 녹음 완료")
                    break

    if not frames:
        return np.array([], dtype="int16")

    audio = np.concatenate(frames, axis=0).flatten()
    return audio.astype("float32") / 32768.0  


def audio_to_text(audio: np.ndarray) -> str:
    """numpy 배열 → Whisper STT → 텍스트"""
    if len(audio) == 0:
        return ""

    buffer = io.BytesIO()
    sf.write(buffer, audio, SAMPLE_RATE, format="WAV")
    buffer.seek(0)
    buffer.name = "audio.wav"

    result = client.audio.transcriptions.create(
        model="whisper-1",
        file=buffer,
        language="ko"
    )
    return result.text


def listen() -> str:
    """녹음 + STT 한번에"""
    audio = record_until_silence()
    if len(audio) == 0:
        return ""
    text = audio_to_text(audio)
    print(f"📝 인식 결과: {text}")
    return text


# 테스트
if __name__ == "__main__":
    while True:
        input("\n🔴 Enter 누르면 녹음 시작...")
        result = listen()
        print(f"결과: {result}")