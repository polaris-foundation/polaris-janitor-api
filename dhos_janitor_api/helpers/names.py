import logging

# Get faker to shut up.
logging.getLogger("faker.factory").setLevel("INFO")

from faker import Faker  # isort:skip

fake = Faker()


def city() -> str:
    return fake.city()


def first_name_female() -> str:
    return fake.first_name_female()


def first_name_male() -> str:
    return fake.first_name_male()


def first_name() -> str:
    return fake.first_name()


def last_name() -> str:
    return fake.last_name()
