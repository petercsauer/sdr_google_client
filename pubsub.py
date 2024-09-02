from google.cloud import pubsub_v1
import sys
import uuid

def get_mac_address():
    """Returns the MAC address of the device."""
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return mac

def create_pubsub_topic(project_id, topic_name):
    """Creates a new Pub/Sub topic if it does not exist."""
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_name)
    
    try:
        topic = publisher.create_topic(request={"name": topic_path})
        print(f"Created new Pub/Sub topic: {topic_name}")
    except Exception as e:
        print(f"Error creating topic or topic already exists: {e}")

def generate_chunks():
    while True:
        data = sys.stdin.buffer.read(512)
        if not data:
            break
        yield data

def stream_audio_to_pubsub(project_id, topic_id):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    for chunk in generate_chunks():
        # Publish each chunk to the Pub/Sub topic
        publisher.publish(topic_path, chunk)
        print(f"Sent chunk to {topic_id}")

if __name__ == "__main__":
    project_id = "rtl-test"
    mac_address = get_mac_address()
    topic_id = mac_address  # Use MAC address as the topic name

    # Create the Pub/Sub topic if it doesn't exist
    create_pubsub_topic(project_id, topic_id)

    # Stream audio to the Pub/Sub topic
    stream_audio_to_pubsub(project_id, topic_id)
