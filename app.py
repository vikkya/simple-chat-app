from flask import Flask, render_template,request, redirect, url_for
from flask_socketio import SocketIO, join_room
from flask_login import LoginManager, login_user, logout_user,login_required, current_user
import pymongo
from pymongo.errors import DuplicateKeyError
from db import get_user,save_user, save_group, add_group_members, get_groups_for_user, get_group, get_group_members, is_group_member, is_group_admin, update_group, remove_group_members, save_message, get_messages
from bson.json_util import dumps
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
socketio = SocketIO(app,cors_allowed_origins="*")
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@app.route("/")
def home():
    if current_user.is_authenticated:
        groups = get_groups_for_user(current_user.username)
    return render_template("index.html", groups=groups)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    message = ""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = get_user(username)

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("home"))
        else:
            message = "login failed"
    return render_template('login.html', message=message)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/create_group", methods=['GET', 'POST'])
@login_required
def create_group():
    message = ""
    if request.method == 'POST':
        group_name = request.form.get("group_name")
        usernames = [username.strip() for username in request.form.get("members").split(",")]
        
        if len(group_name) and len(usernames):
            group_id = save_group(group_name, current_user.username)
            if current_user.username in usernames:
                usernames.remove(current_user.username)
            add_group_members(group_id, group_name, usernames, current_user.username)
            return redirect(url_for("view_group", group_id=group_id))
        else:
            message = "Failed to create group"
    return render_template("create_group.html", message=message)


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    message = ""
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            save_user(username, email, password)
            redirect(url_for("login"))
        except DuplicateKeyError:
            message = "User already exists"
    return render_template('signup.html', message=message)

@app.route("/groups/<group_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    message = ""
    group = get_group(group_id)
    if group and is_group_admin(group_id, current_user.username):
        existing_members = [member['_id']['username'] for member in get_group_members(group_id)]
        group_members_str = ",".join(existing_members)
        if request.method == 'POST':
            group_name = request.form.get("group_name")
            group['group_name'] = group_name
            update_group(group_id, group_name)

            new_members = [username.strip() for username in request.form.get("members").split(",")]
            members_to_add = list(set(new_members) - set(existing_members))
            members_to_delete = list(set(existing_members) - set(new_members))
            if len(members_to_add):
                add_group_members(group_id, group_name, members_to_add, current_user.username)
            if len(members_to_delete):
                remove_group_members(group_id, members_to_delete)
            message = "Updated Successfully"
            group_members_str = ",".join(new_members)
        
        return render_template("edit_group.html", group=group, group_members_str=group_members_str, message=message)
    else:
        return "Group not found", 404

@app.route("/groups/<group_id>")
@login_required
def view_group(group_id):
    group = get_group(group_id)
    if group and is_group_member(group_id, current_user.username):
        group_members = get_group_members(group_id)
        messages = get_messages(group_id)
        return render_template("/view_group.html", username=current_user.username, group=group, group_members=group_members, messages=messages)
    else:
        return "Group not found", 404

@app.route("/groups/<group_id>/messages")
@login_required
def get_older_messages(group_id):
    group = get_group(group_id)
    if group and is_group_member(group_id, current_user.username):
        page = int(request.args.get('page', 0))
        messages = get_messages(group_id, page)
        return dumps(messages)
    else:
        return "Group not found", 404


@socketio.on("send_message")
def handle_send_message_event(data):
    app.logger.info(f"{data['username']} sent a message {data['message']} to group {data['group']}")

    save_message(data['group'], data['message'], data['username'])
    socketio.emit("receive_message", data, room=data['group'])

@socketio.on("join_group")
def handle_join_group_event(data):
    app.logger.info(f"{data['username']} has joined the group {data['group']}")
    join_room(data['group'])
    socketio.emit("join_group_announcement", data)

@login_manager.user_loader
def load_user(username):
    return get_user(username)



if __name__ == "__main__":
    socketio.run(app, debug=True)

# ztQLx8ApKOXPjdBx mongoDB password
# mongodb+srv://vikky:ztQLx8ApKOXPjdBx@cluster0.7s50k.mongodb.net/SIMPLECHATAPP?retryWrites=true&w=majority