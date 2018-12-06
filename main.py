# -*- coding: utf-8 -*-

import sys

import xbmcaddon
import xbmcplugin
import xbmcgui
import xbmc
import json

from resources.lib.mediaset import mediaset
from resources.lib.utils import utils
from urllib import urlencode
from urlparse import parse_qsl

addon       = xbmcaddon.Addon()
addonname   = addon.getAddonInfo('name')
utils       = utils()
mediaset    = mediaset()

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

mediaset.getApiData()

def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.
    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))
 
def router(paramstring):
    xbmc.log(paramstring,2)
    """
    Router function that calls other functions
    depending on the provided paramstring
    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'list':
            # Display a list of elements
            if params['type'] == 'live':
                mediaset.displayLiveChannelsList(_handle, _url)
            if params['type'] == 'ondemand':       
                if 'brandId' in params:
                    if 'subBrandId' in params:
                        mediaset.getOnDemandProgramDetailsCategory(_handle, _url, params['brandId'], params['subBrandId'])
                    else:
                        mediaset.getOnDemandProgramDetails(_handle, _url, params['brandId'])
                else:
                    if 'category' in params:
                        if 'startswith' in params:
                            mediaset.listOnDemandCatalogue(_handle, _url, params['category'], params['startswith'])
                        else:
                            mediaset.listOnDemandCategories(_handle, _url, params['category'])
                    else:
                        mediaset.listOnDemandCategories(_handle, _url)
                
        elif params['action'] == 'play':
            item = xbmcgui.ListItem(path = params['url'])
            xbmcplugin.setResolvedUrl(_handle, True, item)
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        if 1:
            # If the plugin is called from Kodi UI without any parameters,
            # display the list of video categories
            xbmcplugin.setPluginCategory(_handle, 'Menu')
            
            menu = mediaset.getMainMenu()
            
            for m in menu:
                list_item = xbmcgui.ListItem(label=m['label'])
                is_folder = True
                url = get_url(action=m['url']['action'], type=m['url']['type'])
                xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
                
            # Finish creating a virtual folder.
            xbmcplugin.endOfDirectory(_handle)
        
    

if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
    

