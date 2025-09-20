from flask import Flask, render_template, redirect, request, url_for
from translations import translations  # <- import from the file

app = Flask(__name__)

@app.route('/')
def index():
    return redirect(url_for('home', lang='en'))

@app.route('/home')
def home():
    lang = request.args.get('lang', 'en')
    if lang not in translations:
        return redirect(url_for('home', lang='en'))

    text = translations[lang]
    return render_template('Home.html', text=text, lang=lang)

if __name__ == '__main__':
    app.run(debug=True)
