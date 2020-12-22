from fastapi import FastAPI, Request


app = FastAPI()

@app.post("/")
def on_event(request: Request):
    """
    Handles an event from Google Chat.
    """
    event = request.client_host
    if event['type'] == 'ADDED_TO_SPACE' and not event['space']['singleUserBotDm']:
        text = 'Thanks for adding me to "%s"!' % (event['space']['displayName'] if event['space']['displayName'] else 'this chat')
    elif event['type'] == 'MESSAGE':
        text = 'You said: `%s`' % event['message']['text']
    else:
       return

    return {'text': text}

