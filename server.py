import datetime
import os
import uuid
import time

import tzlocal as tzlocal
from apscheduler.schedulers.background import BackgroundScheduler

import mailer
from flask_cors import CORS
from http import HTTPStatus
from flask import Flask, request, jsonify, render_template, redirect

external_url = os.environ.get("external_url")
admin_password = os.environ.get("admin_password")
current_vote = {}
app = Flask(__name__, template_folder="templates")
CORS(app)


def generate_url():
    current_id = str(uuid.uuid4())
    current_vote["vote_ids"].append(current_id)
    return "<a href='{}'>Vote here!</a>".format(external_url + "/vote/" + current_id)


@app.route("/", methods=["GET"])
def default():
    return redirect("/start_vote")


@app.route("/start_vote", methods=["POST", "GET"])
def start_vote():
    if request.method == "POST":
        password = request.form.get("password")
        if not password or admin_password != password:
            return jsonify({"err": "No password/wrong password"}), HTTPStatus.FORBIDDEN
        mail_list = request.form.get("emails", "").split(",")
        if not mail_list:
            return jsonify({"err": "No mail list"}), HTTPStatus.BAD_REQUEST
        title = request.form.get("title")
        expiry_date = time.time()+60*int(request.form.get("duration", 10))
        if expiry_date <= time.time():
            return jsonify({"err": "Expiry date must be in the future"}), HTTPStatus.BAD_REQUEST
        question = request.form.get("question")
        answers = request.form.get("answers", "").split(",")
        if not question or not answers:
            return jsonify({"err": "Missing question or answers"}), HTTPStatus.BAD_REQUEST
        global current_vote
        current_vote = {
            "title": title,
            "create_date": time.time(),
            "expiry_date": expiry_date,
            "question": question,
            "answers": answers,
            "vote_ids": [],
            "votes": {},
            "mail_list": mail_list
        }
        mail_codes_dict = {mail: generate_url() for mail in mail_list}
        mailer.send_mail_list(mail_codes_dict)
        return "Bun, bravo", HTTPStatus.CREATED
    else:
        return render_template("start_vote.html")


@app.route("/vote/<vote_id>", methods=["GET", "POST"])
def vote(vote_id):
    if request.method == "GET":
        ts = current_vote["expiry_date"]
        local_timezone = tzlocal.get_localzone()
        date = datetime.datetime.fromtimestamp(ts, local_timezone).strftime("%Y-%m-%d %H:%M:%S")
        return render_template("vote.html",
                               question=current_vote["question"],
                               answers=current_vote["answers"],
                               title=current_vote["title"],
                               expire=date)
    else:
        answer = request.form.get("answer")
        print(answer)
        if answer in current_vote["answers"]:
            if vote_id in current_vote["vote_ids"]:
                current_vote["vote_ids"].remove(vote_id)
                current_vote["votes"][vote_id] = answer
                print(current_vote["votes"][vote_id] + "  " + answer)
                if not current_vote["vote_ids"]:
                    end_vote()
        return "Bv coae", HTTPStatus.CREATED


def end_vote():
    global current_vote
    last_vote = current_vote
    current_vote = {}
    total_votes = len(last_vote["vote_ids"]) + len(last_vote["votes"])
    discarded_votes = len(last_vote["vote_ids"])
    percent_voted = (total_votes - discarded_votes) / total_votes * 100
    votes = {answer: 0 for answer in last_vote["answers"]}
    for vote_id in last_vote["votes"]:
        vote_answer = last_vote["votes"][vote_id]
        votes[vote_answer] += 1
    mail_body = "Total votes: {}\n<br>Discarded votes: {}\n<br>Percent voted: {}%".format(
        total_votes, discarded_votes, percent_voted
    )
    for answer in votes:
        answer_votes = votes[answer]
        mail_body += "\n<br>Votes for {}: {}".format(answer, answer_votes)
    mail_list = last_vote["mail_list"] + [mailer.server_mail]
    mailer.send_mail_list({mail: mail_body for mail in mail_list})


def check_time():
    if "expiry_date" not in current_vote:
        return
    if time.time() >= current_vote["expiry_date"]:
        end_vote()


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_time, "interval", seconds=10)
    scheduler.start()
    app.run("0.0.0.0", 5000)
