from bs4 import BeautifulSoup
from datetime import timedelta
import aiohttp
import csv
import datetime
import re


class IndeedScraper:
    """
    A class to scrape Indeed Job listings

    Attributes
    ----------
    job_domain_with_locations : dict
    job_queries : list
    job_sort_order: str
    job_age :str
    job_loop_pages :int
    job_types :list
    job_desc_keyword_list : list
    csv_path : str

    """

    def __init__(
        self,
        job_domains_with_locations,
        job_queries,
        job_sort,
        job_age,
        job_pages_to_loop,
        job_working_types,
        job_desc_keyword_list,
        csv_path,
    ):

        # Initialize all the instance's variables
        self.job_domains_with_locations = job_domains_with_locations
        self.job_queries = job_queries
        self.job_sort = job_sort
        self.job_age = job_age
        self.job_pages_to_loop = job_pages_to_loop
        self.job_working_types = job_working_types
        self.job_desc_keyword_list = job_desc_keyword_list
        self.csv_path = csv_path

    def job_page_urls_builder(self):
        """
        Builds Indeed URL list to be queried

        Parameters:
            self: instance

        Returns:
            job_pages_to_query_urls(list): List of indeed URLs to scrape for job
                                            listings
            job_query_domains(list): List of indeed domains depending upon the
                                        url
            job_query_locations(list): List of locations for the url
            job_alt_queries(list): List of job queries

        """

        job_pages_to_query_urls = []
        job_query_domains = []
        job_query_locations = []
        job_alt_queries = []

        # (Domain, (Query Locations)) pair
        for key, values in self.job_domains_with_locations.items():

            # (Domain, (Query Locations)[0]) pair
            for location in values:

                # (Domain, (Query Locations)[0], Job_Queries[0]) pair
                for queries in self.job_queries:

                    # (Domain, (Query Locations)[0], Job_Queries[0], Job_Types[0]) pair
                    for job_alt_types in self.job_working_types:

                        # (Domain, (Query Locations)[0], Job_Queries[0], Job_Types[0], Job_Pages[10 in increments]) pair
                        for pages in range(10, self.job_pages_to_loop * 10, 10):

                            # Builds the query with variables and append it to a list
                            job_pages_to_query_urls.append(
                                key
                                + "/jobs?q="
                                + queries.replace(" ", "+")
                                + "&l="
                                + location
                                + "&sort="
                                + self.job_sort
                                + "&start="
                                + str(pages)
                                + "&jt="
                                + job_alt_types
                                + "&fromage="
                                + self.job_age
                            )

                            job_query_domains.append(key)  # Indeed Domain
                            job_query_locations.append(location)  # Job Query Location
                            job_alt_queries.append(queries)  # Job Query

        return (
            job_pages_to_query_urls,
            job_query_domains,
            job_query_locations,
            job_alt_queries,
        )

    async def get_job_details(
        self, job_query_page_url, job_domain, job_query_location, job_query, sem
    ):
        """
        Asynchronous function that gets HTML from URL list and returns job
        details as CSV

        Parameters:
            job_query_page_url(list): List of urls of the job listing pages
            job_domain(list) : List of domains as per the url
            job_query_location(list): List of locations as per the url
            job_query(list): List of job queries


        """

        # Asynchronous Requests with async+aiohttp+beautifulsoup
        async with aiohttp.ClientSession() as session:
            async with sem, session.get(job_query_page_url) as resp:
                page_source = await resp.text()
                page_html = BeautifulSoup(page_source, "lxml")

        # Appends to the CSV File/creates the CSV File if not present
        csv_file = open("%s" % self.csv_path, "a+")
        csv_writer = csv.writer(csv_file)

        # Get all the information about the job from a given page URL and writes
        # to CSV
        # print(page_html) # To Test if the IP is blocked and is having google
        # captcha problem

        # Get the job description page URL and job descriptions
        for job_blocks in page_html.find_all("div", class_="jobsearch-SerpJobCard"):
            job_desc_page_url = self.get_job_desc_page_url(job_blocks, job_domain)

            async with aiohttp.ClientSession() as session_ii:
                async with sem, session_ii.get(job_desc_page_url) as resp_ii:
                    job_desc_page_source = await resp_ii.text()
                    job_desc_html = BeautifulSoup(job_desc_page_source, "lxml")
                    try:
                        job_desc = job_desc_html.find(
                            "div", class_="jobsearch-jobDescriptionText"
                        ).text
                    except:
                        job_desc = "empty"

            job_desc_search = job_desc.replace(",", "").replace(".", "")

            # Check Whether Job Description Contains Keywords
            job_desc_got_keywords = "False"
            if set(self.job_desc_keyword_list).intersection(
                str(job_desc_search).split()
            ):
                job_desc_got_keywords = "True"

            # Console Output
            print(
                self.get_job_title(job_blocks),
                self.get_company_name(job_blocks),
                self.get_job_posted_date(job_blocks),
                self.get_job_location(job_blocks),
                self.get_job_salary(job_blocks),
                self.get_job_desc_page_url(job_blocks, job_domain),
                job_desc,
                job_desc_got_keywords,
            )

            csv_writer.writerow(
                [
                    self.get_job_title(job_blocks),
                    self.get_company_name(job_blocks),
                    self.get_job_location(job_blocks),
                    self.get_job_salary(job_blocks)[0],  # Min Salary
                    self.get_job_salary(job_blocks)[1],  # Max Salary
                    self.get_job_desc_page_url(job_blocks, job_domain),
                    self.get_job_posted_date(job_blocks),  # Job posted date
                    datetime.datetime.now(),
                    job_desc,
                    job_desc_got_keywords,
                    job_query,
                    job_query_location,
                    job_domain,
                ]
            )

    def get_job_title(self, job_card_html):
        """ Returns the job title """
        return str(job_card_html.find("h2", class_="title").a.text)

    def get_company_name(self, job_card_html):
        """ Returns the company name of the job        """
        return job_card_html.find("div", class_="sjcl").div.span.text

    def get_job_posted_date(self, job_card_html):
        """ Returns the date on which the job listing is posted        """

        days_before = job_card_html.find("span", class_="date").text
        days_before = (
            days_before.replace("Just posted", "0")
            .replace("Today", "0")
            .replace("today", "0")
            .replace("days", "")
            .replace("day", "")
            .replace("ago", "")
        )
        days_before = int(days_before)

        job_posted_date = datetime.datetime.now() - timedelta(days=days_before)
        job_posted_date = job_posted_date.strftime("%d/%m/%Y")
        return job_posted_date

    def get_job_location(self, job_card_html):
        """ Returns the location of the company for a job        """

        job_location = job_card_html.find("span", class_="location")
        clean_regex = re.compile("<.*?>")
        job_location = str(job_location)
        job_location = re.sub(clean_regex, "", job_location)
        return job_location

    def get_job_salary(self, job_card_html):
        """ Returns the min salary and max salary of the job        """

        job_salary = job_card_html.find("span", class_="salaryText")
        clean_regex = re.compile("<.*?>")
        job_salary = str(job_salary)
        job_salary = re.sub(clean_regex, "", job_salary)

        job_salary = (
            job_salary.replace("\n", "")
            .replace("$", "")
            .replace("hour", "")
            .replace("From", "")
            .replace("None", "0")
            .replace(",", "")
            .replace("₹", "")
        )

        if "month" in job_salary:
            job_salary = job_salary.replace("a month", "")

            # Cal Min Salary for month
            try:
                job_min_salary = int(job_salary.split(" ")[0])
            except:
                job_min_salary = 0

            # Cal Max Salary for month
            try:
                job_max_salary = int(job_salary.split(" ")[2])
            except:
                job_max_salary = 0

        elif "year" in job_salary:
            job_salary = job_salary.replace("a year", "")

            # Cal Min Salary for year
            try:
                job_min_salary = int(job_salary.split(" ")[0]) / 12
            except:
                job_min_salary = 0

            # Cal Max Salary for year
            try:
                job_max_salary = int(job_salary.split(" ")[2]) / 12
            except:
                job_max_salary = 0

        else:
            job_min_salary = 0
            job_max_salary = 0

        return (job_min_salary, job_max_salary)

    def get_job_desc_page_url(self, job_card_html, query_site):
        """ Returns the url of job description page        """
        job_desc_page_url = job_card_html.find("h2", class_="title").a["href"]
        job_desc_page_url = str(job_desc_page_url)
        job_desc_page_url = query_site + job_desc_page_url
        return job_desc_page_url
