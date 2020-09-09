import os
import csv
import time
from random import randint
from urllib.request import urlretrieve
from selenium import webdriver
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options as CH_OPTIONS

BASE_URL = 'https://9gag.com/video/fresh'
OUTPUT_FILE = 'videos_data.csv'


## Save to CSV
def save_to_csv(filename, data):
    new_data = []
    with open(filename, 'a') as f:
        writer = csv.writer(f)
        try:
            writer.writerow(data)
        except:
            try:
                for x in data:
                    try:
                        x.encode('utf-8')
                    except:
                        try:
                            x.decode('utf-8')
                        except:
                            x = ''
                    new_data.append(x)
            except:
                pass

            new_data = [x.encode('ascii', 'replace') for x in new_data]
            writer.writerow(new_data)

    f.close()


def read_done_csv(file):
    done = []
    if (os.path.exists(file)):
        with open(file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                try:
                    if row[-1] not in done:
                        done.append(row[0])
                except IndexError:
                    continue
    return done


def make_soup(driver):
    soup = BeautifulSoup(driver.page_source, 'html5lib')
    return soup


def make_driver():
    options = CH_OPTIONS()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--mute-audio")
    # options.add_argument("--headless")
    options.add_argument('log-level=2')
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.delete_all_cookies()

    return driver


def download_video(url, category, filename):
    file_path = os.getcwd() + '/videos/{0}/{1}'.format(category, filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    urlretrieve(url, file_path)
    return file_path


def main():
    driver = make_driver()
    driver.get(BASE_URL)
    # Random wait until the page load completely
    delay = randint(7, 10)
    time.sleep(delay)

    last_count = 0
    while True:
        done_links = read_done_csv(OUTPUT_FILE)
        soup = make_soup(driver)
        videos_tag = soup.find('section', {'id': 'list-view-2'}).findAll('div', {'class': 'list-stream'})

        # Count based scroll condition
        new_count = len(videos_tag)
        if last_count == new_count:
            break

        last_count = new_count

        # extracting videos data
        for tag in videos_tag:
            try:
                # Video Detail extraction
                video_info = {}
                video_info['url'] = tag.find('source', {'type': 'video/mp4'})['src']
                # Ignore already scraped video
                if video_info['url'] in done_links:
                    continue

                video_info['title'] = tag.find('header').find('h1').get_text().strip()
                video_info['thumbnail'] = tag.find('video')['poster']
                video_info['points'] = tag.find('p', {'class': 'post-meta'}).find('a',
                                                                                  {'class': 'point'}).get_text().strip()
                video_info['comments'] = tag.find('p', {'class': 'post-meta'}).find('a',
                                                                                    {
                                                                                        'class': 'comment'}).get_text().strip()
                video_info['category'] = tag.find('div', {'class': 'post-section'}).find('a', {
                    'class': 'section'}).get_text().strip()
                video_info['filename'] = video_info['url'].split('/')[-1]
                print(video_info['url'])
                # Download Video
                video_info['filepath'] = download_video(video_info['url'], video_info['category'],
                                                        video_info['filename'])

                # Save Data to csv
                if not os.path.exists(OUTPUT_FILE):
                    save_to_csv(OUTPUT_FILE,
                                ['Video URL', 'Title', 'Video Path', 'Category', 'No. of Comments', 'Points',
                                 'Thumbnail'])

                save_to_csv(OUTPUT_FILE,
                            [video_info['url'], video_info['title'], video_info['filepath'], video_info['category'],
                             video_info['comments'], video_info['points'], video_info['thumbnail']])
            except:
                pass

        try:
            element = driver.find_element_by_xpath("//section[@id='list-view-2']").find_elements_by_xpath(
                "//div[@class='loading']")[-1]
            driver.execute_script("arguments[0].scrollIntoView();", element)
            # Random wait until the page load completely
            delay = randint(7, 10)
            time.sleep(delay)
        except:
            print("Unable to scroll")
            break

    driver.close()


main()
