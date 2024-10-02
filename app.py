from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, 
    TextMessage, 
    TextSendMessage,
    ImageSendMessage
)
import cohere
import os
from dotenv import load_dotenv

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

def generate_reply(prompt):
    instruction = "請用繁體中文或英文回答以下問題（不超過五十字）："
    full_prompt = f"{instruction}\n{prompt}"

    response = co.generate(
        model='command-r-plus-08-2024',
        prompt=full_prompt,
        max_tokens=50,
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
    print("收到的消息內容：", event.message.text)
    reply = generate_reply(event.message.text)
    print("生成的回覆：", reply)

    if reply.startswith('https://'):
        api.reply_message(
            event.reply_token,
            ImageSendMessage(original_content_url=reply,
                             preview_image_url=reply))
    else:
        api.reply_message(event.reply_token, 
                          TextSendMessage(text=reply))
