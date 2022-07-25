from datetime import date


def generate_patient(location_uuid: str, clinician_uuid: str) -> dict:
    return {
        "first_name": "Dummy",
        "last_name": "Patient",
        "phone_number": "07594203248",
        "allowed_to_text": False,
        "allowed_to_email": False,
        "dob": "1957-06-09",
        "hospital_number": "435y3948",
        "email_address": "dummypatient@hotmail.co.uk",
        "dh_products": [
            {
                "product_name": "GDM",
                "opened_date": "2018-06-22",
                "accessibility_discussed": True,
                "accessibility_discussed_with": clinician_uuid,
                "accessibility_discussed_date": "2018-06-22",
            }
        ],
        "sex": "248152002",
        "accessibility_considerations": None,
        "record": {
            "pregnancies": [{"estimated_delivery_date": date.today().isoformat()}],
            "diagnoses": [
                {
                    "sct_code": "11687002",
                    "diagnosed": "2018-06-22",
                    "risk_factors": [],
                    "management_plan": {
                        "start_date": "2018-06-22",
                        "end_date": "2018-9-11",
                        "sct_code": "D0000007",
                        "doses": [],
                    },
                    "readings_plan": {
                        "sct_code": "33747003",
                        "start_date": "2018-06-22",
                        "end_date": "2018-9-11",
                        "days_per_week_to_take_readings": 4,
                        "readings_per_day": 4,
                    },
                    "observable_entities": [
                        {
                            "sct_code": "113076002",
                            "date_observed": "2021-01-01",
                            "value_as_string": "65",
                            "metadata": {
                                "0hr": 50,
                                "1hr": 100,
                                "2hr": 75,
                            },
                        },
                        {
                            "sct_code": "113076002",
                            "date_observed": "2021-01-01",
                        },
                    ],
                }
            ],
        },
        "locations": [location_uuid],
    }


def generate_clinician(location_uuid: str) -> dict:
    return {
        "first_name": "Dummy",
        "last_name": "Clinician",
        "phone_number": "07123456770",
        "nhs_smartcard_number": "211213",
        "email_address": "dummyclinician@hotmail.com",
        "job_title": "winner",
        "locations": [location_uuid],
        "groups": ["GDM Clinician"],
        "products": [{"product_name": "GDM", "opened_date": "2017-01-01"}],
    }
