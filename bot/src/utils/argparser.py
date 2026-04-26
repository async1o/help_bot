import argparse

from src.db.db import reset_tables, create_tables


async def add_args():

    parser = argparse.ArgumentParser()

    parser.add_argument("--create_tables", action="store_true")
    parser.add_argument("--reset_tables", action="store_true")

    args = parser.parse_args()

    if args.create_tables:
        await create_tables()

    if args.reset_tables:
        await reset_tables()
