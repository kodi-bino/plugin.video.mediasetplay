from urllib import urlencode

class utils():

    def get_url(self,_url, **kwargs):
        """
        Create a URL for calling the plugin recursively from the given set of keyword arguments.
        :param kwargs: "argument=value" pairs
        :type kwargs: dict
        :return: plugin call URL
        :rtype: str
        """
        return '{0}?{1}'.format(_url, urlencode(kwargs))