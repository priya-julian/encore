"""Encore -- Austin concert discovery driven by your own show history.

Run:  python app.py      then open http://localhost:5000
"""
import secrets
import threading

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from encore import config, events, log, service

config.load_env()

app = Flask(__name__, template_folder="encore/templates",
            static_folder="encore/static")
app.secret_key = secrets.token_hex(16)

_run_lock = threading.Lock()


def sid() -> str:
    if "sid" not in session:
        session["sid"] = secrets.token_hex(6)
    return session["sid"]


@app.route("/")
def discover():
    return render_template("discover.html", page="discover")


@app.route("/api/picks")
def api_picks():
    force = request.args.get("force") == "1"
    with _run_lock:
        result = service.get_picks(force=force)
    if not result.get("error"):
        events.record("run", sid(), count=len(result["picks"]),
                      considered=result.get("considered", 0),
                      cached=result.get("from_cache", False),
                      cost=round(result.get("cost", 0), 5))
    return jsonify(result)


@app.route("/api/event", methods=["POST"])
def api_event():
    body = request.get_json(silent=True) or {}
    kind = str(body.get("kind", ""))[:24]
    if kind not in {"new_to_me", "save", "ticket_click", "not_for_me"}:
        return jsonify({"ok": False}), 400
    events.record(kind, sid(), artist=str(body.get("artist", ""))[:80])
    return jsonify({"ok": True})


@app.route("/log")
def show_log():
    rows = log.read()
    order = {"loved": 0, "liked": 1, "fine": 2, "meh": 3}
    rows.sort(key=lambda r: (order.get(r["gut_rating"], 9), r["artist"].lower()))
    return render_template("log.html", page="log", rows=rows,
                           source=log.log_path().name)


@app.route("/log/add", methods=["POST"])
def add_show():
    rows = log.read(config.DATA_DIR / "concert_log.csv")
    form = request.form
    artist = (form.get("artist") or "").strip()
    if artist:
        rows.append({
            "artist": artist,
            "date": (form.get("date") or "").strip(),
            "venue": (form.get("venue") or "").strip(),
            "city": (form.get("city") or "Austin TX").strip(),
            "openers": (form.get("openers") or "").strip(),
            "gut_rating": (form.get("gut_rating") or "liked").strip(),
            "notes": (form.get("notes") or "").strip(),
        })
        log.write(rows)
        events.record("add_show", sid(), artist=artist[:80])
    return redirect(url_for("show_log"))


@app.route("/taste")
def taste():
    return render_template("taste.html", page="taste")


@app.route("/api/profile")
def api_profile():
    from encore import llm
    from encore import events as ev

    rows = log.read()
    if not rows:
        return jsonify({"error": "no shows in your log yet"})
    return jsonify(service.get_profile(rows, llm.Meter(),
                                       rejected=ev.rejected_artists()))


@app.route("/api/events.jsonl")
def api_events():
    """Raw anonymous usage events.

    Render's free tier wipes the filesystem when the service sleeps or
    redeploys, so this exists to pull the impact data down before that
    happens. It contains an anonymous session id and artist names, nothing
    identifying.
    """
    from flask import Response

    from encore import events as ev

    path = ev.EVENTS_PATH
    body = path.read_text(encoding="utf-8") if path.is_file() else ""
    return Response(body, mimetype="application/x-ndjson")


@app.route("/impact")
def impact():
    return render_template("impact.html", page="impact", stats=events.summary())


if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
