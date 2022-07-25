from datetime import date, datetime, timedelta

import pytest

from dhos_janitor_api.blueprint_api.generator.message_generator import MessageGenerator


@pytest.mark.usefixtures("app")
class TestMessageGenerator:
    def test_message_date(self) -> None:
        date_working = date.today() - timedelta(days=2)
        product_date = date_working.strftime("%Y-%m-%d")
        message_generator = MessageGenerator({"uuid": "1"})
        message_date = message_generator._message_date(product_date)
        date_now = datetime.today()
        assert message_date is not None
        assert message_date <= date_now

    def test_generate_message_data(self) -> None:
        patient = {
            "uuid": "555",
            "dh_products": [{"opened_date": "2018-08-20"}],
            "locations": ["locationuuid"],
        }
        message_data = MessageGenerator(patient)
        messages = message_data.generate_message_data(number_of_messages=1)
        for message in messages:
            assert message["receiver"] in ["locationuuid", "555", "F"]
