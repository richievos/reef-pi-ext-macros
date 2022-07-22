import json, requests


class ReefPiClient(object):
    """A client for interacting with a ReefPi system through its api."""

    def __init__(self, hostname):
        self.hostname = hostname

    ####################
    def login_and_set_session(self, user, password):
       session = requests.Session();
       session.post(self._url("/auth/signin"), data = json.dumps({"user":user,"password":password}))
       # TODO: error
       self.session = session
       return session


    ####################
    def get_temps(self):
        r = self.session.get(self._url("/api/tcs"))
        if r.status_code != 200:
            raise Exception(f"Could not fetch temps, status_code={r.status_code}")
        return json.loads(r.text)


    # { "temperature": 78.35 }
    def get_current_reading(self, temp_id):
        r = self.session.get(self._url("/api/tcs/{id}/current_reading".format(id=temp_id)))
        if r.status_code != 200:
            raise Exception(f"Could not fetch current_reading, status_code={r.status_code}")

        return json.loads(r.text)


    ####################
    def get_macros(self):
        r = self.session.get(self._url("/api/macros"))
        if r.status_code != 200:
            raise Exception(f"Could not fetch macros, status_code={r.status_code}")
        return json.loads(r.text)


    ####################
    def get_lights(self):
        r = self.session.get(self._url("/api/lights"))
        if r.status_code != 200:
            raise Exception(f"Could not fetch lights, status_code={r.status_code}")
        return json.loads(r.text)


    def update_light(self, light):
        if not light["id"]:
            raise Exception("Must pass in a light with an id")

        light_id = light["id"]
        r = self.session.post(self._url(f"/api/lights/{light_id}"), data=json.dumps(light))
        if r.status_code != 200:
            raise Exception(f"Could not update light with id={light_id}, status_code={r.status_code}")

        return None


    def _url(self, path):
        return "http://{hostname}{path}".format(hostname=self.hostname, path=path)
