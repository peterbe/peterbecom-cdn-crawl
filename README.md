**UPDATE**

**This started as an experiment to compare the difference of hitting
`....peterbe.com` via a CDN or not via CDN.**

**Now it's morphed into a simpler tool to just check on the CDN for
one domain.**



# peterbecom-cdn-crawl

This is an experiment to see the performance difference between
`https://www.peterbe.com` (which in April 2019, is a DigitalOcean
server based in NYC, USA) and `https://beta.peterbe.com` (which is a KeyCDN
"zone" CNAME).

The test downloads the 100 most recent blog posts with Brotli (`Accept-Encoding`)
and after a while starts spitting out comparison stats.

## Install

Python 3 with `requests` and `pyquery` installed. Then run:

    python cdn-crawler.py

Between each `requests.get()` there's a 3 sec sleep. You can change to to,
5.5 for example like this:

    echo 5.5 > cdn-crawler-sleeptime

The stats are printed after every 10 iterations. You can change that,
for example, to 20 like this:

    echo 20 > cdn-crawler-report-every
