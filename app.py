from flask import Flask, render_template, request
import requests
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///weather.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

@app.route("/", methods=["GET", "POST"])
def hello_world():
    if request.method == "POST":
        city_name = request.form.get("city")

        if city_name:
            existing_city = City.query.filter_by(name=city_name).first()
            if not existing_city:
                new_city = City(name=city_name)
                db.session.add(new_city)
                db.session.commit()

    url = "https://api.openweathermap.org/data/2.5/weather?q={}&appid=edae26e708808e0debd8123af6c6b546"

    cities = City.query.all()
    weather_data = []

    for city in cities:
        r = requests.get(url.format(city.name)).json()

        if r.get("cod") != 200:
            continue

        weather = {
            "city": city.name,
            "temperature": round(r["main"]["temp"] - 273.15, 1),
            "description": r["weather"][0]["description"],
            "icon": r["weather"][0]["icon"]
        }
        weather_data.append(weather)

    return render_template("index.html", weather=weather_data)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)
