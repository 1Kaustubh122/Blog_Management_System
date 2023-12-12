from flask import Flask, render_template, request, redirect, url_for,jsonify,abort
from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime
import urllib.request
import json 
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/kaustubhkrishna/Documents/Mini_Proj_23/blog.db'

db = SQLAlchemy(app)

class Blogpost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50))
    subtitle = db.Column(db.String(50))
    author = db.Column(db.String(20))
    date_posted = db.Column(db.DateTime)
    content = db.Column(db.Text)
    views = db.Column(db.Integer, default=0)




@app.route('/')
def index():
    posts = Blogpost.query.order_by(Blogpost.date_posted.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/post/<int:post_id>')
def post(post_id):
    post = Blogpost.query.get(post_id)
    if post:
        post.views += 1  # Increment the views count
        db.session.commit()  # Save the updated views count to the database
        return render_template('post.html', post=post)
    else:
        abort(404)

@app.route('/add')
def add():
    return render_template('add.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')
@app.route('/weather', methods =['POST', 'GET']) 
def weather():
    try:
        if request.method == 'POST': 
            city = request.form['city']
            city=city.lower()
            if city=='':
                city='chennai'
        else: 
            city = 'chennai'
        source =urllib.request.urlopen('https://api.openweathermap.org/data/2.5/weather?q='+city+'&appid=7bbd0b4c0ed5d239150d327613a714e2').read()
        list_of_data = json.loads(source) 
    except:
        city = 'chennai'
        source =urllib.request.urlopen('https://api.openweathermap.org/data/2.5/weather?q='+city+'&appid=7bbd0b4c0ed5d239150d327613a714e2').read()
        list_of_data = json.loads(source) 
    # data for variable list_of_data 
    data = {
        "cityname":city.capitalize(),
        "country_code": str(list_of_data['sys']['country']), 
        "coordinate": str(list_of_data['coord']['lon']) + ' ' 
                    + str(list_of_data['coord']['lat']), 
        "temp": str(list_of_data['main']['temp']) + 'k', 
        "pressure": str(list_of_data['main']['pressure']), 
        "humidity": str(list_of_data['main']['humidity']), 
    } 
    print(data) 
    return render_template('index1.html', data = data) 

@app.route('/addpost', methods=['POST'])
def addpost():
    title = request.form['title']
    subtitle = request.form['subtitle']
    author = request.form['author']
    content = request.form['content']

    post = Blogpost(title=title, subtitle=subtitle, author=author, content=content, date_posted=datetime.now())

    db.session.add(post)
    db.session.commit()

    return redirect(url_for('index'))

tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")

@app.route("/bot")
def bot():
    return render_template('ChatBot.html')


@app.route("/get", methods=["GET", "POST"])
def chat():
    msg = request.form["msg"]
    input = msg
    return get_Chat_response(input)

def get_Chat_response(text):
    print(input)
    # Let's chat for 5 lines
    for step in range(5):
        new_user_input_ids = tokenizer.encode(str(text) + tokenizer.eos_token, return_tensors='pt')

        bot_input_ids = torch.cat([chat_history_ids, new_user_input_ids], dim=-1) if step > 0 else new_user_input_ids

        chat_history_ids = model.generate(bot_input_ids, max_length=1000, pad_token_id=tokenizer.eos_token_id)

        return tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)
    
@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = Blogpost.query.get_or_404(post_id)
    
    if request.method == 'POST':
        post.title = request.form['title']
        post.subtitle = request.form['subtitle']
        post.content = request.form['content']
        db.session.commit()
        return redirect(url_for('post', post_id=post.id)) 
    
    return render_template('edit_post.html', post=post)


# Route to delete a specific post
@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    post = Blogpost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('index'))

    
if __name__ == '__main__':
    app.run(port=2000)