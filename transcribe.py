from __future__ import division

import sys
import time
import uuid
from google.cloud import speech
from google.cloud import translate_v2 as translate
from google.cloud import storage
from google.cloud.speech_v1p1beta1 import types
import google.api_core.exceptions

def generate_chunks():
    while True:
        data = sys.stdin.buffer.read(512)
        if not data:
            break
        yield data

def get_mac_address():
    """Returns the MAC address of the device."""
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return mac

def create_bucket_if_not_exists(bucket_name):
    """Creates a new bucket if it does not exist."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    if not bucket.exists():
        bucket = storage_client.create_bucket(bucket_name)
        print(f"Created new bucket: {bucket_name}")
    else:
        print(f"Bucket {bucket_name} already exists.")

def save_to_cloud_storage(bucket_name, content, file_name):
    """Uploads a string to a Google Cloud Storage bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.upload_from_string(content)
    print(f"Transcription saved to {bucket_name}/{file_name}")

def listen_print_loop(responses, translate_client, bucket_name, file_name, file_name_2, save_interval=5):
    all_transcripts = ""
    all_translations = ""
    last_save_time = time.time()

    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript
        print(f'Transcript: {transcript}')

        # Translate the transcript into Spanish
        translation = translate_client.translate(transcript, target_language='es')
        translated_text = translation['translatedText']
        print(f'Translated to Spanish: {translated_text}')

        if result.is_final:
            # Append the final transcription to the file content
            all_transcripts += f'{transcript}\n'
            all_translations += f'{translated_text}\n'

            # Save the transcription and translation at regular intervals to avoid rate limits
            current_time = time.time()
            if current_time - last_save_time > save_interval:
                save_to_cloud_storage(bucket_name, all_transcripts, file_name)
                save_to_cloud_storage(bucket_name, all_translations, file_name_2)
                last_save_time = current_time

            print(f'Final Transcript: {transcript}')
            print(f'Final Translation to Spanish: {translated_text}')

    # Ensure the final save when the stream ends
    save_to_cloud_storage(bucket_name, all_transcripts, file_name)
    save_to_cloud_storage(bucket_name, all_translations, file_name_2)

def transcribe_and_translate_streaming():
    client = speech.SpeechClient()
    translate_client = translate.Client()

    # Get the device's MAC address to use as the bucket name
    mac_address = get_mac_address()
    bucket_name = mac_address

    # Create a new bucket if it does not exist
    create_bucket_if_not_exists(bucket_name)

    # Create unique file names based on the current time
    file_name = f"transcription_{time.strftime('%Y%m%d-%H%M%S')}.txt"
    file_name_2 = f"translation_{time.strftime('%Y%m%d-%H%M%S')}.txt"

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=24000,
        language_code="en-US",
        alternative_language_codes=["fr-FR", "de-DE", "it-IT"],
        enable_automatic_punctuation=True,
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True,
        single_utterance=False  # Keep the session open after each utterance
    )

    audio_generator = generate_chunks()

    requests = (
        speech.StreamingRecognizeRequest(audio_content=chunk)
        for chunk in audio_generator
    )

    try:
        responses = client.streaming_recognize(
            streaming_config, requests
        )
        listen_print_loop(responses, translate_client, bucket_name, file_name, file_name_2)
    except google.api_core.exceptions.GoogleAPICallError as e:
        print(f"API error: {e}")

if __name__ == "__main__":
    transcribe_and_translate_streaming()
