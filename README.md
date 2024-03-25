# Andy Bot
Telegram bot for scraping information from social networks and other platforms.

## Supported social networks
- [x] TikTok
- [ ] Instagram
- [ ] VK
- [ ] Pinterest
- [ ] Spotify
- [ ] Yandex Music

## Demo
https://t.me/mybyandybot

## Installation
To install and run the bot, follow these steps:

1. Clone this repository:

    ```
    git clone https://github.com/papayyg/andy-bot.git
    ```
2. Navigate into the cloned directory:

    ```
    cd andy-bot
    ```

3. Create a virtual environment:

    ```
    python -m venv <virtual_environment_name>
    ```

4. Activate the virtual environment. Depending on your operating system, the command to activate the environment will differ:

    For Windows:

    ```
    <virtual_environment_name>\Scripts\activate
    ```

    For Unix or MacOS:

    ```
    source <virtual_environment_name>/bin/activate
    ```

5. Install the required dependencies:

    ```
    pip install -r requirements.txt
    ```

6. Create a `.env` file in the root directory and specify the following environment variables:

    ```
    BOT_TOKEN=<your_bot_token>
    MONGO_HOST=<your_mongo_uri>
    ```

7. Run the bot by executing the `bot.py` file:

    ```
    python bot.py
    ```


## Python Version:

AndyBot is developed using Python 3.9.13.

## Libraries Used:

- aiogram (3.4.1): A Python framework for Telegram bot development.
- MongoDB: A NoSQL database used for data storage.

## Multilingual Support

Bot supports multilingual capabilities. To add support for additional languages, follow these steps:

1. Navigate to the `locales` folder.

2. Open the `translations.json` file.

3. Add translations for the desired language following the existing format.

## License

[MIT](https://choosealicense.com/licenses/mit/)


