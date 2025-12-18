from flask import Flask, render_template, request,redirect,url_for,jsonify
import requests
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///weather.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

load_dotenv()

@app.route("/", methods=["GET", "POST"])
def hello_world():
  
    if request.method == "POST":
        city_name = request.form.get("city", "").strip().title()

        if city_name:
            existing_city = City.query.filter_by(name=city_name).first()
            if not existing_city:
                new_city = City(name=city_name)
                db.session.add(new_city)
                db.session.commit()

    url = f"https://api.openweathermap.org/data/2.5/weather?q={{}}&appid={os.getenv('API_KEY')}&units=metric"

    cities = City.query.all()
    weather_data = []
    

    for city in cities:
        r = requests.get(url.format(city.name)).json()

        if r.get("cod") != 200:
            continue

        weather = {
            "city": city.name,
            "temperature": round(r["main"]["temp"], 1),
            "description": r["weather"][0]["description"],
            "icon": r["weather"][0]["icon"],
            "id": city.id
        }
        weather_data.append(weather)

    return render_template("index.html", weather=weather_data)


@app.route("/delete/<int:city_id>",methods=["POST"])
def delete(city_id):
    city =City.query.get_or_404(city_id)
    db.session.delete(city)
    db.session.commit()
    return redirect(url_for("hello_world"))

@app.route("/api/cities", methods=["GET", "POST"])
def api_cities():
    if request.method == "GET":
        cities = City.query.all()
        return jsonify([
            {"id": city.id, "name": city.name}
            for city in cities
        ])

    if request.method == "POST":
        data = request.get_json()
        city_name = data.get("name", "").strip().title()

        if not city_name:
            return jsonify({"error": "City name required"}), 400

        if City.query.filter_by(name=city_name).first():
            return jsonify({"error": "City already exists"}), 409

        city = City(name=city_name)
        db.session.add(city)
        db.session.commit()

        return jsonify({"id": city.id, "name": city.name}), 201


@app.route("/api/cities/<int:id>", methods=["DELETE"])
def api_delete_city(id):
    city = City.query.get_or_404(id)
    db.session.delete(city)
    db.session.commit()
    return jsonify({"message": "City deleted"})



@app.route("/api/weather", methods=["GET"])
def api_weather():
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={{}}&appid={os.getenv('API_KEY')}&units=metric"
    )

    weather_data = []

    for city in City.query.all():
        r = requests.get(url.format(city.name), timeout=5).json()

        if r.get("cod") != 200:
            continue

        weather_data.append({
            "id": city.id,
            "city": city.name,
            "temperature": round(r["main"]["temp"], 1),
            "description": r["weather"][0]["description"],
            "icon": r["weather"][0]["icon"],
        })

    return jsonify(weather_data)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        app.run(port=8000)
