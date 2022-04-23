# Games information retriving - SI 507 W22 Final Project
Final project for Umich SI 507 course, retrive games related information from steam 


## Requirements
The project is created with Python 3.8.3 with following required Python packages:
* requests
* flask
* beautifulsoup4
* sqlite3

## How to run the code
Type python3 main.py or run the code main.py directly. Then visit the link http://127.0.0.1:5000/ to interact with the program.

## data processing and data structure
index.html is main page for user interaction, it accepts search word requests(game related word, number of games you want to display,results showing order) or category search requests(game category, number of games you want to display, Preferences of Display).
Flask functions will receive the inputs and crawl or use cache to get specific information of searched games. Storing the data in sqlite3 temporarily for each search.

data structure mainly represented by html files.
detail.html and extension_info.html in templates folder will use the data stored in sqlite3 database.
detail.html will show each game's (Title & url), overall rate, tags, image url, description of the game, price, release date, url to more information. 
extension_info.html gives each game's information of its developer,supported languages, system minimum requirements and system recommended requirements.
game_status.html will show top 10 games sorted by current player count. It will display each game's (title&url), img, current players, peak Today. This information is crwaled with out using cache.

cache.json is used in constructing detail.html and extension_info.html. read_json.py demonstrates the basic step to use the json file.

