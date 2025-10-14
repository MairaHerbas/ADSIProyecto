from flask import Flask, render_template, request, jsonify
import webbrowser
import threading

app = Flask(__name__)

@app.route("/")
def home():
    # Renderiza la interfaz HTML (index.html)
    return render_template("index.html")

@app.route("/api/calcular", methods=["POST"])
def calcular():
    data = request.get_json()
    try:
        x = float(data.get("x", 0))
        return jsonify({"resultado": x * 2})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    url = "http://127.0.0.1:5000/"
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    app.run(debug=True)
