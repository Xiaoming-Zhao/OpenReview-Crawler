#! /usr/bin/env python
#################################################################################
#     File Name           :     ICLR2020/crawler.py
#     Created By          :     Xiaoming Zhao
#     Last Modified       :     [2020-04-27 00:23]
#     Description         :     web crawler for ICLR 2020
#################################################################################


import os
import pickle
import argparse
from bs4 import BeautifulSoup
# from urllib.request import urlopen
from typing import List, Dict
from time import sleep
from collections import defaultdict
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options


OPENREVIEW_URL = "https://openreview.net"

POSTER_URL = "https://openreview.net/group?id=ICLR.cc/2020/Conference#accept-poster"
SPOTLIGHT_URL = "https://openreview.net/group?id=ICLR.cc/2020/Conference#accept-spotlight"
ORAL_URL = "https://openreview.net/group?id=ICLR.cc/2020/Conference#accept-talk"
URL_DICT = {"poster": POSTER_URL, "spotlight": SPOTLIGHT_URL, "talk": ORAL_URL}

DRIVER_PATH = "/Users/apple/Documents/ChromeDriver/chromedriver"


def get_ratings(openreview_url: str,
                url_dict: Dict[str, str],
                driver_path: str,
                save_f: str):

    paper_infos = defaultdict(dict)

    for track, base_url in tqdm(url_dict.items()):

        # generate webpage for listing all papers
        options = Options()
        options.add_argument("--headless")
        browser = webdriver.Chrome(options=options, executable_path=driver_path)
        browser.get(base_url)
        sleep(10)

        # find the div where paper titles etc locate
        content_element = browser.find_element_by_class_name("tab-content")
        content_html = content_element.get_attribute("innerHTML")

        # print(content_element)

        # get detailed HTML
        soup = BeautifulSoup(content_html, "html.parser")
        div_tags = soup.find_all("div", id=f"accept-{track}")
        # print(f"accept-{track}")
        li_papers = div_tags[0].find_all("li", class_="note")

        N = len(li_papers)
        print(f"Find {N} accepted papers in {track} track.")

        for i in tqdm(range(N)):

            paper_title = li_papers[i].find("h4").find("a").string.strip()
            paper_part_url = li_papers[i].find("h4").find("a")["href"]
            paper_url = f"{openreview_url}{paper_part_url}"
            # print(openreview_url, paper_part_url, paper_url)

            paper_infos[paper_title]["url"] = paper_url
            paper_infos[paper_title]["track"] = track

            # go to the webpage for specific paper
            browser.get(paper_url)
            try:
                WebDriverWait(browser, 5).until(lambda _: len(_.find_elements_by_class_name("note_content_field")) >= 1)
            except:
                raise ValueError

            paper_keys = browser.find_elements_by_class_name("note_content_field")
            paper_vals = browser.find_elements_by_class_name("note_content_value")

            paper_infos[paper_title]["ratings"] = []
            for j in range(len(paper_keys)):
                paper_content_html = paper_keys[j].get_attribute("innerHTML")
                if paper_content_html.strip() == "Rating:":
                    paper_infos[paper_title]["ratings"].append(float(paper_vals[j].get_attribute("innerHTML").split(":")[0].strip()))

            if i % 20 == 0:
                pickle.dump(paper_infos, open(save_f, "wb"))

    pickle.dump(paper_infos, open(save_f, "wb"))
    browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--save_f",
        required=True,
        help="Path to file for saving results",
    )
    parser.add_argument(
        "--driver_f",
        required=True,
        help="Path to WebDriver file",
    )

    args = parser.parse_args()

    get_ratings(OPENREVIEW_URL, URL_DICT, args.driver_f, args.save_f)
