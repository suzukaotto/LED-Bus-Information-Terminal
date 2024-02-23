# This snippet has been automatically generated and should be regarded as a
# code template only.
# It will require modifications to work:
# - It may require correct/in-range values for request initialization.
# - It may require specifying regional endpoints when creating the service
#   client as shown in:
#   https://googleapis.dev/python/google-api-core/latest/client_options.html
from google.cloud import texttospeech_v1

def sample_list_voices():
    # Create a client
    client = texttospeech_v1.TextToSpeechClient()

    # Initialize request argument(s)
    request = texttospeech_v1.ListVoicesRequest(
    )

    # Make the request
    response = client.list_voices(request=request)

    # Handle the response
    print(response)