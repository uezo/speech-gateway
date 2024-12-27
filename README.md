# SpeechGateway

A reverse proxy server that enhances speech synthesis with essential, extensible features. 🦉💬


## 💎 Features

- 🥰 **Supports Popular Speech Services**: Works seamlessly with AivisSpeech, VOICEVOX, Style-Bert-VITS2, and NijiVoice — and lets you integrate additional services to suit your needs.
- 🗂️ **Caching**: Boost response speed and save API calls with built-in audio caching.
- 🔄 **Format Conversion**: Effortlessly convert WAV to MP3 for bandwidth-friendly responses.
- 📊 **Performance Metrics**: Track synthesis time and cache hits for in-depth insights.
- ⚡️ **Low Latency**: Streamlined pipeline for minimal delay, delivering fast results!
- 🌟 **Unified Interface**: Use various text-to-speech services through a unified interface — now with multi-language support!🌏


## 🎁 Installation

```sh
pip install git+https://github.com/uezo/speech-gateway
```

To use MP3 format conversion, you also need to install ffmpeg to your computer.


## 🚀 Start server

Create a script like the following example:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from speech_gateway.gateway.voicevox import VoicevoxGateway
from speech_gateway.gateway.sbv2 import StyleBertVits2Gateway
from speech_gateway.gateway.nijivoice import NijiVoiceGateway

# Create gateways
voicevox_gateway = VoicevoxGateway(base_url="http://127.0.0.1:10101", debug=True)
sbv2_gateway = StyleBertVits2Gateway(base_url="http://127.0.0.1:5000", debug=True)
nijivoice_gateway = NijiVoiceGateway(api_key=NIJIVOICE_API_KEY, prefix="/nijivoice", debug=True)

# Create app
app = FastAPI()

# Add gateways to app
app.include_router(voicevox_gateway.get_router(), prefix="/aivisspeech")
app.include_router(sbv2_gateway.get_router(), prefix="/sbv2")
app.include_router(nijivoice_gateway.get_router(), prefix="/nijivoice")

# On app down
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await voicevox_gateway.shutdown()
    await sbv2_gateway.shutdown()
    await nijivoice_gateway.shutdown()
```

Then, run it with uvicorn:

```
uvicorn run:app --port 8000
```

In this example, you can access AivisSpeech at http://127.0.0.1:8000/aivisspeech, Style-Bert-VITS2 at http://127.0.0.1:8000/sbv2, and NijiVoice at http://127.0.0.1:8000/nijivoice.

**NOTE**: If you want to perform MP3 conversion, make sure to include `x_audio_format=mp3` as a query parameter in your request. 


## 🌟 Unified Interface

You can use various text-to-speech services through a unified interface specification.
Below is an example of providing a unified interface for AivisSpeech, Style-Bert-VITS2, and Nijivoice.

```python
from speech_gateway.gateway.unified import UnifiedGateway

# Create UnifiedGateway and add gateways with its service name
unified_gateway = UnifiedGateway(debug=True)
unified_gateway.add_gateway("aivisspeech", aivisspeech_gateway, True)   # Set as default gateway
unified_gateway.add_gateway("sbv2", sbv2_gateway)
unified_gateway.add_gateway("nijivoice", nijivoice_gateway)

# Add unified interface router
app.include_router(unified_gateway.get_router())
```

### Parameters

POST a JSON object with the following fields:

| Parameter     | Type   | Required | Description |
|---------------|--------|----------|---------------------------------------------------------------------------------------------|
| `text`        | string | Required | The text to be synthesized into speech. |
| `speaker`     | string | Optional | The unique identifier for the voice in each speech service.<br>For Style-Bert-VITS2, specify as `{model_id}-{speaker_id}`.<br>If omitted, the default speaker of the speech service will be used. |
| `service_name`| string | Optional | The name of the service as specified in `add_gateway`.<br>If omitted, the default gateway will be used. |
| `language`| string | Optional | The language. The corresponding text-to-speech service will be used. If omitted, the default gateway will be used. |


### Client code

You can access the services in a unified manner as shown in the client code below:

```python
import httpx

req = {"text": "こんにちは。これはデフォルトサービスだよ。", "speaker": "888753761"}
# req = {"text": "こんにちは。これはAivisSpeechだよ。", "speaker": "888753761", "service_name": "aivisspeech"}
# req = {"text": "こんにちは。これはStyle-Bert-VITS2だよ。", "speaker": "0-0", "service_name": "sbv2"}
# req = {"text": "こんにちは。これはにじボイスだよ。", "speaker": "a192db5f-bd8b-4fc7-bc08-af5ca5957c12", "service_name": "nijivoice"}

resp = httpx.post("http://127.0.0.1:8000/tts", json=req, timeout=60)

with open("tts.wav", "wb") as f:
    f.write(resp.content)
```

**NOTE**: Due to the unified specification, it is not possible to use features specific to each text-to-speech service (e.g., intonation adjustment or pitch variation control). If you need high-quality speech synthesis utilizing such features, please use the individual service interfaces.


### Multi-language Support

You can configure the system to use the appropriate speech service based on the language, without explicitly specifying the service name.  
By passing `languages` to `add_gateway`, you can register a speech service that corresponds to the `language` specified in the request. Additionally, by registering a `default_speaker`, you can eliminate the need to specify a `speaker` in each request.

```python
# Gateway for default language (ja-JP) - Voice: 888753761
unified_gateway.add_gateway("aivisspeech", aivisspeech_gateway, default_speaker="888753761", default=True)

# Gateway for en-US and zh-CN - Voice: Alloy
unified_gateway.add_gateway("openai", openai_gateway, languages=["en-US", "zh-CN"], default_speaker="alloy")
```

Here is an example of client code to call this API. Switching the `language` enables easy support for multiple languages.

```python
import httpx

# Simply set the text and language - easily switch between multiple languages
req = {"text": "こんにちは。これはデフォルトサービスだよ。"}
# req = {"text": "Hello. This is the speech service for English.", "language": "en-US"}
# req = {"text": "你好，这是英语的语音服务。", "language": "zh-CN"}

resp = httpx.post("http://127.0.0.1:8000/tts", json=req, timeout=60)

with open("tts.wav", "wb") as f:
    f.write(resp.content)
```


## 🛠️ Customization

You can add new speech synthesis services to relay.
Additionally, you can extend the cache store, audio format converter, and performance recorder. For example, the default cache store uses the file system, but you can replace it with a cloud storage service or another alternative.

We’ll provide documentation for these customizations as the need arises, so if you have specific requests, please open an issue! 🙏
