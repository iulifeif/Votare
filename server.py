import os
import uuid
import time
import mailer
from flask_cors import CORS
from http import HTTPStatus
from flask import Flask, request, jsonify, render_template

external_url = os.environ.get("external_url")
admin_password = os.environ.get("admin_password")
current_vote = {}
app = Flask(__name__, template_folder="templates")
CORS(app)


def generate_url():
    current_id = str(uuid.uuid4())
    current_vote["vote_ids"].append(current_id)
    return external_url + "/vote/" + current_id


@app.route("/start_vote", methods=["POST"])
def start_vote():
    if not request.is_json:
        return jsonify({"err": "Not a json request."}), HTTPStatus.BAD_REQUEST
    password = request.json.get("password")
    if not password or admin_password != password:
        return jsonify({"err": "No password/wrong password"}), HTTPStatus.FORBIDDEN
    mail_list = request.json.get("emails")
    if not mail_list:
        return jsonify({"err": "No mail list"}), HTTPStatus.BAD_REQUEST
    title = request.json.get("title")
    expiry_date = request.json.get("expiry_date", time.time()+10*60)
    if expiry_date <= time.time():
        return jsonify({"err": "Expiry date must be in the future"}), HTTPStatus.BAD_REQUEST
    question = request.json.get("question")
    answers = request.json.get("answers")
    if not question or not answers or type(answers) is not list:
        return jsonify({"err": "Missing question or answers"}), HTTPStatus.BAD_REQUEST
    global current_vote
    current_vote = {
        "title": title,
        "create_date": time.time(),
        "expiry_date": expiry_date,
        "question": question,
        "answers": answers,
        "vote_ids": [],
        "votes": {}
    }
    mail_codes_dict = {mail: generate_url() for mail in mail_list}
    mailer.send_mail_list(mail_codes_dict)
    return jsonify({}), HTTPStatus.CREATED


@app.route("/vote/<vote_id>", methods=["GET", "POST"])
def vote(vote_id):
    if request.method == "GET":
        return render_template("vote.html",
                               question=current_vote["question"],
                               answers=current_vote["answers"],
                               title=current_vote["title"],
                               expire=current_vote["expiry_date"])
    else:
        answer = request.form.get("answer")
        if answer in current_vote["answers"]:
            if vote_id in current_vote["vote_ids"]:
                current_vote["vote_ids"].remove(vote_id)
                current_vote["votes"][vote_id] = answer
        return jsonify({}), HTTPStatus.CREATED


if __name__ == '__main__':
    app.run("0.0.0.0", 5000)
