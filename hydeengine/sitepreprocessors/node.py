from django.conf import settings
import sys

"""
Preprocessor providing nodes management:
    - `NodeInjector` provides injection abilities (e.g. reference to node A
       from node B as alias C)
"""

class NodeInjector(object):
    """
        Finds the node that represents the given path and injects it with the given     
        variable name into all the posts contained in the current node.
    """
    @staticmethod
    def process(folder, params):
        context = settings.CONTEXT
        site = context['site']
        node = params['node']

        try:
            varName = params['variable']
            path = params['path']
            params['injections'] = { varName: path }
        except KeyError:
            pass
        for varName, path in params['injections'].iteritems():
            if sys.platform == "win32":
                path = path.replace("/", "\\")
            nodeFromPathFragment = site.find_node(site.folder.parent.child_folder(path))
            if not nodeFromPathFragment:
                continue
            for post in node.walk_pages():
                setattr(post, varName, nodeFromPathFragment)
