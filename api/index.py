from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, 
    TextMessage, 
    TextSendMessage,
    ImageSendMessage,
    FollowEvent
)
import cohere
import os
from dotenv import load_dotenv
import vercel_wsgi

load_dotenv()

app = Flask(__name__)

# 初始化 LINE Bot API 和 Webhook Handler
line_bot_api = LineBotApi(os.getenv('LINE_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_SECRET'))

# 初始化 Cohere 客戶端
cohere_api_key = os.getenv('COHERE_API_KEY')
co = cohere.Client(cohere_api_key)

def generate_reply(prompt):
    instruction = "請用繁體中文或英文回答以下問題："
    full_prompt = f"{instruction}\n{prompt}"
    
    response = co.generate(
        model='command-r-03-2024',
        prompt=full_prompt,
        max_tokens=50,
        temperature=0.5,
        k=0,
        p=0.75,
        frequency_penalty=0,
        presence_penalty=0,
        stop_sequences=[],
        return_likelihoods='NONE'
    )
    return response.generations[0].text.strip()

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("收到的消息內容：", event.message.text)  # 調試打印
    reply = generate_reply(event.message.text)
    print("生成的回覆：", reply)  # 調試打印

    if reply.startswith('https://'):
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(original_content_url=reply,
                             preview_image_url=reply))
    else:
        line_bot_api.reply_message(event.reply_token, 
                                   TextSendMessage(text=reply))

@handler.add(FollowEvent)
def handle_follow(event):
    welcome_message = "歡迎加入！問我任何問題吧，我會用 AI 回覆你！"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=welcome_message))

@app.route("/", methods=["POST"])
def callback():
    # 取得 X-Line-Signature 表頭電子簽章內容
    signature = request.headers.get('X-Line-Signature')

    # 以文字形式取得請求內容
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 比對電子簽章並處理請求內容
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("電子簽章錯誤, 請檢查密鑰是否正確？")
        abort(400)

    return 'OK'

# 使用 vercel_wsgi 處理請求
def handler_func(request, context):
    return vercel_wsgi.handle_request(app, request, context)
