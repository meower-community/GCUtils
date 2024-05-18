import bottle
import json
import waitress
from database import Database

Bottle = bottle.Bottle()
bottle.TEMPLATE_PATH = ["templates"]




def run_Bottle():
    waitress.serve(Bottle, host="127.0.0.1", port=2400, trusted_proxy="127.0.0.1", trusted_proxy_headers=["X-Forwarded-For"])





def render_json():
    data = Database.get_all_groupchats()

    ret = []
    for groupc in data:

        if not groupc["settings"]["public"]:
            continue

        ret.append({
            "nickname": groupc["data"]["nickname"],
            "uuid": groupc["_id"]
        })
    return ret

try:
    messages = render_json()

except Exception as e:
    print(f"{e.__class__.__name__}: {e}")
    messages = []
    api_messages = []


@Bottle.route("/rerender") # type: ignore
def rerender():
    if bottle.request.remote_addr != "127.0.0.1":
        return bottle.HTTPResponse("", 403)

    global messages
    messages = render_json()

    return ""


@Bottle.route("/api/chats")  # type: ignore
def api_chats():
    bottle.response.content_type = 'application/json; charset=UTF8'
    return json.dumps(messages)  # type: ignore


@Bottle.route("/") # type: ignore
@bottle.jinja2_view("/rerender")
def web():
    bottle.response.content_type = 'text/html; charset=UTF8'
    return bottle.jinja2_template("index.html", messages=messages)


@Bottle.route("/<path:path>") # type: ignore
def index_js(path):
    return bottle.static_file(path, root="static")


if __name__ == "__main__":
    run_Bottle()
