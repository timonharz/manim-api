from pathlib import Path
from gtts import gTTS

from langdetect import detect, LangDetectException

class TTSService:
    @staticmethod
    def generate_audio(text: str, output_path: Path):
        """
        Generates an audio file from the given text using gTTS.
        
        Args:
            text: The text script to narrate.
            output_path: The path where the audio file should be saved.
        """
        try:
            lang = detect(text)
        except LangDetectException:
            lang = 'en'
            
        tts = gTTS(text=text, lang=lang)
        tts.save(str(output_path))
        return output_path
