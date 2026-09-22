from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>Campus Exchange</h1><p>Welcome! The app is running.</p>"

if __name__ == "__main__":
    app.run(debug=True)