# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Flight booking dialog."""

from datatypes_date_time.timex import Timex

from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult
from botbuilder.dialogs.prompts import ConfirmPrompt, TextPrompt, PromptOptions
from botbuilder.core import MessageFactory, BotTelemetryClient, NullTelemetryClient
from botbuilder.schema import InputHints
from .cancel_and_help_dialog import CancelAndHelpDialog
from .date_resolver_dialog import DateResolverDialog
from .city_dialog import CityDialog
from .budget_dialog import BudgetDialog


class BookingDialog(CancelAndHelpDialog):
    """Flight booking implementation."""

    def __init__(
        self,
        dialog_id: str = None,
        telemetry_client: BotTelemetryClient = NullTelemetryClient(),
    ):
        super(BookingDialog, self).__init__(
            dialog_id or BookingDialog.__name__, telemetry_client
        )
        self.telemetry_client = telemetry_client

        text_prompt = TextPrompt(TextPrompt.__name__)
        text_prompt.telemetry_client = telemetry_client

        waterfall_dialog = WaterfallDialog(
            WaterfallDialog.__name__,
            [
                self.destination_step,
                self.origin_step,
                self.str_date_step,
                self.end_date_step,
                self.budget_step,
                self.confirm_step,
                self.final_step,
            ],
        )
        waterfall_dialog.telemetry_client = telemetry_client

        self.city_destination_dialog = CityDialog("city_destination", self.telemetry_client)
        self.city_origin_dialog = CityDialog("city_origin", self.telemetry_client)
        self.str_date_dialog = DateResolverDialog("str_date", self.telemetry_client)
        self.end_date_dialog = DateResolverDialog("end_date", self.telemetry_client)
        self.budget_dialog = BudgetDialog("budget", self.telemetry_client)

        self.add_dialog(text_prompt)
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.add_dialog(self.str_date_dialog)
        self.add_dialog(self.end_date_dialog)
        self.add_dialog(self.city_destination_dialog)
        self.add_dialog(self.city_origin_dialog)
        self.add_dialog(self.budget_dialog)
        self.add_dialog(waterfall_dialog)

        self.initial_dialog_id = WaterfallDialog.__name__


    async def destination_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for destination."""

        booking_details = step_context.options

        # start city dialog
        if booking_details.destination is None:
            self.city_destination_dialog.luis_recognizer = self.luis_recognizer
            return await step_context.begin_dialog(
                 self.city_destination_dialog.id, booking_details.destination
            )  # pylint: disable=line-too-long,bad-continuation

        return await step_context.next(booking_details.destination)


    async def origin_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt for origin city."""

        booking_details = step_context.options

       # Capture the response to the previous step's prompt
        booking_details.destination = step_context.result

        # start city dialog
        if booking_details.origin is None:
            self.city_origin_dialog.luis_recognizer = self.luis_recognizer
            return await step_context.begin_dialog(
                 self.city_origin_dialog.id, booking_details.origin
            )  # pylint: disable=line-too-long,bad-continuation

        return await step_context.next(booking_details.origin)


    async def str_date_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for travel date.
        This will use the DATE_RESOLVER_DIALOG."""

        booking_details = step_context.options

        # Capture the results of the previous step
        booking_details.origin = step_context.result

        # start date resolver dialog
        if not booking_details.str_date or self.is_ambiguous(
            booking_details.str_date
        ):
            return await step_context.begin_dialog(
                self.str_date_dialog.id, booking_details.str_date
            )  # pylint: disable=line-too-long

        return await step_context.next(booking_details.str_date)


    async def end_date_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for travel date.
        This will use the DATE_RESOLVER_DIALOG."""

        booking_details = step_context.options

        # Capture the results of the previous step
        booking_details.str_date = step_context.result

        # start date resolver dialog
        if not booking_details.end_date or self.is_ambiguous(
            booking_details.end_date
        ):
            return await step_context.begin_dialog(
                self.end_date_dialog.id, booking_details.end_date
            )  # pylint: disable=line-too-long

        return await step_context.next(booking_details.end_date)


    async def budget_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt for origin city."""

        booking_details = step_context.options

        # Capture the response to the previous step's prompt
        booking_details.end_date = step_context.result

        # start budget dialog
        if booking_details.budget is None:
            self.budget_dialog.luis_recognizer = self.luis_recognizer
            return await step_context.begin_dialog(
                 self.budget_dialog.id, booking_details.budget
            )  # pylint: disable=line-too-long,bad-continuation

        return await step_context.next(booking_details.budget)


    async def confirm_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Confirm the information the user has provided."""

        booking_details = step_context.options

        # Capture the results of the previous step
        booking_details.budget = step_context.result

        msg = (
            f"Please confirm, I have you traveling to: { booking_details.destination }"
            f" from: { booking_details.origin } on date from: { booking_details.str_date}"
            f" to: { booking_details.end_date } with a budget of: { booking_details.budget}"
        )

        # Offer a YES/NO prompt.
        return await step_context.prompt(
            ConfirmPrompt.__name__, PromptOptions(prompt=MessageFactory.text(msg))
        )

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Complete the interaction and end the dialog."""

        booking_details = step_context.options

        # positive response
        if step_context.result:
            return await step_context.end_dialog(booking_details)

        # negative response : send datas to app insight
        properties = {}
        properties['init_message'] = booking_details.initial_message
        properties['destination'] = booking_details.destination
        properties['origin'] = booking_details.origin
        properties['str_date'] = booking_details.str_date
        properties['end_date'] = booking_details.end_date
        properties['budget'] = booking_details.budget
        self.telemetry_client.track_trace("BOOKING NOT CONFIRMED", properties, "ERROR")

        msg = (
            "Sorry you didn't book, I hope I will help you next time"
        )
        message = MessageFactory.text(
            msg, msg, InputHints.ignoring_input
        )
        await step_context.context.send_activity(message)


        return await step_context.end_dialog()


    def is_ambiguous(self, timex: str) -> bool:
        """Ensure time is correct."""
        timex_property = Timex(timex)
        return "definite" not in timex_property.types
