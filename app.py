from chalice import Chalice, Response
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Chalice(app_name='line-oa-bot')
line_bot = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET_ID'))

@app.route('/')
def index():
    return {'hello': 'world'}

@app.route('/callback', methods=['POST'])
def callback():
    request = app.current_request
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    print(f"signature : {signature}")
    # get request body as text
    body = request.raw_body.decode('utf-8')
    print(f"body : {body}")
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        return Response(body='Invalid signature. Please check your channel access token/channel secret.',
        status_code=400,headers={'Content-Type':'text/plain'})

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def reply_message(event):
    line_bot.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )
