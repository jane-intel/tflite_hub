import time
from collections import namedtuple

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ModelInfo = namedtuple('ModelInfo', ('name', 'link', 'description'))
DEFAULT_SLEEP = 2
BASE_URL = "https://tfhub.dev/"
HOME_PAGE_FOR_TF_LITE_MODELS = BASE_URL + "s?deployment-format=lite&subtype=module,placeholder"


def get_single_str_attr(soup, tag, class_name) -> (bool, str):
    result = soup.find_all(tag, {'class': class_name})
    if result is None or len(result) != 1:
        return False, ""
    return True, result[0].get_text().strip()


def collect_from_page(page: "Page", models: set, page_index: int):
    page_content = page.content()
    models_num = len(models)
    soup = BeautifulSoup(page_content, features="html.parser")
    model_cards = soup.find_all("a", {'class': 'model-card'})
    for model_card in model_cards:
        name_status, name = get_single_str_attr(model_card, 'div', 'name-container')
        desc_status, description = get_single_str_attr(model_card, 'div', 'description')
        link = model_card.attrs['href'].strip()

        if not name_status and not description and link == "/":
            continue
        new_record = ModelInfo(name=name, link=link, description=description)
        if new_record in models:
            pass  # print("Repeated:", name)
        else:
            models.add(new_record)
    print("Page", page_index, "done. New entries registered:", len(models) - models_num)


def button_is_disabled(page: "Page"):
    page_content = page.content()
    soup = BeautifulSoup(page_content, features="html.parser")
    button = soup.find_all("button", {'aria-label': 'Next page'})
    assert button is not None and len(button) == 1
    attrs = button[0].attrs
    return 'disabled' in attrs and attrs['disabled'] == 'true'


def collect_by_model(i: int, model: ModelInfo, page: "Page", individual_model_links: set):
    num_collected_prev = len(individual_model_links)

    page_content = page.content()
    soup = BeautifulSoup(page_content, features="html.parser")
    format_container = soup.find_all('div', {'class': 'model-formats'})
    assert format_container is not None and len(format_container) == 1, format_container
    tabs = format_container[0].find_all('div', {'role': 'tab'})
    assert tabs is not None and len(tabs) > 0, tabs
    for tab in tabs:
        text = tab.get_text()
        if 'lite' not in text.lower():  # filter out all the non TFLite options
            continue
        page.click('id=' + tab.attrs['id'])
        time.sleep(DEFAULT_SLEEP)  # ugly way to whit until script would change the page. expect_navigation doesn't work
        page_content = page.content()
        soup = BeautifulSoup(page_content, features="html.parser")
        download = soup.find_all('download-button')
        assert download is not None and len(download) == 1, download
        download = download[0]
        link = download.find('a')
        assert link is not None and hasattr(link, 'attrs') and 'href' in link.attrs, link
        link = link.attrs['href']
        new_record = ModelInfo(name=model.name, link=link, description=model.description + " " + text)
        individual_model_links.add(new_record)
    print("#", i, ":", len(individual_model_links) - num_collected_prev, "links collected for", model.name)


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    models, models_num, page_index = set(), 0, 1

    page_path = HOME_PAGE_FOR_TF_LITE_MODELS
    page.goto(page_path)

    collect_from_page(page, models, page_index)
    while not button_is_disabled(page):
        page_index += 1
        page.click('[aria-label="Next page"]')
        time.sleep(DEFAULT_SLEEP)  # ugly way to whit until script would change the page. expect_navigation doesn't work
        collect_from_page(page, models, page_index)
    print(len(models), " model cards")

    individual_model_links = set()
    for i, model in enumerate(models):
        page.goto(BASE_URL + model.link)
        time.sleep(DEFAULT_SLEEP)  # ugly way to whit until script would change the page. expect_navigation doesn't work
        collect_by_model(i, model, page, individual_model_links)
    browser.close()
    print(len(individual_model_links), "model links collected")

    file = open('log.dsv', mode='w+')
    for link in individual_model_links:
        file.write("$".join([link.name, link.link, link.description]) + "\n")
