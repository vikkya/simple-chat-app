from pymongo import MongoClient
from bson import ObjectId
from werkzeug.security import generate_password_hash
from user import User
from datetime import datetime
import os

client = MongoClient(os.environ.get('DATABASE_URL'))

chat_db = client.get_database(os.environ.get("DB_NAME"))

users_collection = chat_db.get_collection("users")
group_collection = chat_db.get_collection("groups")
group_members_collection = chat_db.get_collection("group_members")


def save_user(username, email, password):
    password_hash = generate_password_hash(password)
    users_collection.insert_one({"_id": username, "email": email, "password": password_hash})

def get_user(username):
    user_data = users_collection.find_one({"_id": username})
    if user_data is not None:
        return User(user_data['_id'], user_data['email'], user_data['password'])
    else:
        return None

def save_group(group_name, created_by):
    group_id = group_collection.insert_one({
        'group_name': group_name, 'created_by': created_by, 'created_at': datetime.now()}).inserted_id
    
    add_group_member(group_id, group_name, created_by, created_by, is_group_admin=True)
    return group_id

def update_group(group_id, group_name):
    group_collection.update_one({'_id': ObjectId(group_id)}, {"$set": {"group_name": group_name}})
    group_members_collection.update_many({'_id.group_id': ObjectId(group_id)}, {'$set': {'group_name': group_name}})

def get_group(group_id):
    return group_collection.find_one({'_id': ObjectId(group_id)})

def add_group_member(group_id, group_name, username, added_by, is_group_admin=False):
    group_members_collection.insert_one(
        {'_id': {'group_id': ObjectId(group_id), 'username': username}, 
        'group_name': group_name,'added_by': added_by, 'added_at': datetime.now(), 'is_group_admin': is_group_admin})

def add_group_members(group_id, group_name, usernames, added_by):
    group_members_collection.insert_many([
        {'_id': {'group_id': ObjectId(group_id), 'username': username}, 
        'group_name': group_name,'added_by': added_by, 'added_at': datetime.now(), 'is_group_admin': False} for username in usernames])

def remove_group_members(group_id, usernames):
    group_members_collection.delete_many({'_id': {'$in': [{'group_id:': ObjectId(group_id), 'username': username} for username in usernames]}})

def get_group_members(group_id):
    return list(group_members_collection.find({'_id.group_id': ObjectId(group_id)}))

def get_groups_for_user(username):
    return list(group_members_collection.find({'_id.username': username}))

def is_group_member(group_id, username):
    return group_members_collection.count_documents({'_id': {'group_id': ObjectId(group_id), 'username': username}})

def is_group_admin(group_id, username):
    return group_members_collection.count_documents({'_id': {'group_id': ObjectId(group_id), 'username': username}, 'is_group_admin':True})
