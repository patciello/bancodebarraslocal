from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
import os
from dotenv import load_dotenv

#Google OAuth
from authlib.integrations.flask_client import OAuth


# Carregando as credenciais do arquivo JSON
with open('config/credentials.json') as f:
    credentials = json.load(f)



app = Flask(__name__)

# Load environment variables
load_dotenv()
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')
app.secret_key = os.environ.get('SECRET_KEY', 'minha_chave_secreta')

# Initialize MongoDB client
client = MongoClient(app.config['MONGO_URI'])
db = client['barcode_db']
collection = db['barcodes']


# Configuração do OAuth usando as credenciais do JSON
oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=credentials['web']['client_id'],
    client_secret=credentials['web']['client_secret'],
    access_token_url=credentials['web']['token_uri'],
    authorize_url=credentials['web']['auth_uri'],
    authorize_redirect_uri=credentials['web']['redirect_uris'][0],  # Usando o primeiro redirect_uri da lista
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid profile email'}
)




@app.route('/')
def index():
    if 'google_token' in session:
        user = oauth.google.get('userinfo').json()
        return f"Você está logado como {user['email']}"
    return redirect(url_for('login'))

@app.route('/login')
def login():
    redirect_uri = url_for('auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/auth')
def auth():
    token = oauth.google.authorize_access_token()
    session['google_token'] = token
    user = oauth.google.get('userinfo').json()
    session['user_info'] = user
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('google_token', None)
    session.pop('user_info', None)
    return redirect('/')



@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        barcode = request.form.get('barcode')
        if collection.find_one({'barcode': barcode}):
            flash('Código de barras já foi adicionado!', 'warning')
        else:
            collection.insert_one({'barcode': barcode})
            flash('Código de barras adicionado com sucesso!', 'success')
        return redirect(url_for('home'))
    # Retrieve the last 10 barcodes
    recent_barcodes = collection.find().sort('_id', -1).limit(10)
    return render_template('home.html', barcodes=recent_barcodes)

@app.route('/history')
def history():
    all_barcodes = collection.find().sort('_id', -1)
    return render_template('history.html', barcodes=all_barcodes)

if __name__ == '__main__':
    app.run(debug=True)
