from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
app.secret_key = os.getenv('SECRET_KEY')

# Initialize MongoDB client
client = MongoClient(app.config['MONGO_URI'])
db = client['barcode_db']
collection = db['barcodes']

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
