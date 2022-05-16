from aiounittest import AsyncTestCase

from botbuilder.ai.luis import LuisRecognizer
from flight_booking_recognizer import FlightBookingRecognizer
from helpers.luis_helper import LuisHelper

from botbuilder.core.adapters import TestAdapter

from botbuilder.core import (
    BotAdapter,
    TurnContext,
)

from botbuilder.schema import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    ConversationAccount,
)

from config import DefaultConfig


class LuisRecognizerTest(AsyncTestCase):
    """
    This class contains 4 tests:
    - test luis recognizer setting
    - test the luis recognizer with a complete query
    - test the luis recognizer with a partial query
    - test the luis recognizer with an inappropriate query
    """

    default_config = DefaultConfig()

    _luisAppId: str = default_config.LUIS_APP_ID
    _subscriptionKey: str = default_config.LUIS_API_KEY
    _endpoint: str = "https://" + default_config.LUIS_API_HOST_NAME
    

    def test_luis_recognizer_construction(self):
        """
        This test check the recognizer setting from an str endpoint 
        """

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


    async def test_complete_booking_query(self):
        """
        This test checks the recognizer returns all entities and book intent with a complete query
        """

        luis_recognizer = FlightBookingRecognizer(self.default_config)
        utterance: str = "I want travel from Paris to Roma from August 18 2022 to August 29 with budget of 500$" 

        # Call LUIS and gather any potential booking details.
        context = LuisRecognizerTest._get_context(utterance, TestAdapter())
        intent, luis_result = await LuisHelper.execute_luis_query(
            luis_recognizer, context
        )

        self.assertIsNotNone(luis_result)
        self.assertIsNotNone(intent)
        self.assertEqual("book", intent)
        self.assertIsNotNone(luis_result.origin)
        self.assertIsNotNone(luis_result.destination)
        self.assertIsNotNone(luis_result.str_date)
        self.assertIsNotNone(luis_result.end_date)
        self.assertIsNotNone(luis_result.budget)
        self.assertEqual("Roma", luis_result.destination)
        self.assertEqual("Paris", luis_result.origin)
        self.assertEqual("august 18 2022", luis_result.str_date)
        self.assertEqual("august 29", luis_result.end_date)
        self.assertEqual("500 $", luis_result.budget)


    async def test_partial_booking_query(self):
        """
        This test checks the recognizer returns good entities and book intent with a partial query
        """

        luis_recognizer = FlightBookingRecognizer(self.default_config)
        utterance: str = "I want travel to London and my budget is 1500$" 

        # Call LUIS and gather any potential booking details.
        context = LuisRecognizerTest._get_context(utterance, TestAdapter())
        intent, luis_result = await LuisHelper.execute_luis_query(
            luis_recognizer, context
        )

        self.assertIsNotNone(luis_result)
        self.assertIsNotNone(intent)
        self.assertEqual("book", intent)
        self.assertIsNone(luis_result.origin)
        self.assertIsNotNone(luis_result.destination)
        self.assertIsNone(luis_result.str_date)
        self.assertIsNone(luis_result.end_date)
        self.assertIsNotNone(luis_result.budget)
        self.assertEqual("London", luis_result.destination)
        self.assertEqual("1500 $", luis_result.budget)


    async def test_not_book_intent_query(self):
        """
        This test checks the recognizer returns no result and None intent with an inappropriate query
        """

        luis_recognizer = FlightBookingRecognizer(self.default_config)

        # this query is not recognized as a book intent
        utterance: str = "ljflgjldfk" 

        # Call LUIS and gather any potential booking details.
        context = LuisRecognizerTest._get_context(utterance, TestAdapter())
        intent, luis_result = await LuisHelper.execute_luis_query(
            luis_recognizer, context
        )

        # self.assertIsNone(intent)
        self.assertEqual("None", intent)
        self.assertIsNone(luis_result)


    @staticmethod
    def _get_context(utterance: str, bot_adapter: BotAdapter) -> TurnContext:
        activity = Activity(
            type=ActivityTypes.message,
            text=utterance,
            conversation=ConversationAccount(),
            recipient=ChannelAccount(),
            from_property=ChannelAccount(),
        )
        return TurnContext(bot_adapter, activity)
