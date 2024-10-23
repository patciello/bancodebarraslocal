from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Google OAuth
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)

# Load environment variables
load_dotenv()
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')
app.secret_key = os.environ.get('SECRET_KEY', 'CLIENT_SECRET')

# Initialize MongoDB client
client = MongoClient(app.config['MONGO_URI'])
db = client['barcode_db']
collection = db['barcodes']

# Configuração do OAuth usando as credenciais do JSON
oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    access_token_url=os.environ.get('GOOGLE_TOKEN_URI'),
    authorize_url=os.environ.get('GOOGLE_AUTH_URI'),
    authorize_redirect_uri=os.environ.get('GOOGLE_REDIRECT_URI'),
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid profile email'}
)

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'google_token' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        barcode = request.form.get('barcode')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if len(barcode) == 44:
            trecho = barcode[26:34]
            barcode_data = {'barcode': barcode, 'timestamp': timestamp, 'trecho': trecho}
        else:
            barcode_data = {'barcode': barcode, 'timestamp': timestamp}
        
        if collection.find_one({'barcode': barcode}):
            flash('Código de barras já foi adicionado!', 'warning')
        else:
            collection.insert_one(barcode_data)
            flash('Código de barras adicionado com sucesso!', 'success')
        return redirect(url_for('home'))
    
    # Recupera os últimos 10 códigos de barras
    recent_barcodes = collection.find().sort('_id', -1).limit(10)
    recent_barcodes = [{'barcode': b['barcode'], 'timestamp': b['timestamp'], 'trecho': b.get('trecho')} for b in recent_barcodes]
    return render_template('home.html', barcodes=recent_barcodes)

# Rota para visualizar o histórico de códigos de barras
@app.route('/history')
def history():
    if 'google_token' not in session:
        return redirect(url_for('login'))
    
    all_barcodes = collection.find().sort('_id', -1)
    all_barcodes = [{'barcode': b['barcode'], 'timestamp': b['timestamp'], 'trecho': b.get('trecho')} for b in all_barcodes]
    return render_template('history.html', barcodes=all_barcodes)

# Rota de login
@app.route('/login')
def login():
    redirect_uri = url_for('auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

# Rota de autenticação
@app.route('/auth')
def auth():
    token = oauth.google.authorize_access_token()
    session['google_token'] = token
    user = oauth.google.get('userinfo').json()
    session['user_info'] = user
    return redirect(url_for('home'))

# Rota de logout
@app.route('/logout')
def logout():
    session.pop('google_token', None)
    session.pop('user_info', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
