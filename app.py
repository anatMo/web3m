from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Hard-coded user and password
USERNAME = 'crypto_whale'
PASSWORD = 'js*gnHfcx!'

@app.route('/')
def login_page():
    return render_template('login.html', error=None)

# Login page
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if username == USERNAME and password == PASSWORD:
        return redirect(url_for('tools_page'))
    else:
        return render_template('login.html', error='Invalid credentials.')

 # Tools page
@app.route('/tools')
def tools_page():
    return render_template('tools.html')

if __name__ == '__main__':
    app.run(debug=True)