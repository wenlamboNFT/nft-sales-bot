import asyncio
import json
import logging
import logging.config

from dotenv import load_dotenv

from observer import SaleFinderSubject, FilteredDiscordObserver


load_dotenv()
with open("configs/log_config.json", "r", encoding="UTF-8") as stream:
    config = json.load(stream)
logging.config.dictConfig(config)
logger = logging.getLogger("standard")
with open("configs/config.json", encoding="UTF-8") as g:
    configs = json.load(g)


async def main():
    sale_finder_subject = SaleFinderSubject()

    for channel in configs["channels"]:
        if configs["channels"][channel]["turnedOn"]:
            observer = FilteredDiscordObserver(configs["channels"][channel])
            if configs["channels"][channel]["filter"]:
                observer.set_filter(configs["channels"][channel]["filter"])
            sale_finder_subject.attach(observer)

    while True:
        try:
            await sale_finder_subject.run()
        except Exception as e:
            logger.critical(
                "Something failed horribly. Will try to run again soon", exc_info=True
            )
        finally:
            await sale_finder_subject.api_calls.close_client()

        logger.info(
            "Job is done. Waiting %s seconds.",
            configs["general"]["salesCallIntervalSeconds"],
        )
        await asyncio.sleep(configs["general"]["salesCallIntervalSeconds"])


if __name__ == "__main__":
    asyncio.run(main())
