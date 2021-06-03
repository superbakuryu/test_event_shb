#! coding: utf-8
import pymongo
from flask import (
    Flask,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from bson.objectid import ObjectId
import sentry_sdk
from waitress import serve
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from sentry_sdk.integrations.flask import FlaskIntegration
from datetime import timedelta
import requests
import json
# from meinheld import server
from flask_sse import sse


def getNOW():
    return datetime.now().timestamp()


myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["api_platform"]

app = Flask(__name__)
app.secret_key = 'somesecretkeythatonlyishouldknow'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=120)

# sentry_sdk.init(
#     dsn="https://cb15bf47dbf84812a698a1d23ef0a527:16d5b523c6db4071ba2d61927438850c@3.0.212.27:9002/12",

#     integrations=[FlaskIntegration()]
# )
app.config["REDIS_URL"] = "redis://127.0.0.1:6379/6"
app.register_blueprint(sse, url_prefix='/stream')


@app.route('/send', methods=['GET', 'POST'])
def send_message():
    data = request.get_json()
    bot_conversation_id = data.get('bot_conversation_id')

    insert_data = {"user_id": "",
                   "username": "Test Webhook",
                   "timestamp": getNOW(),
                   "link_api": "https://developer.nextiva.vn/send",
                   "request": bot_conversation_id,
                   "response": data,
                   "origin_request": "",
                   "origin_response": ""
                   }
    mydb.api_logs.insert_one(insert_data)
    sse.publish(data, type=bot_conversation_id)
    return "Message sent!"


@app.template_filter('shorten_id')
def shorten_id(value):
    return abs(hash(value)) % (10 ** 8)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


def get_bearer_token():
    url = "https://api.nextiva.vn/auth"

    payload = {'api_key': '2752aad4-d53a-4f3a-8506-000b911a2846'}
    files = [

    ]
    headers = {}

    response = requests.request(
        "POST", url, headers=headers, data=payload, files=files)
    return response.json().get('access_token')


@app.route('/', methods=['GET', 'POST'])
def test_event_shb():
    if request.method == 'POST':
        error = None
        customer_phone = request.form.get('customer_phone')
        if len(customer_phone) != 10:
            error = "Số điện thoại không hợp lệ"
            return json.dumps({"result": False, "error": error})

        customer_name = request.form.get('customer_name')
        if len(customer_name) == 0:
            error = "Tên không được để trống"
            return json.dumps({"result": False, "error": error})

        customer_cmnd = request.form.get('customer_cmnd')
        if len(customer_cmnd) == 0:
            error = "Số CMND không được để trống"
            return json.dumps({"result": False, "error": error})
        customer_gender = request.form.get('customer_gender')
        account_number = request.form.get('account_number')
        if len(account_number) == 0:
            error = "Số tài khoản không được để trống"
            return json.dumps({"result": False, "error": error})
        sum_of_money = request.form.get('sum_of_money')
        if len(sum_of_money) == 0:
            error = "Số tiền không được để trống"
            return json.dumps({"result": False, "error": error})

        token = get_bearer_token()

        url = "https://api.nextiva.vn/call/bot"

        call_params = '{"customer_phone": "' + customer_phone + '","customer_name": "' + customer_name + '","customer_cmnd": "' + customer_cmnd + '","customer_gender": "' + customer_gender + \
                      '","account_number": "' + account_number + '","sum_of_money": "' + sum_of_money + \
                      '","bank_name": "Ngân hàng SHB","bank_phone": "1800588856"}'

        payload = {'hotline': '0366568956',
                   'called': customer_phone,
                   'bot_id': '103',
                   'bot_region': 'NORTH',
                   'call_params': call_params,
                   'cus_id': '0'}
        files = [

        ]
        headers = {
            'Authorization': f'Bearer {token}'
        }

        response = requests.request(
            "POST", url, headers=headers, data=payload, files=files)

        r_json = response.json()
        code = r_json.get('code')
        data = r_json.get('data')
        conversation_id = data.get('conversation_id')
        return json.dumps({'result': True, "conversation_id": conversation_id, "code": code})

    else:
        error = None
        return render_template('test_event_shb.html', error=error)


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_name', None)
    return redirect('/login')

