import re
from validators.url import url as isNormalURL


class Validation:
    @staticmethod
    def isValidUrl(url: str) -> bool:
        # adapted from the following sources:
        # https://www.geeksforgeeks.org/check-if-an-url-is-valid-or-not-using-regular-expression/
        # https://www.regextester.com/111391
        # https://github.com/python-validators/validators/blob/master/src/validators/url.py

        if not url:
            return False

        pattern = re.compile(
            "^https?:\/\/localhost(:[0-9]+)?(\/.*)?$"
        )  # patter for http[s]://localhost:PORT/PATH
        try:
            if re.search(pattern, url) or isNormalURL(url):
                return True
        except:
            pass  # isNormalURL throws an error if not True.

        return False
