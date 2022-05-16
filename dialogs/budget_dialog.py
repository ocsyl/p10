# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Handle date/time resolution for booking dialog."""

from datatypes_date_time.timex import Timex

from botbuilder.core import MessageFactory, BotTelemetryClient, NullTelemetryClient
from botbuilder.dialogs import WaterfallDialog, DialogTurnResult, WaterfallStepContext
from botbuilder.dialogs.prompts import (
    PromptValidatorContext,
    PromptOptions,
)
from .cancel_and_help_dialog import CancelAndHelpDialog
from flight_booking_recognizer import FlightBookingRecognizer
from helpers.luis_helper import LuisHelper, Intent
from botbuilder.schema import InputHints
from botbuilder.dialogs.prompts import ConfirmPrompt, TextPrompt, PromptOptions


class BudgetDialog(CancelAndHelpDialog):
    """Resolve the date"""

    def __init__(
        self,
        dialog_id: str = None,
        telemetry_client: BotTelemetryClient = NullTelemetryClient(),
    ):
        super(BudgetDialog, self).__init__(
            dialog_id or BudgetDialog.__name__, telemetry_client
        )
        self.telemetry_client = telemetry_client

        text_prompt = TextPrompt(TextPrompt.__name__, BudgetDialog.budget_validator)
        text_prompt.telemetry_client = telemetry_client

        waterfall_dialog = WaterfallDialog(
            WaterfallDialog.__name__ + "3", [self.initial_step, self.final_step]
        )
        waterfall_dialog.telemetry_client = telemetry_client

        self.add_dialog(waterfall_dialog)
        self.add_dialog(text_prompt)

        self.initial_dialog_id = WaterfallDialog.__name__ + "3"


    async def initial_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for the date."""

        msg = "What is your budget?"
        reprompt_msg = "I'm sorry, please enter your budget with an amount and optionnaly a devise "

        # ask the budget to the user
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text(msg),
                retry_prompt=MessageFactory.text(reprompt_msg),
            ),
        )  # pylint: disable=line-too-long,bad-continuation


    async def final_step(self, step_context: WaterfallStepContext):
        """Cleanup - set final return value and end dialog."""

        # Capture the response to the previous step's prompt
        budget = step_context.result

        # if budget contains two elements or less, its format was checked in previous step (NUMBER DEVISE)
        if len(step_context.result.split()) <= 2:
            return await step_context.end_dialog(budget)

        # if not luis configured, return the provided budget
        if not self.luis_recognizer.is_configured:
            return await step_context.end_dialog(budget)

        # ask luis to analyze the text
        intent, luis_result = await LuisHelper.execute_luis_query(
            self.luis_recognizer, step_context.context
        )

        # get budget result from luis
        budget_result = None
        if luis_result:
            budget_result = luis_result.budget

        if budget_result is None:
            budget_result = step_context.result

        return await step_context.end_dialog(budget_result)


    @staticmethod
    async def budget_validator(prompt_context: PromptValidatorContext) -> bool:
        """ Validate the budget provided. """
       
        provided_budget = prompt_context.recognized.value
        budget_split = provided_budget.split()

        # if budget len is bigger than two, luis will be asked to find the budget in the text 
        if len(budget_split)>2:
            return True

        # check the budget format : OK : 100, $100, 100$, €100, 100€, 100 dollars, euros 100, 100 pounds...
        number = 0
        alpha = 0
        symbol = 0
        devise = False
        elements = len(budget_split)
        budget_ok = False

        for element in budget_split:
            
            if element.replace(',','.',1).replace('.','',1).isdigit():
                number +=1
                
            if element.isalpha():
                alpha +=1

            if element in ["€", "$"]:
                symbol +=1
                
            if element[:1] in ["€", "$"] :
                symbol +=1
                elements+=1
                if element[1:].isalpha():
                    alpha +=1
                if element[1:].replace(',','.',1).replace('.','',1).isdigit():
                    number +=1

            if element[-1:] in ["€", "$"] :
                symbol +=1
                elements+=1
                if element[:-1].isalpha():
                    alpha +=1
                if element[:-1].replace(',','.',1).replace('.','',1).isdigit():
                    number +=1
                    
                
        if elements == 1:
            if number == 1:
                budget_ok = True
                
        if alpha == 1 or symbol == 1:
            devise = True
                
        if elements == 2:
            if number == 1 and devise:
                budget_ok = True
                    
        return budget_ok

