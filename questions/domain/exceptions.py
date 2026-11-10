from datetime import date


class QuestionDateAlreadyTaken(Exception):
    def __init__(self, for_day: date) -> None:
        self.for_day = for_day
        super().__init__(f"A question is already scheduled for {for_day.isoformat()}")
