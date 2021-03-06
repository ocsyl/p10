# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


class BookingDetails:
    def __init__(
        self,
        initial_message: str = None,
        destination: str = None,
        origin: str = None,
        str_date: str = None,
        end_date: str = None,
        budget: str = None,
        unsupported_airports=None,
    ):
        if unsupported_airports is None:
            unsupported_airports = []
        self.initial_message = initial_message
        self.destination = destination
        self.origin = origin
        self.str_date = str_date
        self.end_date = end_date
        self.budget = budget
        self.unsupported_airports = unsupported_airports
