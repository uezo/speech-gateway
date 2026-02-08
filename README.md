# SpeechGateway

A reverse proxy server that enhances speech synthesis with essential, extensible features. 🦉💬


## 💎 Features

- 🥰 **Supports Popular Speech Services**: Works seamlessly with Aivis Cloud / AivisSpeech, VOICEVOX, Style-Bert-VITS2, CoeFont, OpenAI and Azure — and lets you integrate additional services to suit your needs.
- 🗂️ **Caching**: Boost response speed and save API calls with built-in audio caching.
- 🔄 **Format Conversion**: Effortlessly convert WAV to MP3 for bandwidth-friendly responses.
- 📊 **Performance Metrics**: Track synthesis time and cache hits for in-depth insights.
- 🌟 **Unified Interface**: Use various text-to-speech services through a unified interface — now with multi-language support!🌏


## 🐍 Start with Python

Install `speech-gateway` from PyPI.

```sh
pip install speech-gateway
```

Create a script like the following example:

```python
from fastapi import FastAPI
from speech_gateway.gateway.voicevox import VoicevoxGateway
from speech_gateway.gateway.sbv2 import StyleBertVits2Gateway

# Create gateways
voicevox_gateway = VoicevoxGateway(base_url="http://127.0.0.1:50021", debug=True)
sbv2_gateway = StyleBertVits2Gateway(base_url="http://127.0.0.1:5000", debug=True)

# Create app
app = FastAPI()

# Add gateways to app
app.include_router(voicevox_gateway.get_router(), prefix="/voicevox")
app.include_router(sbv2_gateway.get_router(), prefix="/sbv2")
```

Then, run it with uvicorn:

```sh
uvicorn run:app --port 8000
```

In this example, you can access VOICEVOX at http://127.0.0.1:8000/voicevox and Style-Bert-VITS2 at http://127.0.0.1:8000/sbv2 with cache functionality.


**NOTE**: To use MP3 format conversion, you also need to install ffmpeg to your computer.


## 🐳 Start with Docker

Get resources and move into it.

```sh
git clone https://github.com/uezo/speech-gateway.git
cd speech-gateway/docker
```

Edit `.env`.

```sh
nano .env
```

**[!! Linux Only !!]** Make directories and set permissions.

```sh
sh init-data.sh
```

Start services.

```sh
docker compose up -d
```

Try Unified API at http://127.0.0.1:8000/docs .


## 🌟 Unified Interface

You can use various text-to-speech services through a unified interface specification.
Below is an example of providing a unified interface for VOICEVOX and Style-Bert-VITS2.

```python
from speech_gateway.gateway.unified import UnifiedGateway

# Create UnifiedGateway and add gateways with its service name
unified_gateway = UnifiedGateway(debug=True)
unified_gateway.add_gateway("voicevox", voicevox_gateway, True)   # Set as default gateway
unified_gateway.add_gateway("sbv2", sbv2_gateway)

# Add unified interface router
app.include_router(unified_gateway.get_router())
```

### Parameters

POST a JSON object with the following fields:

| Parameter     | Type   | Required | Description |
|---------------|--------|----------|---------------------------------------------------------------------------------------------|
| `text`        | string | Required | The text to be synthesized into speech. |
| `speaker`     | string | Optional | The unique identifier for the voice in each speech service.<br>For Style-Bert-VITS2, specify as `{model_id}-{speaker_id}`.<br>If omitted, the default speaker of the speech service will be used. |
| `style`| string | Optional | A predefined set of voice styles that includes `neutral`, `joy`, `angry`, `sorrow`, `fun`, and `surprised`. |
| `speed`| float | Optional | The speed of synthesized speech, where 1.0 is normal speed.<br>Values greater than 1.0 increase the speed (e.g., 1.5 is 50% faster), <br>and values less than 1.0 decrease the speed (e.g., 0.5 is 50% slower). <br>The acceptable range depends on each speech service.|
| `service_name`| string | Optional | The name of the service as specified in `add_gateway`.<br>If omitted, the default gateway will be used. |
| `language`| string | Optional | The language. The corresponding text-to-speech service will be used. If omitted, the default gateway will be used. |


### Client code

You can access the services in a unified manner as shown in the client code below:

```python
import httpx

req = {"text": "こんにちは。これはデフォルトサービスだよ。", "speaker": "46"}
# req = {"text": "こんにちは。これはボイスボックスだよ。", "speaker": "46", "service_name": "voicevox"}
# req = {"text": "こんにちは。これはスタイル・バート・ビッツツーだよ。", "speaker": "0-0", "service_name": "sbv2"}

resp = httpx.post("http://127.0.0.1:8000/tts", json=req, timeout=60)

with open("tts.wav", "wb") as f:
    f.write(resp.content)
```

**NOTE**: Due to the unified specification, it is not possible to use features specific to each text-to-speech service (e.g., intonation adjustment or pitch variation control). If you need high-quality speech synthesis utilizing such features, please use the individual service interfaces.


### Applying Style

Define styles on server side.

```python
aivisspeech_gateway = VoicevoxGateway(base_url="http://127.0.0.1:10101", debug=True)
# Define speakers for each style
aivisspeech_gateway.style_mapper["888753761"] = {
    "joy": "888753764",
    "angry": "888753765",
    "sorrow": "888753765",
    "fun": "888753762",
    "surprised": "888753762"
}

sbv2_gateway = StyleBertVits2Gateway(base_url="http://127.0.0.1:5000", debug=True)
# Define sytle name for each style
sbv2_gateway.style_mapper["0-0"] = {
    "joy": "上機嫌",
    "angry": "怒り・悲しみ",
    "sorrow": "怒り・悲しみ",
    "fun": "テンション高め",
    "surprised": "テンション高め"
}
```

Call with style from client.

```python
req = {"service_name": "aivisspeech", "text": "こんにちは。これはデフォルトサービスだよ。", "speaker": "888753761", "style": "angry"}
# req = {"service_name": "sbv2", "text": "こんにちは。これはStyle-Bert-VITS2だよ。", "speaker": "0-0", "style": "angry"}

resp = httpx.post("http://127.0.0.1:8000/tts", json=req, timeout=60)

with open("tts.wav", "wb") as f:
    f.write(resp.content)
```


### Multi-language Support

You can configure the system to use the appropriate speech service based on the language, without explicitly specifying the service name.  
By passing `languages` to `add_gateway`, you can register a speech service that corresponds to the `language` specified in the request. Additionally, by registering a `default_speaker`, you can eliminate the need to specify a `speaker` in each request.

```python
# Gateway for default language (ja-JP) - Voice: 46
unified_gateway.add_gateway("voicevox", voicevox_gateway, default_speaker="46", default=True)

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


### Authentication

You can protect UnifiedGateway with API key-based authentication.

```python
# Create unified gateway with API key
unified_gateway = UnifiedGateway(api_key="MyApiKey")
```

To access a server with `api_key` configured, set the API key in the Authorization header like `Authorization: Bearer MyApiKey`.


## 🧩 Python SDK

When your client application is limited to a single Python application, you can use SpeechGateway directly as a Python library without running a proxy server.

```python
import asyncio
from speech_gateway.gateway.unified import UnifiedGateway
from speech_gateway.gateway.voicevox import VoicevoxGateway
from speech_gateway.gateway import UnifiedTTSRequest

async def main():
    # Create gateways
    voicevox_gateway = VoicevoxGateway(base_url="http://127.0.0.1:50021")

    # Create UnifiedGateway and add gateways
    unified_gateway = UnifiedGateway()
    unified_gateway.add_gateway("voicevox", voicevox_gateway, default_speaker="46", default=True)

    # Call tts directly
    response = await unified_gateway.tts(UnifiedTTSRequest(text="こんにちは"))

    # Save audio
    with open("output.wav", "wb") as f:
        f.write(response.audio_data)

    # Cleanup
    await unified_gateway.shutdown()

asyncio.run(main())
```

This approach is useful when integrating speech synthesis into an existing Python application without the overhead of HTTP communication.


## 🛠️ Customization

You can add new speech synthesis services to relay.
Additionally, you can extend the cache store, audio format converter, and performance recorder. For example, the default cache store uses the file system, but you can replace it with a cloud storage service or another alternative.

We'll provide documentation for these customizations as the need arises, so if you have specific requests, please open an issue! 🙏


## 💡 Migration from v0.1 to v0.2

### Breaking Changes

Version 0.2 introduces a major architectural change: **streaming has been replaced with buffered processing**.

#### Why We Removed Streaming

SpeechGateway is designed for short utterances — typically a few seconds of audio segmented by punctuation. For this use case:

- **Minimal latency benefit**: The time difference between "first byte received" and "all data received" is negligible for short audio clips (typically tens to hundreds of KB).
- **Simplified codebase**: Streaming required complex async iterator management, concurrent task handling, and error propagation across stream boundaries. Buffered processing is straightforward and less error-prone.
- **Better cache compatibility**: Caching requires complete data. Streaming needed an extra aggregation step, while buffered data can be cached directly.

If your use case involves long-form audio synthesis (30+ seconds), you may want to consider a different approach or stay on v0.1.

#### Code Changes Required

**Gateway initialization**: The `stream_source` parameter has been removed. Configuration options are now passed directly to the gateway constructor.

```python
# v0.1
from speech_gateway.source.voicevox import VoicevoxStreamSource
gateway = VoicevoxGateway(stream_source=VoicevoxStreamSource(base_url="..."))

# v0.2
gateway = VoicevoxGateway(base_url="...", cache_dir="voicevox_cache")
```

**Custom FormatConverter**: The `convert` method signature has changed.

```python
# v0.1
async def convert(self, input_stream: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
    async for chunk in input_stream:
        # process chunk
        yield processed_chunk

# v0.2
async def convert(self, input_bytes: bytes) -> bytes:
    # process all data at once
    return processed_bytes
```
