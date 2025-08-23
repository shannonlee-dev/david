from flask import Flask, render_template
import socket

app = Flask(__name__)

@app.route("/menu")
def home():
    if app.debug:
        hostname = '컴퓨터(인스턴스) : ' + socket.gethostname()
    else:
        hostname = ' '
    return render_template("menu.html",computername=hostname)
    
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8800, debug = True)
