import json
from os import path
from typing import Dict, Tuple, Union
from unittest import mock
from unittest.mock import MagicMock, Mock

from aiounittest import AsyncTestCase
from msrest import Deserializer
from requests import Session
from requests.models import Response

from botbuilder.ai.luis import LuisApplication, LuisPredictionOptions, LuisRecognizer
from botbuilder.ai.luis.luis_util import LuisUtil
from botbuilder.core import (
    BotAdapter,
    BotTelemetryClient,
    IntentScore,
    RecognizerResult,
    TurnContext,
)
from botbuilder.core.adapters import TestAdapter
from botbuilder.schema import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    ConversationAccount,
)
from config import DefaultConfig


class LuisRecognizerTest(AsyncTestCase):
    default_config = DefaultConfig()

    _luisAppId: str = default_config.LUIS_APP_ID
    _subscriptionKey: str = default_config.LUIS_API_KEY
    _endpoint: str = "https://" + default_config.LUIS_API_HOST_NAME

    def test_luis_recognizer_construction(self):
            # Arrange
            endpoint = (
                LuisRecognizerTest._endpoint + "/luis/v2.0/apps/"
                + LuisRecognizerTest._luisAppId + "?verbose=true&timezoneOffset=-360"
                "&subscription-key=" + LuisRecognizerTest._subscriptionKey + "&q="
            )

            # Act
            recognizer = LuisRecognizer(endpoint)

            # Assert
            app = recognizer._application
            self.assertEqual(LuisRecognizerTest._luisAppId, app.application_id)
            self.assertEqual(LuisRecognizerTest._subscriptionKey, app.endpoint_key)
            self.assertEqual(LuisRecognizerTest._endpoint, app.endpoint)
