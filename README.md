# stockM

Use telegram to get stock updates regarding your portfolio of stocks.

## Usage

1. Download the [Telegram][1] application.
2. Search for the bot called **Stock Updates Slave** (*@stock_updates_bot*).
3. Find the list of helper commands using the `/` button.

### Basic Commands

1. Update portfolio/watchlist of stocks
    To update portfolio or watchlist, select the *Update stock portfolio*
    or *Update watchlist* option from the markup keyboard. Enter the stock(s)
    that you wish to monitor using their tickers, separated by a space.
    Example:
    ```
    AMZN BABA TSLA CRM ZM SE
    ```

2. Get portfolio/watchlist updates
    Using the *Portfolio updates* or *Watchlist updates* options from the
    same markup keyboard, these commands sends push notifications of daily
    price changes to the list of stocks you've indicated.

3. Get price change for a single stock
    ```
    /get_px_change <ticker>
    ```

4. Get price change for multiple stocks
    ```
    /get_px_change <ticker1> <ticker2> <ticker3>
    ```

5. Toggle daily notifications using the `Subscribe/Unsubscribe to daily 
update` option from the markup keyboard. This toggles your daily push 
notifications on/off.

## Deployment using Heroku
### Via Procfile
This service is deployed on heroku using the `Procfile` listed in this
repository. To launch a service of your own, follow these steps:

1. Get an account with Heroku and install the heroku-cli
2. Create a new project

    ```bash
    heroku create <project_name>
    ```
3. To deploy this telegram bot, we need to set the telegram bot token as
an environment variable.

    ```bash
    heroku config:set TOKEN=<your_token_number>
    ```

4. Push the repo to the Heroku remote. Note that heroku will only build
if you push the main or master branch. No action will be taken if other
branches are pushed.

    ```bash
    git push heroku main
    ```

### Via Dockerfile
Referenced from this [link][2]

```bash
heroku container:login
heroku create APP_NAME
heroku container:push web --app APP_NAME
heroku container:release web --app APP_NAME
heroku open

# or can go to the website to manually scale it up
heroku ps:scale web=1
```

## Serverless deployment using AWS Lambda

0. Install serverless (this assumes you have NPM)
    ```bash
    npm install -g serverless

    # Check that you have serverless installed
    serverless --version
    ```

1. Create a folder to be used for serverless deployment (note: `sls` is
shorthand for `serverless`)
    ```bash
    sls create --template aws-python3 --path <path_to_create>
    ```

2. To use serverless-python-requirements, we have to first install the plugin.
Note that since we are using `dockerizedPip` in our custom requirements, we
also need to have Docker installed.
    ```bash
    npm install --save serverless-python-requirements
    ```

3. Copy over `requirements.txt` and the `stockM` folder to this path we have
created in step 1 `<path_to_create>`.

4. Export `DATABASE_URL`, `TOKEN` (telegram bot token) and AWS credentials.
    ```bash
    export DASEBASE_URL=
    export TOKEN=
    export AWS_ACCESS_KEY_ID=
    export AWS_SECRET_ACCESS_KEY=
    ```

5. Deploy to serverless.
    ```bash
    sls deploy
    ```

6. (Optional) Test that serverless deployment is working.
    ```bash
    sls invoke -f <function>
    ```


## References
1. [Python telegram bot - Persistent Conversation Bot][3]

[1]: https://telegram.org/
[2]: https://medium.com/@ksashok/containerise-your-python-flask-using-docker-and-deploy-it-onto-heroku-a0b48d025e43
[3]: https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/persistentconversationbot.py