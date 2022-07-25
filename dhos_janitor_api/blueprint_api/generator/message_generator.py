import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from flask_batteries_included.helpers.timestamp import parse_datetime_to_iso8601

from dhos_janitor_api.data.dhos_messages_data import content

MESSAGE_VALUES = [0, 1, 2, 5]  # Respectively: general, dosage, dietary, callback.


class MessageGenerator:
    patient = None
    clinician = None

    def __init__(self, patient: dict) -> None:
        self.patient = patient

    def generate_message_data(self, number_of_messages: int = 1) -> List[Dict]:
        if self.patient is None:
            raise ValueError("Patient object missing")
        messages: List[Dict] = []
        for _ in range(number_of_messages):
            value = random.choice(MESSAGE_VALUES)
            message_date = self._message_date(
                self.patient["dh_products"][0]["opened_date"]
            )
            if not message_date:
                return messages
            if value <= 2:
                sender = self.patient["locations"][0]
                sender_type = "location"
                receiver = self.patient["uuid"]
                receiver_type = "patient"
            else:
                sender = self.patient["uuid"]
                sender_type = "patient"
                receiver = self.patient["locations"][0]
                receiver_type = "location"

            message_data = {
                "sender": sender,
                "sender_type": sender_type,
                "receiver": receiver,
                "receiver_type": receiver_type,
                "created": parse_datetime_to_iso8601(message_date),
                "created_by_": sender,
                "modified_by_": sender,
                "modified": parse_datetime_to_iso8601(message_date),
                "message_type": {"value": value},
                "content": random.choice(content[value]),
            }
            messages.append(message_data)
        return messages

    def _message_date(self, product_date_iso8601: str) -> Optional[datetime]:

        product_date = datetime.strptime(product_date_iso8601, "%Y-%m-%d")
        date_now = datetime.today()
        if date_now < product_date:
            return None
        elif date_now.date() == product_date.date():
            return product_date
        else:
            date_difference = date_now - product_date
            days = random.randint(0, date_difference.days)
            message_date = (
                date_now - timedelta(days) - timedelta(minutes=self._random_minutes())
            )
            if message_date < product_date:
                return product_date

        return message_date

    def _random_minutes(self) -> int:
        return random.randint(0, 240)
