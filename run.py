from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from speech_gateway.gateway.voicevox import VoicevoxGateway
from speech_gateway.gateway.nijivoice import NijiVoiceGateway
from speech_gateway.gateway.sbv2 import StyleBertVits2Gateway

# Configure root logger
logger = logging.getLogger("speech_gateway")
logger.setLevel(logging.INFO)
log_format = logging.Formatter("[%(levelname)s] %(asctime)s : %(message)s")
streamHandler = logging.StreamHandler()
streamHandler.setFormatter(log_format)
logger.addHandler(streamHandler)

NIJIVOICE_API_KEY = "YOUR_API_KEY"

# Create gateways
aivisspeech_gateway = VoicevoxGateway(base_url="http://127.0.0.1:10101", debug=True)
sbv2_gateway = StyleBertVits2Gateway(base_url="http://127.0.0.1:5000", debug=True)
nijivoice_gateway = NijiVoiceGateway(api_key=NIJIVOICE_API_KEY, prefix="/nijivoice", debug=True)

# Create app
app = FastAPI()

# Add gateways to app
app.include_router(aivisspeech_gateway.get_router(), prefix="/aivisspeech")
app.include_router(sbv2_gateway.get_router(), prefix="/sbv2")
app.include_router(nijivoice_gateway.get_router(), prefix="/nijivoice")

# On app down
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await aivisspeech_gateway.shutdown()
    await sbv2_gateway.shutdown()
    await nijivoice_gateway.shutdown()
