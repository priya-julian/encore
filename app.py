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
        result = service.get_picks(force=force, session=sid())
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
    session_id = sid()
    rows = log.read(session=session_id)
    order = {"loved": 0, "liked": 1, "fine": 2, "meh": 3}
    rows.sort(key=lambda r: (order.get(r["gut_rating"], 9), r["artist"].lower()))
    return render_template("log.html", page="log", rows=rows,
                           own=log.is_own_log(session_id))


@app.route("/log/add", methods=["POST"])
def add_show():
    session_id = sid()
    artist = (request.form.get("artist") or "").strip()
    if artist:
        log.add(session_id, {
            "artist": artist,
            "date": request.form.get("date", ""),
            "venue": request.form.get("venue", ""),
            "city": request.form.get("city") or "Austin TX",
            "openers": request.form.get("openers", ""),
            "gut_rating": request.form.get("gut_rating") or "liked",
            "notes": request.form.get("notes", ""),
        })
        events.record("add_show", session_id, artist=artist[:80])
    return redirect(url_for("show_log"))


@app.route("/log/bulk", methods=["POST"])
def add_bulk():
    """Paste a list of shows, one per line. Far less friction than a form."""
    session_id = sid()
    parsed = log.parse_bulk(request.form.get("bulk") or "")
    if parsed:
        existing = log.read(log.user_path(session_id))
        log.write(existing + parsed, session=session_id)
        events.record("add_bulk", session_id, count=len(parsed))
    return redirect(url_for("show_log"))


@app.route("/log/reset", methods=["POST"])
def reset_log():
    """Start over with an empty log of your own."""
    session_id = sid()
    path = log.user_path(session_id)
    if path.is_file():
        path.unlink()
    return redirect(url_for("show_log"))


@app.route("/taste")
def taste():
    return render_template("taste.html", page="taste")


@app.route("/api/profile")
def api_profile():
    from encore import llm

    session_id = sid()
    rows = log.read(session=session_id)
    if not rows:
        return jsonify({"error": "no shows in your log yet"})
    return jsonify(service.get_profile(
        rows, llm.Meter(), rejected=events.rejected_artists(session_id)))


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
