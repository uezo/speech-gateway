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
from speech_gateway.gateway.coefont import CoefontGateway
from speech_gateway.gateway.unified import UnifiedGateway

load_dotenv()
SPGW_DEBUG = os.getenv("SPGW_DEBUG", "false").lower() in ("true", "1", "yes")
SPGW_LOG_LEVEL = os.getenv("SPGW_LOG_LEVEL", "INFO")
SPGW_API_KEY = os.getenv("SPGW_API_KEY")

# Azure
SPGW_AZURE_ENABLED = os.getenv("SPGW_AZURE_ENABLED", "false").lower() in ("true", "1", "yes")
SPGW_AZURE_API_KEY = os.getenv("SPGW_AZURE_API_KEY") or os.getenv("AZURE_SPEECH_API_KEY")
SPGW_AZURE_REGION = os.getenv("SPGW_AZURE_REGION") or os.getenv("AZURE_SPEECH_REGION")
SPGW_AZURE_LANGUAGES = os.getenv("SPGW_AZURE_LANGUAGES")
SPGW_AZURE_DEFAULT_SPEAKER = os.getenv("SPGW_AZURE_DEFAULT_SPEAKER")
# OpenAI
SPGW_OPENAI_ENABLED = os.getenv("SPGW_OPENAI_ENABLED", "false").lower() in ("true", "1", "yes")
SPGW_OPENAI_API_KEY = os.getenv("SPGW_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
SPGW_OPENAI_LANGUAGES = os.getenv("SPGW_OPENAI_LANGUAGES")
SPGW_OPENAI_DEFAULT_SPEAKER = os.getenv("SPGW_OPENAI_DEFAULT_SPEAKER")
# VOICEVOX
SPGW_VOICEVOX_ENABLED = os.getenv("SPGW_VOICEVOX_ENABLED", "false").lower() in ("true", "1", "yes")
SPGW_VOICEVOX_URL = os.getenv("SPGW_VOICEVOX_URL")
SPGW_VOICEVOX_LANGUAGES = os.getenv("SPGW_VOICEVOX_LANGUAGES")
SPGW_VOICEVOX_DEFAULT_SPEAKER = os.getenv("SPGW_VOICEVOX_DEFAULT_SPEAKER")
# AivisSpeech
SPGW_AIVISSPEECH_ENABLED = os.getenv("SPGW_AIVISSPEECH_ENABLED", "false").lower() in ("true", "1", "yes")
SPGW_AIVISSPEECH_URL = os.getenv("SPGW_AIVISSPEECH_URL")
SPGW_AIVISSPEECH_LANGUAGES = os.getenv("SPGW_AIVISSPEECH_LANGUAGES")
SPGW_AIVISSPEECH_DEFAULT_SPEAKER = os.getenv("SPGW_AIVISSPEECH_DEFAULT_SPEAKER")
# Style-Bert-VITS2
SPGW_SBV2_ENABLED = os.getenv("SPGW_SBV2_ENABLED", "false").lower() in ("true", "1", "yes")
SPGW_SBV2_URL = os.getenv("SPGW_SBV2_URL")
SPGW_SBV2_LANGUAGES = os.getenv("SPGW_SBV2_LANGUAGES")
SPGW_SBV2_DEFAULT_SPEAKER = os.getenv("SPGW_SBV2_DEFAULT_SPEAKER")
# CoeFont
SPGW_COEFONT_ENABLED = os.getenv("SPGW_COEFONT_ENABLED", "false").lower() in ("true", "1", "yes")
SPGW_COEFONT_ACCESS_KEY = os.getenv("SPGW_COEFONT_ACCESS_KEY")
SPGW_COEFONT_ACCESS_SECRET = os.getenv("SPGW_COEFONT_ACCESS_SECRET")
SPGW_COEFONT_LANGUAGES = os.getenv("SPGW_COEFONT_LANGUAGES")
SPGW_COEFONT_DEFAULT_SPEAKER = os.getenv("SPGW_COEFONT_DEFAULT_SPEAKER")
# Defaults
SPGW_DEFAULT_SERVICE = os.getenv("SPGW_DEFAULT_SERVICE")

# Database
SPGW_DB_HOST = "db"
SPGW_DB_PORT = 5432
SPGW_DB_NAME = os.getenv("SPGW_DB_NAME")
SPGW_DB_USER = os.getenv("SPGW_DB_USER")
SPGW_DB_PASSWORD = os.getenv("SPGW_DB_PASSWORD")

# Configure root logger
logger = logging.getLogger("speech_gateway")
logger.setLevel(SPGW_LOG_LEVEL)
log_format = logging.Formatter("[%(levelname)s] %(asctime)s : %(message)s")
streamHandler = logging.StreamHandler()
streamHandler.setFormatter(log_format)
logger.addHandler(streamHandler)


def create_app() -> FastAPI:
    # Performance recorder
    performance_recorder = PostgreSQLPerformanceRecorder(
        host=SPGW_DB_HOST,
        port=SPGW_DB_PORT,
        dbname=SPGW_DB_NAME,
        user=SPGW_DB_USER,
        password=SPGW_DB_PASSWORD
    )

    # Unified gateway
    unified_gateway = UnifiedGateway(api_key=SPGW_API_KEY, debug=SPGW_DEBUG)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        await unified_gateway.shutdown()

    # Create API app
    app = FastAPI(
        title="Speech Gateway",
        lifespan=lifespan,
    )

    # Register unified gateway router
    app.include_router(unified_gateway.get_router(), tags=["Unified API"])

    # Create service gateways
    if SPGW_AZURE_ENABLED:
        azure_gateway = AzureGateway(
            api_key=SPGW_AZURE_API_KEY,
            cache_dir="/data/cache/azure",
            performance_recorder=performance_recorder,
            region=SPGW_AZURE_REGION,
            debug=SPGW_DEBUG
        )
        unified_gateway.add_gateway(
            service_name="azure",
            gateway=azure_gateway,
            languages=SPGW_AZURE_LANGUAGES.split(",") if SPGW_AZURE_LANGUAGES else None,
            default_speaker=SPGW_AZURE_DEFAULT_SPEAKER,
            default=SPGW_DEFAULT_SERVICE == "azure"
        )
        app.include_router(azure_gateway.get_router(), prefix="/azure", tags=["Azure"])
        logger.info("[Gateway] Azure on /azure")

    if SPGW_OPENAI_ENABLED:
        openai_gateway = OpenAIGateway(
            api_key=SPGW_OPENAI_API_KEY,
            cache_dir="/data/cache/openai",
            performance_recorder=performance_recorder,
            debug=SPGW_DEBUG
        )
        unified_gateway.add_gateway(
            service_name="openai",
            gateway=openai_gateway,
            languages=SPGW_OPENAI_LANGUAGES.split(",") if SPGW_OPENAI_LANGUAGES else None,
            default_speaker=SPGW_OPENAI_DEFAULT_SPEAKER,
            default=SPGW_DEFAULT_SERVICE == "openai"
        )
        app.include_router(openai_gateway.get_router(), prefix="/openai", tags=["OpenAI"])
        logger.info("[Gateway] OpenAI on /openai")

    if SPGW_VOICEVOX_ENABLED:
        voicevox_gateway = VoicevoxGateway(
            base_url=SPGW_VOICEVOX_URL,
            cache_dir="/data/cache/voicevox",
            performance_recorder=performance_recorder,
            debug=SPGW_DEBUG
        )
        unified_gateway.add_gateway(
            service_name="voicevox",
            gateway=voicevox_gateway,
            languages=SPGW_VOICEVOX_LANGUAGES.split(",") if SPGW_VOICEVOX_LANGUAGES else None,
            default_speaker=SPGW_VOICEVOX_DEFAULT_SPEAKER,
            default=SPGW_DEFAULT_SERVICE == "voicevox"
        )
        app.include_router(voicevox_gateway.get_router(), prefix="/voicevox", tags=["VOICEVOX"])
        logger.info("[Gateway] VOICEVOX on /voicevox")

    if SPGW_AIVISSPEECH_ENABLED:
        aivisspeech_gateway = VoicevoxGateway(
            base_url=SPGW_AIVISSPEECH_URL,
            cache_dir="/data/cache/aivis-speech",
            performance_recorder=performance_recorder,
            debug=SPGW_DEBUG
        )
        unified_gateway.add_gateway(
            service_name="aivis-speech",
            gateway=aivisspeech_gateway,
            languages=SPGW_AIVISSPEECH_LANGUAGES.split(",") if SPGW_AIVISSPEECH_LANGUAGES else None,
            default_speaker=SPGW_AIVISSPEECH_DEFAULT_SPEAKER,
            default=SPGW_DEFAULT_SERVICE == "aivis-speech"
        )
        app.include_router(aivisspeech_gateway.get_router(), prefix="/aivis-speech", tags=["Aivis Speech"])
        logger.info("[Gateway] AivisSpeech on /aivis-speech")

    if SPGW_SBV2_ENABLED:
        sbv2_gateway = StyleBertVits2Gateway(
            base_url=SPGW_SBV2_URL,
            cache_dir="/data/cache/sbv2",
            performance_recorder=performance_recorder,
            debug=SPGW_DEBUG
        )
        unified_gateway.add_gateway(
            service_name="sbv2",
            gateway=sbv2_gateway,
            languages=SPGW_SBV2_LANGUAGES.split(",") if SPGW_SBV2_LANGUAGES else None,
            default_speaker=SPGW_SBV2_DEFAULT_SPEAKER,
            default=SPGW_DEFAULT_SERVICE == "sbv2"
        )
        app.include_router(sbv2_gateway.get_router(), prefix="/sbv2", tags=["Style-Bert-VITS2"])
        logger.info("[Gateway] Style-Bert-VITS2 on /sbv2")

    if SPGW_COEFONT_ENABLED:
        coefont_gateway = CoefontGateway(
            access_key=SPGW_COEFONT_ACCESS_KEY,
            access_secret=SPGW_COEFONT_ACCESS_SECRET,
            cache_dir="/data/cache/coefont",
            performance_recorder=performance_recorder,
            debug=SPGW_DEBUG
        )
        unified_gateway.add_gateway(
            service_name="coefont",
            gateway=coefont_gateway,
            languages=SPGW_COEFONT_LANGUAGES.split(",") if SPGW_COEFONT_LANGUAGES else None,
            default_speaker=SPGW_COEFONT_DEFAULT_SPEAKER,
            default=SPGW_DEFAULT_SERVICE == "coefont"
        )
        app.include_router(coefont_gateway.get_router(), prefix="/coefont", tags=["CoeFont"])
        logger.info("[Gateway] CoeFont on /coefont")

    return app

app = create_app()
