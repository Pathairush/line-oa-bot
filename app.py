from chalice import Chalice, Response
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import boto3
import datetime
import json
import pandas as pd
import numpy as np
import uuid
import awswrangler as wr

app = Chalice(app_name='line-oa-bot')
line_bot = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET_ID'))
s3 = boto3.client('s3', aws_access_key_id=os.getenv("aws_access_key_id"), aws_secret_access_key=os.getenv("aws_secret_access_key"))

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
    # save event
    save_event_to_s3(event, s3)
    # reply message
    line_bot.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )

def save_event_to_s3(event, s3):
    # convert event to dict
    data = json.loads(str(event))
    # input to pd dataframe
    df = pd.DataFrame(data, index=[0])
    # write dataframe to parquet
    uniq_nm = str(uuid.uuid4())
    filename = f'/tmp/{uniq_nm}.parquet'
    key = f"year={datetime.datetime.now().strftime('%Y')}/month={datetime.datetime.now().strftime('%m')}/day={datetime.datetime.now().strftime('%d')}/{uniq_nm}.parquet"
    wr.s3.to_parquet(
        df = df, 
        path = 's3://' + os.getenv("S3_BUCKET_NAME") + '/' + key,
        index=False,
        compression='snappy',
        boto3_session = boto3.session.Session(
            aws_access_key_id=os.getenv("aws_access_key_id"),
            aws_secret_access_key=os.getenv("aws_secret_access_key"),
            region_name ='ap-southeast-1'
        )
    )
