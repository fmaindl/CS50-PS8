import os
import re
from flask import Flask, jsonify, render_template, request

from cs50 import SQL
from helpers import lookup

# Configure application
app = Flask(__name__)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mashup.db")

# Disable pretty JSON
# https://github.com/pallets/flask/issues/2549
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    """Render map"""
    return render_template("index.html")


@app.route("/articles")
def articles():
    """Look up articles for geo"""


    location = request.args.get("geo")

    if not location:
        raise RuntimeError("missing argument")

    articles = lookup(location)

    return jsonify(articles)





@app.route("/search")
def search():
    """Search for places that match query"""


    q = request.args.get("q") + "%"


    comma = q.count(",")
    space = q.count(" ")


    search = db.execute("SELECT * FROM place WHERE postal_code LIKE :q OR place_name LIKE :q OR admin_name1 LIKE :q OR admin_code1 LIKE :q", q = q);


    if len(search) == 0:

        if comma == 1:
            q = q.split(",")
            q[1] = q[1].strip(" ")
            search = db.execute("SELECT * FROM place WHERE place_name LIKE :q0 AND admin_name1 LIKE :q1 OR place_name LIKE :q0 AND admin_code1 LIKE :q1 OR place_name LIKE :q0 AND postal_code LIKE :q1 OR admin_name1 LIKE :q0 AND postal_code LIKE :q1 OR admin_code1 LIKE :q0 AND postal_code LIKE :q1", q0 = q[0], q1 = q[1]);

        elif space == 1:
                q = q.split(" ")
                search = db.execute("SELECT * FROM place WHERE place_name LIKE :q0 AND admin_name1 LIKE :q1 OR place_name LIKE :q0 AND admin_code1 LIKE :q1 OR place_name LIKE :q0 AND postal_code LIKE :q1 OR admin_name1 LIKE :q0 AND postal_code LIKE :q1 OR admin_code1 LIKE :q0 AND postal_code LIKE :q1", q0 = q[0], q1 = q[1]);

        elif space == 2:
            q = q.split(" ")
            q_ = [q[0], q[1] + ' ' + q[2]]
            q = [q[0] + ' ' + q[1], q[2]]
            search = db.execute("SELECT * FROM place WHERE place_name LIKE :q0 AND admin_name1 LIKE :q1 OR place_name LIKE :q0 AND admin_code1 LIKE :q1 OR place_name LIKE :q0 AND postal_code LIKE :q1 OR admin_name1 LIKE :q0 AND postal_code LIKE :q1 OR admin_code1 LIKE :q0 AND postal_code LIKE :q1", q0 = q[0], q1 = q[1]);

            if not search:
                search = db.execute("SELECT * FROM place WHERE place_name LIKE :q_0 AND admin_name1 LIKE :q_1 OR place_name LIKE :q_0 AND admin_code1 LIKE :q_1 OR place_name LIKE :q_0 AND postal_code LIKE :q_1 OR admin_name1 LIKE :q_0 AND postal_code LIKE :q_1 OR admin_code1 LIKE :q_0 AND postal_code LIKE :q_1", q_0 = q_[0], q_1 = q_[1]);

        elif comma == 2:
                q = q.split (",")
                q[1] = q[1].strip(" ")
                q[2] = q[2].strip(" ")
                search = db.execute("SELECT * FROM place WHERE place_name LIKE :q0 AND admin_name1 LIKE :q1 AND country_code LIKE :q2 OR place_name LIKE :q0 AND admin_code1 LIKE :q1 AND country_code LIKE :q2 OR place_name LIKE :q0 AND postal_code LIKE :q1 AND country_code LIKE :q2 OR admin_name1 LIKE :q0 AND postal_code LIKE :q1 AND country_code LIKE :q2 OR admin_code1 LIKE :q0 AND postal_code LIKE :q1 AND country_code LIKE :q2", q0 = q[0], q1 = q[1], q2 = q[2]);



    return jsonify(search)


@app.route("/update")
def update():
    """Find up to 10 places within view"""

    # Ensure parameters are present
    if not request.args.get("sw"):
        raise RuntimeError("missing sw")
    if not request.args.get("ne"):
        raise RuntimeError("missing ne")

    # Ensure parameters are in lat,lng format
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("sw")):
        raise RuntimeError("invalid sw")
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("ne")):
        raise RuntimeError("invalid ne")

    # Explode southwest corner into two variables
    sw_lat, sw_lng = map(float, request.args.get("sw").split(","))

    # Explode northeast corner into two variables
    ne_lat, ne_lng = map(float, request.args.get("ne").split(","))

    # Find 10 cities within view, pseudorandomly chosen if more within view
    if sw_lng <= ne_lng:

        # Doesn't cross the antimeridian
        rows = db.execute("""SELECT * FROM place
                          WHERE :sw_lat <= latitude AND latitude <= :ne_lat AND (:sw_lng <= longitude AND longitude <= :ne_lng)
                          GROUP BY country_code, place_name, admin_code1
                          ORDER BY RANDOM()
                          LIMIT 10""",
                          sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    else:

        # Crosses the antimeridian
        rows = db.execute("""SELECT * FROM place
                          WHERE :sw_lat <= latitude AND latitude <= :ne_lat AND (:sw_lng <= longitude OR longitude <= :ne_lng)
                          GROUP BY country_code, place_name, admin_code1
                          ORDER BY RANDOM()
                          LIMIT 10""",
                          sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    # Output places as JSON
    return jsonify(rows)
