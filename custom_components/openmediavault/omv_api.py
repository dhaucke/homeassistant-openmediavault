"""OpenMediaVault API."""

import json
import logging
from os import path
from typing import Any
from pickle import dump as pickle_dump
from pickle import load as pickle_load
from threading import Lock
from time import time

import requests
from voluptuous import Optional

_LOGGER = logging.getLogger(__name__)


# ---------------------------
#   load_cookies
# ---------------------------
def load_cookies(filename: str) -> Optional(dict):
    """Load cookies from file."""
    if path.isfile(filename):
        with open(filename, "rb") as f:
            return pickle_load(f)
    return None


# ---------------------------
#   save_cookies
# ---------------------------
def save_cookies(filename: str, data: dict):
    """Save cookies to file."""
    with open(filename, "wb") as f:
        pickle_dump(data, f)


# ---------------------------
#   OpenMediaVaultAPI
# ---------------------------
class OpenMediaVaultAPI(object):
    """Handle all communication with OMV."""

    def __init__(self, hass, host, username, password, use_ssl=False, verify_ssl=True):
        """Initialize the OMV API."""
        self._hass = hass
        self._host = host
        self._use_ssl = use_ssl
        self._username = username
        self._password = password
        self._protocol = "https" if self._use_ssl else "http"
        self._ssl_verify = verify_ssl
        if not self._use_ssl:
            self._ssl_verify = True
        self._resource = f"{self._protocol}://{self._host}/rpc.php"

        self.lock = Lock()

        self._connection = None
        self._cookie_jar = None
        self._cookie_jar_file = self._hass.config.path(".omv_cookies.json")
        self._connected = False
        self._reconnected = False
        self._connection_epoch = 0
        self._connection_retry_sec = 58
        self.error = None
        self.connection_error_reported = False
        self.accounting_last_run = None

    # ---------------------------
    #   has_reconnected
    # ---------------------------
    def has_reconnected(self) -> bool:
        """Check if API has reconnected."""
        if self._reconnected:
            self._reconnected = False
            return True

        return False

    # ---------------------------
    #   connection_check
    # ---------------------------
    def connection_check(self) -> bool:
        """Check if API is connected."""
        if not self._connected or not self._connection:
            if self._connection_epoch > time() - self._connection_retry_sec:
                return False

            if not self.connect():
                return False

        return True

    # ---------------------------
    #   disconnect
    # ---------------------------
    def disconnect(self, location="unknown", error=None):
        """Disconnect API."""
        if not error:
            error = "unknown"

        if not self.connection_error_reported:
            if location == "unknown":
                _LOGGER.error("OpenMediaVault %s connection closed", self._host)
            else:
                _LOGGER.error(
                    "OpenMediaVault %s error while %s : %s", self._host, location, error
                )

            self.connection_error_reported = True

        self._reconnected = False
        self._connected = False
        self._connection = None
        self._connection_epoch = 0

    # ---------------------------
    #   connect
    # ---------------------------
    def connect(self) -> bool:
        """Connect API."""
        self.error = None
        self._connected = False
        self._connection_epoch = time()
        self._connection = requests.Session()
        self._cookie_jar = requests.cookies.RequestsCookieJar()

        # Load cookies
        if cookies := load_cookies(self._cookie_jar_file):
            self._connection.cookies.update(cookies)

        self.lock.acquire()
        error = False
        try:
            response = self._connection.post(
                self._resource,
                data=json.dumps(
                    {
                        "service": "session",
                        "method": "login",
                        "params": {
                            "username": self._username,
                            "password": self._password,
                        },
                    }
                ),
                verify=self._ssl_verify,
            )

            if response.status_code != 200:
                error = True

            data = response.json()
            if data["error"] is not None:
                if not self.connection_error_reported:
                    _LOGGER.error(
                        "OpenMediaVault %s unable to connect: %s",
                        self._host,
                        data["error"]["message"],
                    )
                    self.connection_error_reported = True

                self.error_to_strings("%s" % data["error"]["message"])
                self._connection = None
                self.lock.release()
                return False

            resp = data["response"]

            # OMV >= 8.5.0 uses "status" string instead of "authenticated" bool
            if "authenticated" in resp:
                # Legacy schema (OMV < 8.5.0)
                authenticated = resp["authenticated"]
            elif "status" in resp:
                # New schema (OMV >= 8.5.0)
                authenticated = resp["status"] == "authenticated"
            else:
                # Unknown schema - log for debugging
                _LOGGER.warning(
                    "OpenMediaVault %s unexpected auth response schema: %s",
                    self._host,
                    list(resp.keys()),
                )
                authenticated = False

            if not authenticated:
                _LOGGER.error("OpenMediaVault %s authenticated failed", self._host)
                self.error_to_strings()
                self._connection = None
                self.lock.release()
                return False

        except requests.exceptions.ConnectionError as api_error:
            error = True
            self.error_to_strings("%s" % api_error)
            self._connection = None
        except (
            requests.exceptions.Timeout,
            requests.exceptions.RequestException,
        ) as api_error:
            error = True
            self.error_to_strings("%s" % api_error)
            self._connection = None
        except json.decoder.JSONDecodeError as api_error:
            # The request itself succeeded (we have an HTTP response), but the
            # body wasn't valid JSON - previously this fell through to the
            # generic "unexpected error" branch below, which never logged the
            # actual response content, so the real cause (an HTML error page,
            # an auth/CSRF redirect, a proxy in the way, etc.) was invisible
            # and the user only ever saw the generic "cannot_connect" error.
            error = True
            body_preview = (response.text or "")[:500] if response is not None else ""
            _LOGGER.error(
                "OpenMediaVault %s returned a non-JSON response (HTTP %s): %s | %s",
                self._host,
                getattr(response, "status_code", "unknown"),
                api_error,
                body_preview or "<empty body>",
            )
            self._connection = None
        except Exception as api_error:
            error = True
            _LOGGER.warning(
                "OpenMediaVault %s unexpected error during connect: %s",
                self._host,
                api_error,
            )
        else:
            if self.connection_error_reported:
                _LOGGER.warning("OpenMediaVault %s reconnected", self._host)
                self.connection_error_reported = False
            else:
                _LOGGER.debug("OpenMediaVault %s connected", self._host)

            self._connected = True
            self._reconnected = True
            self.lock.release()
            for cookie in self._connection.cookies:
                self._cookie_jar.set_cookie(cookie)

            save_cookies(self._cookie_jar_file, self._cookie_jar)

        # Socket errors
        if error:
            try:
                errorcode = response.status_code
            except Exception:
                errorcode = "no_respose"

            if errorcode == 200:
                errorcode = "cannot_connect"

            _LOGGER.warning(
                "OpenMediaVault %s connection error: %s", self._host, errorcode
            )

            error_code = errorcode
            self.error = error_code
            self._connected = False
            self.disconnect("connect")
            self.lock.release()

        return self._connected

    # ---------------------------
    #   error_to_strings
    # ---------------------------
    def error_to_strings(self, error=""):
        """Translate error output to error string."""
        self.error = "cannot_connect"
        if "Incorrect username or password" in error:
            self.error = "wrong_login"

        if "certificate verify failed" in error:
            self.error = "ssl_verify_failed"

    # ---------------------------
    #   connected
    # ---------------------------
    def connected(self) -> bool:
        """Return connected boolean."""
        return self._connected

    # ---------------------------
    #   query
    # ---------------------------
    def query(
        self,
        service: str,
        method: str,
        params: dict[str, Any] | None = {},
        options: dict[str, Any] | None = {"updatelastaccess": True},
        soft_fail: bool = False,
    ) -> Optional(list):
        """Retrieve data from OMV.

        soft_fail: don't tear down the whole connection (disconnect() /
        self._connected = False, which triggers a 58s reconnect cooldown
        for every other query) over a single failing call. Real-world OMV
        7/8 installs have confirmed cases of specific calls - notably
        Smart.getAttributes for particular disks/controllers - returning a
        500 while the rest of the API remains perfectly healthy; without
        this, one bad disk took every other sensor offline for a minute at
        a time (see upstream issue #149, confirmed root cause + workaround
        "disable S.M.A.R.T." from multiple independent reporters).
        """
        if not self.connection_check():
            return None

        self.lock.acquire()
        error = False
        try:
            _LOGGER.debug(
                "OpenMediaVault %s query: %s, %s, %s, %s",
                self._host,
                service,
                method,
                params,
                options,
            )
            response = self._connection.post(
                self._resource,
                data=json.dumps(
                    {
                        "service": service,
                        "method": method,
                        "params": params,
                        "options": options,
                    }
                ),
                verify=self._ssl_verify,
            )

            if response.status_code == 200:
                data = response.json()
                _LOGGER.debug("OpenMediaVault %s query response: %s", self._host, data)
            else:
                error = True

        except json.decoder.JSONDecodeError as api_error:
            # See the matching branch in connect() - the request succeeded
            # but the body wasn't valid JSON, so log what OMV actually sent
            # back instead of only the generic "unable to fetch data".
            body_preview = (response.text or "")[:500] if response is not None else ""
            _LOGGER.warning(
                "OpenMediaVault %s returned a non-JSON response (HTTP %s): %s | %s",
                self._host,
                getattr(response, "status_code", "unknown"),
                api_error,
                body_preview or "<empty body>",
            )
            self.disconnect("query", api_error)
            self.lock.release()
            return None
        except requests.exceptions.ConnectionError as api_error:
            _LOGGER.warning("OpenMediaVault %s unable to fetch data", self._host)
            self.disconnect("query", api_error)
            self.lock.release()
            return None
        except Exception:
            self.disconnect("query")
            self.lock.release()
            return None

        # Socket errors
        if error:
            try:
                errorcode = response.status_code
            except Exception:
                errorcode = "no_respose"

            if soft_fail:
                _LOGGER.debug(
                    "OpenMediaVault %s unable to fetch data (%s) for %s.%s "
                    "- soft failure, connection kept alive",
                    self._host,
                    errorcode,
                    service,
                    method,
                )
                self.lock.release()
                return None

            _LOGGER.warning(
                "OpenMediaVault %s unable to fetch data (%s)", self._host, errorcode
            )

            error_code = errorcode
            self.error = error_code
            self._connected = False
            self.lock.release()
            return None

        # Api errors
        if data is not None and data["error"] is not None:
            error_message = data["error"]["message"]
            error_code = data["error"]["code"]
            if (
                error_code == 5001
                or error_code == 5002
                or error_message == "Session not authenticated."
                or error_message == "Session expired."
            ):
                _LOGGER.debug("OpenMediaVault %s session expired", self._host)
                self.error = 5001
                if self.connect():
                    return self.query(service, method, params, options)

        self.error = None
        self.lock.release()

        return data["response"]
