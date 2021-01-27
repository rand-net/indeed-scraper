from indeed import *
import asyncio
import yaml


def get_all_jobs():
    with open("config.yaml", "r") as stream:
        try:
            config = yaml.safe_load(stream)
            # print(config)
        except yaml.YAMLError as exc:
            print(exc)

    print(config)
    scraper = IndeedScraper(
        config["domains_locations"],
        config["job_query"],
        config["job_sort"],
        config["job_age"],
        config["job_loop_pages"],
        config["job_type"],
        config["keywords"],
        config["output"],
    )

    # Get all the values for the job_page_urls_builder as separate lists
    (
        job_async_urls,
        job_async_sites,
        job_async_locations,
        job_async_queries,
    ) = scraper.job_page_urls_builder()

    # Debug Values
    # i = 0
    # for url, site, location, query in zip(
    # job_async_urls, job_async_sites, job_async_locations, job_async_queries
    # ):
    # i = i + 1
    # print(job_async_urls, job_async_sites, job_async_urls, job_async_queries)

    # print(i)

    # Asynchronous get_job_details function call
    loop = asyncio.get_event_loop()

    sem = asyncio.Semaphore(config["semaphore"])
    loop.run_until_complete(
        asyncio.gather(
            *(
                scraper.get_job_details(url, site, location, query, sem)
                for url, site, location, query in zip(
                    job_async_urls,
                    job_async_sites,
                    job_async_locations,
                    job_async_queries,
                )
            )
        )
    )


get_all_jobs()
