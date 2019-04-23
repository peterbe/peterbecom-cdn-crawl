#!/usr/bin/env python

import json
import random
import time
import statistics
from collections import defaultdict

import requests
from pyquery import PyQuery


def get_urls(base_url, exclude=set()):
    urls = []
    if base_url.endswith("/"):
        base_url = base_url[:-1]
    doc = PyQuery(base_url + "/plog/")
    doc.make_links_absolute(base_url=base_url)
    for a in doc("dd a"):
        href = a.attrib["href"]
        if href in exclude:
            continue
        urls.append(href)
        if len(urls) > 100:
            break

    return urls


def get_sleeptime(default=2.5):
    try:
        with open("cdn-crawler-sleeptime") as f:
            return float(f.read().strip())
    except FileNotFoundError:
        return default


def stats(responses, last=100):
    def t(s):
        return ("\t" + s).ljust(20)

    def f(s):
        return "{:.2f}ms".format(s * 1000)

    for prefix in sorted(responses):
        print(prefix)
        values = responses[prefix]
        if len(values) < 3:
            print("\tNot enough data")
            continue
        if len(values) > last:
            print(t("COUNT"), len(values), "(but only using the last {})".format(last))
            values = values[-last:]
        else:
            print(t("COUNT"), len(values))

        if any([x["cache"] for x in values]):
            hits = len([x for x in values if x["cache"] == "HIT"])
            misses = len([x for x in values if x["cache"] == "MISS"])
            print(t("HIT RATIO"), "{:.1f}%".format(100 * hits / (hits + misses)))
            print(t("AVERAGE (all)"), f(statistics.mean([x["took"] for x in values])))
            print(t("MEDIAN (all)"), f(statistics.median([x["took"] for x in values])))
            try:
                print(
                    t("AVERAGE (misses)"),
                    f(
                        statistics.mean(
                            [x["took"] for x in values if x["cache"] == "MISS"]
                        )
                    ),
                )
                print(
                    t("MEDIAN (misses)"),
                    f(
                        statistics.median(
                            [x["took"] for x in values if x["cache"] == "MISS"]
                        )
                    ),
                )
                print(
                    t("AVERAGE (hits)"),
                    f(
                        statistics.mean(
                            [x["took"] for x in values if x["cache"] == "HIT"]
                        )
                    ),
                )
                print(
                    t("MEDIAN (hits)"),
                    f(
                        statistics.median(
                            [x["took"] for x in values if x["cache"] == "HIT"]
                        )
                    ),
                )
            except statistics.StatisticsError as exc:
                print(exc)
        else:
            hits = len([x for x in values if x["link"]])
            misses = len([x for x in values if not x["link"]])
            print(t("HIT RATIO"), "{:.1f}%".format(100 * hits / (hits + misses)))
            print(t("AVERAGE"), f(statistics.mean([x["took"] for x in values])))
            print(t("MEDIAN"), f(statistics.median([x["took"] for x in values])))

    with open("cdn-crawler-stats.json", "w") as f:
        json.dump(responses, f, indent=3)


def probe(url):
    t0 = time.time()
    r = requests.get(
        url,
        headers={
            "User-Agent": "cdn-crawler.py",
            "Accept-Encoding": "br, gzip, deflate",
        },
    )
    r.raise_for_status()
    t1 = time.time()
    print(
        url.ljust(100),
        "{:.2f}ms".format((t1 - t0) * 1000),
        str(r.headers.get("x-cache")).ljust(6),
        "Nginx" if r.headers.get("link") and not r.headers.get("x-cache") else "",
    )
    return {
        "took": t1 - t0,
        "cache": r.headers.get("x-cache"),
        "link": r.headers.get("link"),
    }


def get_report_every(default=10):
    try:
        with open("cdn-crawler-report-every") as f:
            return int(f.read().strip())
    except FileNotFoundError:
        return default


def run():
    try:
        with open("cdn-crawler-stats.json") as f:
            responses = json.load(f)
            print(
                "Continuing with {} + {} responses".format(
                    *[len(v) for v in responses.values()]
                )
            )
    except FileNotFoundError:
        responses = defaultdict(list)
    urls = get_urls("https://www.peterbe.com")
    while 1:
        try:
            random.shuffle(urls)
            c = 0
            for url in urls:
                c += 1
                responses["www"].append(probe(url))
                time.sleep(get_sleeptime())
                responses["beta"].append(probe(url.replace("www.", "beta.")))
                time.sleep(get_sleeptime())
                if not c % get_report_every():
                    stats(responses)
        except KeyboardInterrupt:
            print("One last time...")
            stats(responses)
            return 0


if __name__ == "__main__":
    import sys

    sys.exit(run())
