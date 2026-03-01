# Web Scraper

A small command-line web scraper that lets you choose options such as:
- target URL
- selector (`tag`, `.class`, `#id`, `tag.class`, `tag#id`)
- optional attribute to extract (e.g. `href`)
- optional keyword filtering
- optional result limit
- output format (`json` or `csv`)

## Setup

```bash
python web_scraper.py --help
```

## Where do I insert the URL?

Put it in the `--url` flag:

```bash
python web_scraper.py --url "https://example.com" --selector "a" --attr "href"
```

If you skip `--url`, the script will ask you interactively:

```bash
python web_scraper.py --selector "a" --attr "href"
# Enter the page URL to scrape: https://example.com
```

## Usage

Extract all links from a page:

```bash
python web_scraper.py \
  --url "https://example.com" \
  --selector "a" \
  --attr "href"
```

Filter only entries containing a keyword:

```bash
python web_scraper.py \
  --url "https://example.com" \
  --selector "a" \
  --attr "href" \
  --contains "more" \
  --limit 20 \
  --format json
```

Write to CSV:

```bash
python web_scraper.py \
  --url "https://example.com" \
  --selector "a" \
  --attr "href" \
  --format csv \
  --out links.csv
```

## Notes

- This script supports **simple selectors only** (no full CSS combinators).
- For JS-heavy pages, use a browser automation tool (e.g. Playwright/Selenium).
