import json
import requests
from bs4 import BeautifulSoup
import time
import sqlite3
from flask import Flask, render_template, request

CACHE_DICT = {}
CACHE_NAME = "cache.json"
Tags_limit = 4
system_requirments_num = 6


def open_cache():
    try:
        cache_file = open(CACHE_NAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_NAME, "w")
    fw.write(dumped_json_cache)
    fw.close()

# make cache request


def fetch_cache(url, cache):

    if (url in cache.keys()):  # the url is our unique key
        print("---cache---")
        return cache[url], True
    else:
        print("---Fetching---")
        time.sleep(0.5)
        response = requests.get(url)
        return response.text, False

# get result with given category with different selection(NewTrend, Topseller...)
# base url=https://store.steampowered.com/category/
# This function will get conrresponds id, title, final price for the games


def get_catagory_results(baseurl, catagory_term, id_info, max_num_detailes=10):

    catagory_url = baseurl + catagory_term
    response = requests.get(catagory_url)
    # fetch the data with given catagory url
    soup = BeautifulSoup(response.text, 'html.parser')
    catagory_results = soup.find(id=id_info)

    catagory_lists = catagory_results.find_all('a')
    results = []
    num_games = 0
    for game_info in catagory_lists:
        game_dict = {}

        if 'data-ds-appid' not in game_info.attrs.keys():
            continue
        else:
            game_dict['game_id'] = game_info.attrs['data-ds-appid']

        title = game_info.find('div', class_='tab_item_name')
        game_dict['title'] = title.text if title is not None else 'None'

        price = game_info.find('div', class_="discount_final_price")
        game_dict['price'] = price.text if price is not None else 'None'

        results.append(game_dict)
        num_games += 1
        if num_games >= max_num_detailes:
            break
    return results


# get result based on search term
# baseurl="https://store.steampowered.com/search/?term="


def get_search_results(baseurl, search_term, max_num_detailes=10):

    search_url = baseurl + search_term
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    search_results = soup.find(id='search_resultsRows')
    if search_results is None:
        return None, None, None
    # fetch data without cache
    else:
        search_lists = search_results.find_all('a')
        results = []
        num_games = 0
        for game_info in search_lists:
            game_dict = {}

            if 'data-ds-appid' not in game_info.attrs.keys():
                continue
            else:
                game_dict['game_id'] = game_info.attrs['data-ds-appid']

            title = game_info.find('span', class_='title')
            game_dict['title'] = title.text if title is not None else 'None'

            #price = game_info.find('div',class_="search_price")
            price = game_info.find(
                'div', class_="col search_price_discount_combined responsive_secondrow").attrs['data-price-final']
            if price is None:
                game_dict['price'] = "None"
            else:
                game_dict['price'] = "$"+str((int(price)/100))

            results.append(game_dict)
            num_games += 1
            if num_games >= max_num_detailes:
                break
        return results

# get details of games with specific game id


def get_detail_results(game_dicts):
    results = []
    url = 'https://store.steampowered.com/app/'
    for game_info in game_dicts:
        detail_dict = {}
        detail_dict['title'] = game_info['title']
        detail_dict['url'] = url + game_info['game_id']
        detail_dict['id'] = game_info['game_id']
        response_text, status = fetch_cache(
            detail_dict['url'], CACHE_DICT)
        if status:
            detail_dict = response_text
        else:
            soup = BeautifulSoup(response_text, 'html.parser')
            # find description
            description = soup.find('div', class_='game_description_snippet')
            if description is None:
                detail_dict['description'] = 'None'
            else:
                detail_dict['description'] = description.text.strip()
            # find overall rate
            rate = soup.findAll('div', class_="user_reviews_summary_row")
            if rate == None:
                detail_dict['rate'] = 0
            else:
                if 'data-tooltip-html' in rate[1].attrs.keys():
                    rate = str(rate[1].attrs['data-tooltip-html'][0:2])
                    if rate.isnumeric():
                        detail_dict['rate'] = rate
                    else:
                        detail_dict['rate'] = '0'
                else:
                    detail_dict['rate'] = 0
            # find release date
            block = soup.find('div', class_='block')
            date = block.find('div', class_="release_date")
            if date == None:
                detail_dict['release_date'] = 'None'
            else:
                detail_dict['release_date'] = date.find(
                    'div', class_='date').text.strip()

            price = game_info['price']
            detail_dict['price'] = price

            image_url = block.find(
                'img', class_='game_header_image_full')['src']
            detail_dict['image_url'] = image_url

            developer = block.find('div', id="developers_list")
            if developer == None:
                detail_dict['developer'] = "None"
            else:
                developer = developer.find('a').text.strip()
                detail_dict['developer'] = developer
            # retrive tags with specific limits
            tags = block.find_all('a', class_='app_tag')
            num_tags = 0
            tags_list = []
            if tags == None:
                detail_dict['tags'] = 'None'
            else:
                for tag in tags:
                    tags_list.append(tag.text.strip())
                    num_tags += 1
                    if num_tags >= Tags_limit:
                        break
                detail_dict['tags'] = tags_list

            # language option
            language = soup.find('table', class_="game_language_options")
            if language == None:
                detail_dict['language_options'] = 'None'
            else:
                language_options = language.find_all('td', class_="ellipsis")
                language_list = []
                for l in language_options:
                    language_list.append(l.text.strip())
                detail_dict['language_options'] = language_list

            # fetch min System requirements
            min_requirement_block = soup.find(
                "div", class_="game_area_sys_req_leftCol")
            if min_requirement_block == None:
                detail_dict["min_systemRequirements"] = 'None'
            else:
                requirements_ul = min_requirement_block.find(
                    "ul", class_="bb_ul")
                if requirements_ul == None:
                    detail_dict["min_systemRequirements"] = 'None'
                else:
                    re_li = requirements_ul.findAll('li')
                    num_minli = 0
                    min_requirement_list = []
                    for li in re_li:
                        min_requirement_list.append(li.text)
                        num_minli += 1
                        if num_minli >= system_requirments_num:
                            break
                    detail_dict["min_systemRequirements"] = min_requirement_list

            # fetch recommended sys requirements
            min_requirement_block = soup.find(
                "div", class_="game_area_sys_req_rightCol")
            if min_requirement_block == None:
                detail_dict["Recommend_systemRequirements"] = 'None'
            else:
                requirements_ul = min_requirement_block.find(
                    "ul", class_="bb_ul")
                if requirements_ul == None:
                    detail_dict["Recommend_systemRequirements"] = 'None'
                else:
                    re_li = requirements_ul.findAll('li')
                    num_minli = 0

                    requirement_list = []
                    for li in re_li:
                        requirement_list.append(li.text)
                        num_minli += 1
                        if num_minli >= system_requirments_num:
                            break
                    detail_dict["Recommend_systemRequirements"] = requirement_list
                    if "min_systemRequirements" not in detail_dict.keys():
                        detail_dict["min_systemRequirements"] = []
                    if "Recommend_systemRequirements" not in detail_dict.keys():
                        detail_dict["Recommend_systemRequirements"] = []
            CACHE_DICT[detail_dict['url']] = detail_dict
        save_cache(CACHE_DICT)
        results.append(detail_dict)

    return results


# create database
DB_NAME = 'Games.sqlite'


def create_db():

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    drop_games_sql = 'DROP TABLE IF EXISTS "Games"'
    drop_details_sql = 'DROP TABLE IF EXISTS "Details"'
    '''Table Games is used to store info in search and category
       Table Details stores details of games 
    '''
    create_games_sql = '''
        CREATE TABLE IF NOT EXISTS "Games" (
            "Id" INTEGER PRIMARY KEY, 
            "TITLE" TEXT NOT NULL,
            "PRICE" TEXT NOT NULL, 
            FOREIGN KEY (TITLE) REFERENCES  Detailes (TITLE) 
        )
    '''

    create_details_sql = '''
        CREATE TABLE IF NOT EXISTS "Details" (
            "TITLE" TEXT PRIMARY KEY, 
            "RATE" TEXT NOT NULL,
            "TAGS" TEXT NOT NULL,
            "URL" TEXT NOT NULL, 
            "IMAGE_URL" TEXT NOT NULL,
            "DESCRIPTION" TEXT NOT NULL,
            "PRICE" TEXT NOT NULL,
            "RELEASE_DATE" TEXT NOT NULL,
            "DEVELOPER" TEXT NOT NULL,
            "LANGUAGES" TEXT NOT NULL,
            "Min_Requirement" TEXT NOT NULL,
            "Recommend_Requirement" TEXT NOT NULL,
            "Id" INTEGER NOT NULL
        )
    '''
    cur.execute(drop_details_sql)
    cur.execute(drop_games_sql)
    cur.execute(create_games_sql)
    cur.execute(create_details_sql)
    conn.commit()
    conn.close()

# Insert fetched data to database


def load_games(game_dict):

    insert_games_sql = '''
        INSERT INTO Games
        VALUES (?,?,?)
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for game in game_dict:
        cur.execute(insert_games_sql, [
            game['game_id'],
            game['title'],
            game['price']
        ])
    conn.commit()
    conn.close()


def load_details(detail_dict):

    insert_details_sql = '''
        INSERT INTO Details
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for detail in detail_dict:
        cur.execute(insert_details_sql, [
            detail['title'],
            detail['rate'],
            ', '.join(detail['tags']),
            detail['url'],
            detail['image_url'],
            detail['description'],
            detail['price'],
            detail['release_date'],
            detail['developer'],
            ', '.join(detail['language_options']),
            ', '.join(detail["min_systemRequirements"]),
            ', '.join(detail["Recommend_systemRequirements"]),
            detail['id']
        ])
    conn.commit()
    conn.close()


def get_db_results(Switch='1'):

    if Switch == '1':
        query = '''
        SELECT * FROM Details
        '''
    elif Switch == '2':
        query = '''
        SELECT * FROM Details
        WHERE RATE <> 'None'
        ORDER BY RATE DESC 
        '''

    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    result = cursor.execute(query).fetchall()
    connection.close()

    return result


def get_game_status(max_number=10):
    game_status = []
    number = 0
    response = requests.get("https://store.steampowered.com/stats/")
    soup = BeautifulSoup(response.text, 'html.parser')
    trs = soup.findAll('tr', class_='player_count_row')
    for tr in trs:
        game = []
        # current_players
        current_players = tr.findAll(
            'span', class_='currentServers')[0].text
        game.append(current_players)
        # peak_today

        peak_today = tr.findAll(
            'span', class_='currentServers')[1].text
        game.append(peak_today)
        # url
        url = tr.find("a").attrs['href']
        game.append(url)
        response_in = requests.get(url)
        soup_in = BeautifulSoup(response_in.text, 'html.parser')
        # name
        name = soup_in.find('div', id="appHubAppName").text
        game.append(name)
        block = soup_in.find('div', class_='block')
        image_url = block.find(
            'img', class_='game_header_image_full')['src']
        # img_url
        game.append(image_url)
        game_status.append(game)
        number += 1
        if number >= max_number:
            break
    return game_status


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')  # main page design


@app.route('/search_word', methods=['POST'])
def handle_search():
    term = request.form["name"]
    number = int(request.form["number"])
    url_search = "https://store.steampowered.com/search/?term="
    games_dict = get_search_results(url_search, term, number)
    if games_dict is None:
        return render_template('exception.html')
    else:
        details_dict = get_detail_results(games_dict)
        create_db()
        load_games(games_dict)
        load_details(details_dict)
        switch = request.form["order"]
        results = get_db_results(switch)
        return render_template('detail.html', results=results)


@app.route('/catagory', methods=['POST'])
def handle_catagory():

    catagory = request.form["catagory"]
    id_info = request.form["id_info"]
    number = int(request.form["number"])
    url_cata = "https://store.steampowered.com/category/"
    games_dict = get_catagory_results(url_cata, catagory, id_info, number)
    if games_dict is None:
        return render_template('exception.html')
    else:
        details_dict = get_detail_results(games_dict)
        create_db()
        load_games(games_dict)
        load_details(details_dict)
        results = get_db_results()
        return render_template('detail.html', results=results)


@app.route('/game/<id>', methods=['GET'])
def more_info(id):
    query = '''
    SELECT * FROM Details WHERE ID=?
    '''
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    result = cursor.execute(query, [id]).fetchall()
    result = result[0]
    min_req = result[10].split(',')
    rec_req = result[11].split(',')
    connection.close()
    return render_template('extension_info.html', game=result, min_req=min_req, rec_req=rec_req)


@app.route('/game_status', methods=['GET'])
def handle_game_status():
    game_status = get_game_status()

    return render_template('game_status.html', game_status=game_status)


if __name__ == "__main__":
    CACHE_DICT = open_cache()
    app.run(debug=True)
