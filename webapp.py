from flask import Flask, redirect, url_for, session, request, jsonify, Markup
from flask_oauthlib.client import OAuth
from flask import render_template

import pprint
import os
import json

os.system("echo '[]'>" + 'posts.json')

app = Flask(__name__)

app.debug = True #Change this to False for production

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)

#Set up GitHub as OAuth provider
github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'], #your web app's "username" for github's OAuth
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],#your web app's "password" for github's OAuth
    request_token_params={'scope': 'user:email'}, #request read-only access to the user's email.  For a list of possible scopes, see developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',  
    authorize_url='https://github.com/login/oauth/authorize' #URL for github's OAuth login
)

#use a JSON file to store the past posts.  A global list variable doesn't work when handling multiple requests coming in and being handled on different threads
#Create and set a global variable for the name of you JSON file here.  The file will be created on Heroku, so you don't need to make it in GitHub




@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/')
def home():
    return render_template('home.html', past_posts=posts_to_html())
    
    
@app.route('/posted', methods=['POST'])
def post():
    username = session['user_data']['login']
    message = request.form['message']
    if 'cat' in message:
        return redirect("https://www.petsworld.in/blog/10-reasons-why-dogs-are-better-than-cats.html", code=302)
    else:
        try:
            with open('posts.json', 'r+') as forumPosts:
                data = json.load(forumPosts)
                data.append({"username":username, "message":message})
                forumPosts.seek(0)
                forumPosts.truncate()
                json.dump(data, forumPosts)
        except Exception as e:
            print("error")
            print(e)   
        return render_template('home.html', past_posts = posts_to_html())
    #This function should add the new post to the JSON file of posts and then render home.html and display the posts.  
    #Every post should include the username of the poster and text of the post. 
    

#redirect to GitHub's OAuth page and confirm callback URL
@app.route('/login')
def login():   
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='https')) #callback URL must match the pre-configured callback URL

@app.route('/logout')
def logout():
    session.clear()
    return render_template('message.html', message='You were logged out')

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)      
    else:
        try:
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('user').data
            message='You were successfully logged in as ' + session['user_data']['login']
        except Exception as inst:
            session.clear()
            print(inst)
            message='Unable to login, please try again.  '
    return render_template('message.html', message=message)
    
@app.route('/pollPage')
def renderPollpage():
    return render_template('pollPage.html')

#the tokengetter is automatically called to check who is logged in.
@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')

def posts_to_html():
    try:
        with open('posts.json', 'r') as forumPosts:
            post_table = Markup("<table class='table table-bordered'><tr><th>User</th><th>Post</th></tr>")
            posts = json.load(forumPosts)
            for p in posts:
                post_table += Markup("<tr><td>" + p['username'] + "</td><td>" + p["message"] + "</td></tr>")
            post_table += Markup("</table>")
    except Exception as e:
        post_table = ''
        print(e)
    return post_table


if __name__ == '__main__':
    app.run()
