"""Austin venue sources for the Scout agent.

Each entry is a public calendar page -- no API key required. Every URL here
was verified to return HTTP 200. Adding a city means adding entries here;
nothing else in the app is Austin-specific.

Deliberately excluded: Hotel Vegas, Empire Control Room, Saxon Pub and Hole
in the Wall all return 403 to non-browser clients. That is a clear signal
they do not want automated traffic, so Encore does not scrape them.
"""

VENUES = [
    {"name": "Mohawk", "url": "https://mohawkaustin.com/events/", "size": "medium"},
    {"name": "Emo's", "url": "https://www.emosaustin.com/events", "size": "large"},
    {"name": "Stubb's", "url": "https://stubbsaustin.com/concert-calendar/", "size": "large"},
    {"name": "Antone's", "url": "https://antonesnightclub.com/calendar/", "size": "medium"},
    {"name": "Scoot Inn", "url": "https://www.scootinnaustin.com/events", "size": "medium"},
    {"name": "Continental Club", "url": "https://continentalclub.com/austin", "size": "small"},
    {"name": "ACL Live", "url": "https://www.acllive.com/", "size": "large"},
    {"name": "3TEN ACL Live", "url": "https://www.acllive.com/stages/3ten", "size": "small"},
    {"name": "Far Out Lounge", "url": "https://thefaroutaustin.com/events.html", "size": "small"},
    {"name": "Cactus Cafe", "url": "https://universityunions.utexas.edu/play/cactus-cafe", "size": "small"},
    {"name": "Paramount Theatre", "url": "https://www.austintheatre.org/events/", "size": "large"},
    {"name": "Come and Take It Live", "url": "https://www.comeandtakeitlive.com/", "size": "small"},
]

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
