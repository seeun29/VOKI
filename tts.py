import os
import io
import pygame
from google.cloud import texttospeech
from dotenv import load_dotenv

load_dotenv()

client = texttospeech.TextToSpeechClient(
    client_options={"api_key": os.getenv("GOOGLE_API_KEY")}
)

pygame.mixer.init()


def add_ssml_pause(text: str) -> str:
    """일반 텍스트 → SSML 변환 (문장 사이 pause 삽입)"""
    text = text.replace(".", ".<break time='600ms'/>")
    text = text.replace("?", "?<break time='600ms'/>")
    text = text.replace("!", "!<break time='600ms'/>")
    text = text.replace(",", ",<break time='300ms'/>")
    return f"<speak><prosody rate='0.85'>{text}</prosody></speak>"


def text_to_speech(text: str, save_path: str = None) -> None:
    """텍스트 → 음성 변환 후 바로 스피커 재생"""
    ssml_text = add_ssml_pause(text)

    synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        name="ko-KR-Wavenet-A",
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        pitch=0.0
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    # 메모리에서 바로 재생
    audio_buffer = io.BytesIO(response.audio_content)
    pygame.mixer.music.load(audio_buffer)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    if save_path:
        with open(save_path, "wb") as f:
            f.write(response.audio_content)
        print(f"✅ 파일 저장됨: {save_path}")


# 테스트
if __name__ == "__main__":
    tests = [
        "안녕하세요, 드시고 가시나요?",
        "카페라떼 아이스 1잔, 포장으로 준비할까요?",
        "결제가 완료되었습니다. 감사합니다."
    ]
    for text in tests:
        print(f"🔊 재생 중: {text}")
        text_to_speech(text)