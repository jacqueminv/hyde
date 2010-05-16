from django.conf import settings
import re

"""
Default Preprocessors used always by the hyde engine

"""

class ExcerptSetter(object):
    """
    Standard pre-processor initializing whether a post contains an excerpt or not
    """

    regex = re.compile("{%\s*excerpt\s*%}")

    @staticmethod
    def process(folder, params):
        node = params['node']
        if node.type != "content":
            return
        context = settings.CONTEXT
        for post in node.walk_pages():
            content = post.file.read_all()
            if ExcerptSetter.regex.search(content) is not None:
                post.excerpt = True
