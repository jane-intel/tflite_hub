import time
import copy
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# ModelInfo = namedtuple('ModelInfo', ('name', 'link', 'description', "publisher", "downloads"))
DEFAULT_SLEEP = 2
BASE_URL = "https://tfhub.dev/"
HOME_PAGE_FOR_TF_LITE_MODELS = BASE_URL + "s?deployment-format=lite&subtype=module,placeholder"


class ModelInfo:
    name = ""
    link = ""
    description = ""
    publisher = ""
    downloads = ""
    problem_domain = ""
    dataset = ""
    architecture = ""

    attributes = ["name", "link", "description", "publisher", "downloads", "problem_domain", "dataset", "architecture"]

    def __init__(self, model_card: BeautifulSoup):
        name_status, self.name = get_single_str_attr(model_card, 'div', 'name-container')
        self.link = model_card.attrs['href'].strip()
        self.description = get_single_str_attr(model_card, 'div', 'description')[1]

        if not name_status and not self.description and self.link == "/":
            raise Exception("This is not a model card")

        self.publisher = get_single_str_attr(model_card, 'div', 'publisher')[1].replace("Publisher:", "").strip().strip(".")
        self.downloads = get_single_str_attr(model_card, 'div', 'usage')[1]
        self.problem_domain = get_single_str_attr(model_card, 'a', 'problem-domain-link')[1]
        info_status, misc_info = get_all_str_attrs(model_card, "p", "bumper-link")
        for info in misc_info:
            if "Architecture: " in info:
                self.architecture = info.replace("Architecture:", "").strip()
            elif "Dataset: " in info:
                self.dataset = info.replace("Dataset:", "").strip()
            else:
                assert "Unknown field appeared", info

    def set_link(self, value):
        self.link = value

    def set_description(self, value):
        self.description = value

    def __repr__(self):
        return ",".join([str(getattr(self, field)).replace("\n", " ").replace(",", ";") for field in self.attributes])


def get_single_str_attr(soup, tag, class_name) -> (bool, str):
    result = soup.find_all(tag, {'class': class_name})
    if result is None or len(result) != 1:
        return False, ""
    return True, result[0].get_text().strip()


def get_all_str_attrs(soup, tag, class_name) -> (bool, list):
    result = soup.find_all(tag, {'class': class_name})
    if result is None:
        return False, ""
    return True, [r.get_text().strip() for r in result]


def collect_from_page(page: "Page", models: set, page_index: int):
    page_content = page.content()
    models_num = len(models)
    soup = BeautifulSoup(page_content, features="html.parser")
    model_cards = soup.find_all("a", {'class': 'model-card'})
    for model_card in model_cards:
        try:
            new_record = ModelInfo(model_card)
        except Exception as e:
            assert "This is not a model card" in str(e), str(e)
            continue
        if new_record.name in [m.name for m in models] and new_record.link in [m.link for m in models]:
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
        new_record = copy.copy(model)
        new_record.set_link(link)
        new_record.set_description(model.description + " " + text)
        individual_model_links.add(new_record)
    print("#", i, ":", len(individual_model_links) - num_collected_prev, "links collected for", model.name)


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    models, models_num, page_index = set(), 0, 1

    page_path = HOME_PAGE_FOR_TF_LITE_MODELS
    page.goto(page_path)
    time.sleep(DEFAULT_SLEEP)  # ugly way to whit until script would change the page. expect_navigation doesn't work

    collect_from_page(page, models, page_index)
    while not button_is_disabled(page):
        page_index += 1
        page.click('[aria-label="Next page"]')
        time.sleep(DEFAULT_SLEEP)  # ugly way to whit until script would change the page. expect_navigation doesn't work
        collect_from_page(page, models, page_index)
    print(len(models), "model cards")

    individual_model_links = set()
    for i, model in enumerate(models):
        page.goto(BASE_URL + model.link, wait_until='load')
        time.sleep(DEFAULT_SLEEP)  # ugly way to whit until script would change the page. expect_navigation doesn't work
        page.wait_for_selector("div[class=model-formats]")
        collect_by_model(i, model, page, individual_model_links)
    browser.close()
    print(len(individual_model_links), "model links collected")

    file = open('log.dsv', mode='w+')
    [file.write(str(model) + "\n") for model in individual_model_links]
