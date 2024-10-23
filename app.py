from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')
app.secret_key = os.environ.get('SECRET_KEY', 'CLIENT_SECRET')

# Initialize MongoDB client
client = MongoClient(app.config['MONGO_URI'])
db = client['barcode_db']
collection = db['barcodes']

@app.route('/', methods=['GET', 'POST'])
def home():
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
    all_barcodes = collection.find().sort('_id', -1)
    all_barcodes = [{'barcode': b['barcode'], 'timestamp': b['timestamp'], 'trecho': b.get('trecho')} for b in all_barcodes]
    return render_template('history.html', barcodes=all_barcodes)

if __name__ == '__main__':
    app.run(debug=True)
