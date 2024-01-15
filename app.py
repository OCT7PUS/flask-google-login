from flask import Flask, render_template, url_for, session, redirect, request
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os
import telegram
import asyncio

db = SQLAlchemy()
load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY')
DB_URI = os.environ.get('DB_URI')
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username


app = Flask(__name__)

app.secret_key = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
db.init_app(app)
oauth = OAuth(app)

oauth.register('google',
               client_id=GOOGLE_CLIENT_ID,
               client_secret=GOOGLE_CLIENT_SECRET,
               access_token_url='https://accounts.google.com/o/oauth2/token',
               access_token_params=None,
               authorize_url='https://accounts.google.com/o/oauth2/auth',
               authorize_params=None,
               api_base_url='https://www.googleapis.com/oauth2/v1/',
               userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
               jwks_uri='https://www.googleapis.com/oauth2/v2/certs',
               # This is only needed if using openId to fetch user info
               #   server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
               #   decode_claims=False,
               client_kwargs={'scope': 'openid email profile'},
               )



@app.route('/')
def index():
    if 'token' in session and 'email' in session:
        print('user.email')
        print(session['email'])

        print('user.token')
        print(session['token'])

        return render_template('chat.html', user=session['email'])
    else:
        return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    redirect_uri = url_for('auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route('/auth')
def auth():
    token = oauth.google.authorize_access_token()
    user = oauth.google.get('userinfo').json()

    print('=========================================TOKEN=======================================')
    print(token['access_token'])

    print('==========================================USER=======================================')
    print(user['email'])

    session['token'] = token['access_token']
    session['email'] = user['email']


    if 'token' in session and 'email' in session:
        user = session['email']
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

#    # print('Token', token)
#     print('User', user.email)

#     # Use the user info for login or registration
#     return render_template('chat.index', user=user)


@app.route('/logout')
def logout():
    session.pop('token', None)
    session.pop('email', None)
    return redirect(url_for('index'))

@app.route('/send_message', methods=['POST'])
async def send_message():
    content = request.form.get('content')
    
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN) 
    updates = await bot.getUpdates()

    await bot.sendMessage(chat_id=updates[0].message.chat_id, text=content)

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run()
