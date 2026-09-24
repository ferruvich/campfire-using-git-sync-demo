#!/usr/bin/env python3
"""Apply scenario user profiles and organization roles using gcx api."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


SCENARIO_DIR = Path(__file__).resolve().parent.parent
ORG_ID = 1
FIELDS = {"login", "name", "email", "role", "password_env"}


class SetupError(Exception):
    pass


def load_users():
    try:
        users = json.loads((SCENARIO_DIR / "users.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise SetupError("Could not read users.json: {}".format(error)) from None
    if not isinstance(users, list):
        raise SetupError("users.json must contain an array of user definitions.")

    logins, emails = set(), set()
    for index, user in enumerate(users, start=1):
        label = "users.json entry {}".format(index)
        if not isinstance(user, dict) or set(user) != FIELDS:
            raise SetupError(label + " must define login, name, email, role, and password_env only.")
        if any(not isinstance(value, str) or not value.strip() for value in user.values()):
            raise SetupError(label + " must contain nonempty strings.")
        if any(value != value.strip() or any(ord(char) < 32 for char in value)
               for value in user.values()):
            raise SetupError(label + " cannot contain control characters or surrounding whitespace.")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", user["login"]):
            raise SetupError(label + " login must use letters, digits, dots, underscores, or hyphens.")
        if not re.fullmatch(r"[^@\s]+@[^@\s]+", user["email"]):
            raise SetupError(label + " must have an email address.")
        # Grafana stores email addresses in lowercase.
        user["email"] = user["email"].lower()
        if user["role"] not in {"Viewer", "Editor", "Admin"}:
            raise SetupError(label + " role must be Viewer, Editor, or Admin.")
        if not re.fullmatch(r"GRAFANA_[A-Z0-9_]+_PASSWORD", user["password_env"]):
            raise SetupError(label + " password_env must name a GRAFANA_*_PASSWORD variable.")
        login, email = user["login"].casefold(), user["email"].casefold()
        if login in logins or email in emails:
            raise SetupError(label + " repeats a username or email address.")
        logins.add(login)
        emails.add(email)
    return users


def numeric_id(value, label):
    if isinstance(value, bool) or not re.fullmatch(r"[1-9][0-9]*", str(value)):
        raise SetupError("Invalid {} returned by Grafana.".format(label))
    return int(value)


class Grafana:
    def __init__(self, users):
        self.executable = shutil.which("gcx")
        if not self.executable:
            raise SetupError("gcx is required on PATH; see the scenario README.")
        if not (SCENARIO_DIR / "gcx.yaml").is_file():
            raise SetupError("The scenario gcx.yaml file is missing.")
        self.secrets = [os.environ[user["password_env"]] for user in users
                        if os.environ.get(user["password_env"])]

    def redact(self, message):
        for secret in sorted(self.secrets, key=len, reverse=True):
            message = message.replace(json.dumps(secret)[1:-1], "[redacted]")
            message = message.replace(secret, "[redacted]")
        return message[:2000]

    def request(self, method, path, body=None, expected_message=None):
        command = [
            self.executable, "api", path,
            "--config={}".format(SCENARIO_DIR / "gcx.yaml"), "--context=default",
            "--output=json", "--agent=false", "--log-http-payload=false",
            "--method", method,
        ]
        if body is not None:
            command += ["--header", "Content-Type: application/json", "--data", "@-"]
        try:
            result = subprocess.run(
                command, input=json.dumps(body) if body is not None else "",
                capture_output=True, text=True, timeout=30, check=False,
            )
        except subprocess.TimeoutExpired:
            raise SetupError("{} {} timed out after 30 seconds; rerun setup-users.".format(method, path)) from None
        except OSError as error:
            raise SetupError("Could not start gcx: {}".format(error)) from None
        if result.returncode:
            detail = self.redact(result.stderr.strip() or result.stdout.strip())
            raise SetupError("{} {} failed (gcx exit {}): {}".format(
                method, path, result.returncode, detail))
        try:
            response = json.loads(result.stdout)
        except ValueError:
            raise SetupError("{} {} returned invalid JSON.".format(method, path)) from None
        if expected_message is not None:
            if not isinstance(response, dict) or response.get("message") != expected_message:
                raise SetupError("{} {} did not confirm success: {}".format(
                    method, path, self.redact(json.dumps(response))))
        return response

    def list_users(self):
        users, seen_ids = [], set()
        page = 1
        while True:
            batch = self.request("GET", "/api/users?perpage=1000&page={}".format(page))
            if not isinstance(batch, list):
                raise SetupError("Could not list users. Use a Grafana server administrator with basic authentication.")
            for user in batch:
                if not isinstance(user, dict) or not isinstance(user.get("login"), str):
                    raise SetupError("Unexpected user record returned by Grafana.")
                user_id = numeric_id(user.get("id"), "user ID")
                if user_id in seen_ids:
                    raise SetupError("User pagination repeated an ID; rerun setup-users.")
                if not isinstance(user.get("isAdmin"), bool):
                    raise SetupError("Grafana did not return the user's server administrator status.")
                seen_ids.add(user_id)
                users.append(user)
            if len(batch) < 1000:
                return users
            page += 1

    def org_members(self):
        response = self.request("GET", "/api/orgs/{}/users".format(ORG_ID))
        if not isinstance(response, list):
            raise SetupError("Could not list users in organization {}.".format(ORG_ID))
        members = {}
        for member in response:
            if not isinstance(member, dict) or not isinstance(member.get("role"), str):
                raise SetupError("Unexpected organization membership returned by Grafana.")
            members[numeric_id(member.get("userId"), "organization user ID")] = member["role"]
        return members


def setup_users():
    definitions = load_users()
    if not definitions:
        print("No users defined in users.json.")
        return
    grafana = Grafana(definitions)
    actor = grafana.request("GET", "/api/user")
    if not isinstance(actor, dict) or actor.get("isGrafanaAdmin") is not True:
        raise SetupError("The default gcx context must authenticate as a Grafana server administrator.")
    actor_id = numeric_id(actor.get("id"), "authenticated user ID")
    existing_users = grafana.list_users()
    members = grafana.org_members()

    # Resolve every identity and validate every creation password before any writes.
    plan = []
    for desired in definitions:
        matches = [user for user in existing_users
                   if user["login"].casefold() == desired["login"].casefold()]
        if len(matches) > 1:
            raise SetupError("More than one account matches {}.".format(desired["login"]))
        existing = matches[0] if matches else None
        user_id = numeric_id(existing["id"], "user ID") if existing else None
        if existing and (existing["isAdmin"] or user_id == actor_id):
            raise SetupError("Refusing to manage the administrator account {}.".format(desired["login"]))
        for other in existing_users:
            if str(other.get("email", "")).casefold() == desired["email"].casefold():
                if numeric_id(other["id"], "user ID") != user_id:
                    raise SetupError("Email for {} belongs to another account; choose a different email.".format(desired["login"]))
        if existing is None:
            password = os.environ.get(desired["password_env"], "")
            if len(password) < 4:
                raise SetupError("Set {} in the root .env or exported environment to at least four characters before creating {}.".format(
                    desired["password_env"], desired["login"]))
        plan.append((desired, existing))

    for desired, existing in plan:
        login = existing["login"] if existing else desired["login"]
        profile = {"login": login, "name": desired["name"], "email": desired["email"]}
        changed = False
        if existing is None:
            body = dict(profile, OrgId=ORG_ID, password=os.environ[desired["password_env"]])
            response = grafana.request("POST", "/api/admin/users", body, "User created")
            user_id = numeric_id(response.get("id"), "created user ID")
            # Respect actual auto-assignment rather than assuming creation added membership.
            members = grafana.org_members()
            print("Created {}.".format(login), flush=True)
            changed = True
        else:
            user_id = numeric_id(existing["id"], "user ID")
            if any(existing.get(field) != desired[field] for field in ("name", "email")):
                current_profile = grafana.request("GET", "/api/users/{}".format(user_id))
                if not isinstance(current_profile, dict) or numeric_id(current_profile.get("id"), "profile user ID") != user_id:
                    raise SetupError("Grafana returned an unexpected user profile.")
                # The profile API also accepts theme; preserve the user's choice.
                if isinstance(current_profile.get("theme"), str):
                    profile["theme"] = current_profile["theme"]
                grafana.request("PUT", "/api/users/{}".format(user_id), profile, "User updated")
                print("Updated profile for {}.".format(login), flush=True)
                changed = True

        if user_id not in members:
            grafana.request("POST", "/api/orgs/{}/users".format(ORG_ID),
                            {"loginOrEmail": login, "role": desired["role"]}, "User added to organization")
            changed = True
        elif members[user_id] != desired["role"]:
            grafana.request("PATCH", "/api/orgs/{}/users/{}".format(ORG_ID, user_id),
                            {"role": desired["role"]}, "Organization user updated")
            changed = True
        members[user_id] = desired["role"]
        print("{}: {} in organization {} ({}).".format(
            login, desired["role"], ORG_ID, "applied" if changed else "already configured"), flush=True)


if __name__ == "__main__":
    try:
        setup_users()
    except SetupError as error:
        print("Error: {}".format(error), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("User setup interrupted; rerun setup-users to finish.", file=sys.stderr)
        sys.exit(130)
