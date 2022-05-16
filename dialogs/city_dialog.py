# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Handle date/time resolution for booking dialog."""

from datatypes_date_time.timex import Timex

from botbuilder.core import MessageFactory, BotTelemetryClient, NullTelemetryClient
from botbuilder.dialogs import WaterfallDialog, DialogTurnResult, WaterfallStepContext
from botbuilder.dialogs.prompts import (
    PromptOptions,
)
from .cancel_and_help_dialog import CancelAndHelpDialog
from flight_booking_recognizer import FlightBookingRecognizer
from helpers.luis_helper import LuisHelper, Intent
from botbuilder.schema import InputHints
from botbuilder.dialogs.prompts import ConfirmPrompt, TextPrompt, PromptOptions


class CityDialog(CancelAndHelpDialog):
    """Resolve the date"""

    def __init__(
        self,
        dialog_id: str = None,
        telemetry_client: BotTelemetryClient = NullTelemetryClient(),
    ):
        super(CityDialog, self).__init__(
            dialog_id or CityDialog.__name__, telemetry_client
        )

        self.telemetry_client = telemetry_client

        text_prompt = TextPrompt(TextPrompt.__name__)
        text_prompt.telemetry_client = telemetry_client

        waterfall_dialog = WaterfallDialog(
            WaterfallDialog.__name__ + "4", [self.initial_step, self.final_step]
        )
        waterfall_dialog.telemetry_client = telemetry_client

        self.add_dialog(waterfall_dialog)
        self.add_dialog(text_prompt)

        self.initial_dialog_id = WaterfallDialog.__name__ + "4"


    async def initial_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for the date."""

        if self.id == "city_destination":
            msg = "To what city would you like to travel?"
        else:
            # if self.id == "city_origin":
            msg = "From what city will you be travelling?"

        # ask the city to the user
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text(msg),
            ),
        )  # pylint: disable=line-too-long,bad-continuation



    async def final_step(self, step_context: WaterfallStepContext):
        """Cleanup - set final return value and end dialog."""

        # Capture the response to the previous step's prompt
        city = step_context.result

        # if the provided city len is 1, return the provided text
        if len(step_context.result.split())==1:
            return await step_context.end_dialog(city)

        # if not luis configured, return the provided text
        if not self.luis_recognizer.is_configured:
            return await step_context.end_dialog(city)

        # ask luis to analyze the text
        intent, luis_result = await LuisHelper.execute_luis_query(
            self.luis_recognizer, step_context.context
        )

        # get city result from luis
        city_result = None
        if luis_result:
            if self.id == "city_destination":
                city_result = luis_result.destination
            else:
                # if self.id == "city_origin":
                city_result = luis_result.origin

        if city_result is None:
            city_result = step_context.result

        return await step_context.end_dialog(city_result)
        



