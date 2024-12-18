import os

from dotenv import load_dotenv
from flask import Flask, Response, abort, request
import cohere
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    ImageSendMessage,
    MessageEvent,
    TextMessage,
    TextSendMessage
)

load_dotenv()

cohere_api_key = os.getenv('COHERE_API_KEY')
co = cohere.Client(cohere_api_key)

api = LineBotApi(os.getenv('LINE_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_SECRET'))

app = Flask(__name__)

@app.route("/", methods=["POST"])  # 設定為 POST 請求
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("電子簽章錯誤, 請檢查密鑰是否正確？")
        abort(400)

    return 'OK'

@app.route("/", methods=["HEAD", "GET","OPTIONS"])  
def index() -> Response:
    return Response("OK", 200)

def generate_reply(prompt):
    """
    Generate a reply based on the given prompt using the Cohere API.

    Args:
        prompt (str): The input prompt to generate a reply for.

    Returns:
        str: The generated reply text.
    """
    instruction = "請用繁體中文或英文回答以下問題（請將回答限縮在五十字內）："
    full_prompt = f"{instruction}\n{prompt}"

    response = co.generate(
        model='command-r-plus-08-2024',
        prompt=full_prompt,
        max_tokens=100,
        temperature=0.7,
        # k=0,
        p=0.9,
        frequency_penalty=0,
        presence_penalty=0,
        stop_sequences=[],
        return_likelihoods='NONE'
    )
    return response.generations[0].text.strip()

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """
    Handle incoming text messages from LINE.

    Args:
        event (MessageEvent): The event object containing the message data.
    """
    print("收到的消息內容：", event.message.text)
    reply = generate_reply(event.message.text)
    print("生成的回覆：", reply)

    # Check if the reply is a URL
    if reply.startswith('https://'):
        api.reply_message(
            # original_content_url: URL of the original image
            # preview_image_url: URL of the preview image
            ImageSendMessage(original_content_url=reply,
                             preview_image_url=reply))
    else:
        api.reply_message(event.reply_token, 
                          TextSendMessage(text=reply))
