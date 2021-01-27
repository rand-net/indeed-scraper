# indeed-scraper

A python script to scrape indeed websites for jobs matching a criterion.

## Installation

```
git clone  https://github.com/rand-net/indeed-scraper
pip install -r requirements.txt
```
## Usage

```
$ python indeed-scraper.py

```
* You can configure scraper parameters in config.yaml.
```
config.yaml

domains_locations:
  https://indeed.co.in:
    [bengaluru]

  https://indeed.com:
    [newyork, michigan]

job_query:
  [python developer,  web developer]

job_sort:
  date

job_age:
  "3"

job_loop_pages:
  2

job_type:
  fulltime, remote

keywords:
  [css, CSS, html, HTML, HTML5, CSS3, illustrator, photoshop, python,  django, flask ]

output:
  data/indeed_jobs.csv

semaphore:
  5
```
