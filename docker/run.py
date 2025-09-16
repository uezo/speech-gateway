from contextlib import asynccontextmanager
import logging
import os
from fastapi import FastAPI
from dotenv import load_dotenv
from speech_gateway.performance_recorder.postgres import PostgreSQLPerformanceRecorder
from speech_gateway.gateway.azure import AzureGateway
from speech_gateway.gateway.openai_speech import OpenAIGateway
from speech_gateway.gateway.voicevox import VoicevoxGateway
from speech_gateway.gateway.sbv2 import StyleBertVits2Gateway
from speech_gateway.gateway.nijivoice_encoded import NijiVoiceEncodedGateway
from speech_gateway.gateway.unified import UnifiedGateway

# Configure root logger
logger = logging.getLogger("speech_gateway")
logger.setLevel(logging.INFO)
log_format = logging.Formatter("[%(levelname)s] %(asctime)s : %(message)s")
streamHandler = logging.StreamHandler()
streamHandler.setFormatter(log_format)
logger.addHandler(streamHandler)

load_dotenv()
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

# Azure
AZURE_ENABLED = os.getenv("AZURE_ENABLED", "false").lower() in ("true", "1", "yes")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_REGION = os.getenv("AZURE_REGION")
AZURE_LANGUAGES = os.getenv("AZURE_LANGUAGES")
# OpenAI
OPENAI_ENABLED = os.getenv("OPENAI_ENABLED", "false").lower() in ("true", "1", "yes")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_LANGUAGES = os.getenv("OPENAI_LANGUAGES")
# VOICEVOX
VOICEVOX_ENABLED = os.getenv("VOICEVOX_ENABLED", "false").lower() in ("true", "1", "yes")
VOICEVOX_URL = os.getenv("VOICEVOX_URL")
VOICEVOX_LANGUAGES = os.getenv("VOICEVOX_LANGUAGES")
# Style-Bert-VITS2
SBV2_ENABLED = os.getenv("SBV2_ENABLED", "false").lower() in ("true", "1", "yes")
SBV2_URL = os.getenv("SBV2_URL")
SBV2_LANGUAGES = os.getenv("SBV2_LANGUAGES")
# NIJIVOICE
NIJIVOICE_ENABLED = os.getenv("NIJIVOICE_ENABLED", "false").lower() in ("true", "1", "yes")
NIJIVOICE_API_KEY = os.getenv("NIJIVOICE_API_KEY")
NIJIVOICE_LANGUAGES = os.getenv("NIJIVOICE_LANGUAGES")
# Database
DB_PORT = os.getenv("PORT_DB")
DB_USER = os.getenv("SPGW_DB_USER")
DB_PASSWORD = os.getenv("SPGW_DB_PASSWORD")

# Performance recorder
performance_recorder = PostgreSQLPerformanceRecorder(host="spgw-db", port=DB_PORT, user=DB_USER, password=DB_PASSWORD)

# On app down
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Shutdown enabled gateways
    if AZURE_ENABLED and 'azure_gateway' in globals():
        await azure_gateway.shutdown()
    if OPENAI_ENABLED and 'openai_gateway' in globals():
        await openai_gateway.shutdown()
    if VOICEVOX_ENABLED and 'voicevox_gateway' in globals():
        await voicevox_gateway.shutdown()
    if SBV2_ENABLED and 'sbv2_gateway' in globals():
        await sbv2_gateway.shutdown()
    if NIJIVOICE_ENABLED and 'nijivoice_gateway' in globals():
        await nijivoice_gateway.shutdown()

# Create API app
app = FastAPI(lifespan=lifespan)

# Unified gateway
unified_gateway = UnifiedGateway(debug=True)
app.include_router(unified_gateway.get_router())

# Create service gateways
if AZURE_ENABLED:
    azure_gateway = AzureGateway(api_key=AZURE_API_KEY, cache_dir="cache/azure", performance_recorder=performance_recorder, region=AZURE_REGION, debug=DEBUG)
    unified_gateway.add_gateway(
        service_name="azure",
        gateway=azure_gateway,
        languages=AZURE_LANGUAGES.split(",") if AZURE_LANGUAGES else None,
    )
    app.include_router(azure_gateway.get_router(), prefix="/azure")
    logger.info("[Gateway] Azure on /azure")

if OPENAI_ENABLED:
    openai_gateway = OpenAIGateway(api_key=OPENAI_API_KEY, cache_dir="cache/openai", performance_recorder=performance_recorder, debug=DEBUG)
    unified_gateway.add_gateway(
        service_name="openai",
        gateway=openai_gateway,
        languages=OPENAI_LANGUAGES.split(",") if OPENAI_LANGUAGES else None,
    )
    app.include_router(openai_gateway.get_router(), prefix="/openai")
    logger.info(f"[Gateway] OpenAI on /openai")

if VOICEVOX_ENABLED:
    voicevox_gateway = VoicevoxGateway(base_url=VOICEVOX_URL, cache_dir="cache/voicevox", performance_recorder=performance_recorder, debug=DEBUG)
    unified_gateway.add_gateway(
        service_name="voicevox",
        gateway=voicevox_gateway,
        languages=VOICEVOX_LANGUAGES.split(",") if VOICEVOX_LANGUAGES else None,
    )
    app.include_router(voicevox_gateway.get_router(), prefix="/voicevox")
    logger.info(f"[Gateway] VOICEVOX on /voicevox")

if SBV2_ENABLED:
    sbv2_gateway = StyleBertVits2Gateway(base_url=SBV2_URL, cache_dir="cache/sbv2", performance_recorder=performance_recorder, debug=DEBUG)
    unified_gateway.add_gateway(
        service_name="sbv2",
        gateway=sbv2_gateway,
        languages=SBV2_LANGUAGES.split(",") if SBV2_LANGUAGES else None,
    )
    app.include_router(sbv2_gateway.get_router(), prefix="/sbv2")
    logger.info(f"[Gateway] Style-Bert-VITS2 on /sbv2")

if NIJIVOICE_ENABLED:
    nijivoice_gateway = NijiVoiceEncodedGateway(api_key=NIJIVOICE_API_KEY, cache_dir="cache/nijivoice", performance_recorder=performance_recorder, debug=DEBUG)
    unified_gateway.add_gateway(
        service_name="nijivoice",
        gateway=nijivoice_gateway,
        languages=NIJIVOICE_LANGUAGES.split(",") if NIJIVOICE_LANGUAGES else None,
    )
    app.include_router(nijivoice_gateway.get_router(), prefix="/nijivoice")
    logger.info(f"[Gateway] Nijivoice on /nijivoice")
