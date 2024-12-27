import pytest
import os
from speech_gateway.gateway.voicevox import VoicevoxGateway
from speech_gateway.gateway.nijivoice import NijiVoiceGateway
from speech_gateway.gateway.sbv2 import StyleBertVits2Gateway
from speech_gateway.gateway.openai_speech import OpenAIGateway
from speech_gateway.gateway.unified import UnifiedGateway
from speech_gateway.gateway import UnifiedTTSRequest

VOICEVOX_URL = os.getenv("VOICEVOX_URL")
SBV2_URL = os.getenv("SBV2_URL")
NIJIVOICE_API_KEY = os.getenv("NIJIVOICE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@pytest.mark.asyncio
async def test_unified_gateway_default():
    # Create gateways
    voicevox_gateway = VoicevoxGateway(base_url=VOICEVOX_URL, debug=True)
    sbv2_gateway = StyleBertVits2Gateway(base_url=SBV2_URL, debug=True)
    nijivoice_gateway = NijiVoiceGateway(api_key=NIJIVOICE_API_KEY, prefix="/nijivoice", debug=True)
    openai_gateway = OpenAIGateway(api_key=OPENAI_API_KEY, debug=True)

    # Unified gateway
    unified_gateway = UnifiedGateway(debug=True)
    unified_gateway.add_gateway("voicevox", voicevox_gateway, default_speaker="46", default=True)
    unified_gateway.add_gateway("sbv2", sbv2_gateway)
    unified_gateway.add_gateway("nijivoice", nijivoice_gateway)
    unified_gateway.add_gateway("openai", openai_gateway, languages=["en-US", "zh-CN"], default_speaker="alloy")

    assert unified_gateway.get_gateway(UnifiedTTSRequest(text="hello")) == voicevox_gateway

    assert unified_gateway.get_gateway(UnifiedTTSRequest(text="hello", service_name="voicevox")) == voicevox_gateway
    assert unified_gateway.get_gateway(UnifiedTTSRequest(text="hello", service_name="sbv2")) == sbv2_gateway
    assert unified_gateway.get_gateway(UnifiedTTSRequest(text="hello", service_name="nijivoice")) == nijivoice_gateway
    assert unified_gateway.get_gateway(UnifiedTTSRequest(text="hello", service_name="openai")) == openai_gateway
    assert unified_gateway.get_gateway(UnifiedTTSRequest(text="hello", service_name="dummy")) is None

    assert unified_gateway.get_gateway(UnifiedTTSRequest(text="hello", language="ja-JP")) == voicevox_gateway
    assert unified_gateway.get_gateway(UnifiedTTSRequest(text="hello", language="en-US")) == openai_gateway
    assert unified_gateway.get_gateway(UnifiedTTSRequest(text="hello", language="zh-CN")) == openai_gateway

    assert unified_gateway.get_gateway(UnifiedTTSRequest(text="hello", service_name="sbv2", language="en-US")) == sbv2_gateway