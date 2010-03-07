from __future__ import with_statement
import sys
import os
import codecs
import urllib
import operator
from hydeengine.siteinfo import ContentNode
from hydeengine.templatetags.hydetags import RenderExcerptNode
from django.conf import settings
from django.template.loader import render_to_string
from hydeengine.file_system import Folder
from siteinfo import SiteNode

"""
    PRE PROCESSORS
    
    Can be launched before the parsing of each templates and
    after the loading of site info.
"""

class Category:
    def __init__(self, name=""):
        self.posts = []
        self.feed_url = None
        self.archive_url = None
        self.name = name

    @property
    def name(self):
        return self.name
    
    @property
    def posts(self):
        return self.posts

    @property
    def feed_url(self):
        return self.feed_url

    @property
    def archive_url(self):
        return self.archive_url

    

class CategoriesManager:   
    """
    Fetch the category(ies) from every post under the given node
    and creates a reference on them in the node.
    """
    @staticmethod
    def process(folder, params):
        context = settings.CONTEXT
        site = context['site']    
        node = params['node']
        categories = {}
        for post in node.walk_pages():
            if hasattr(post, 'categories') and post.categories != None:
                for category in post.categories:
                    if categories.has_key(category) is False:
                        categories[category] = Category(category)
                    categories[category].posts.append(post)  
                    categories[category].posts.sort(key=operator.attrgetter("created"), reverse=True)
        l = []
        for category in categories.values():
            l.append({"name": category.name,
                      "posts": category.posts,
                      "feed_url": category.feed_url,
                      "post_count": len(category.posts)})
        node.categories = l

class CategoriesArchiveGenerator:
    @staticmethod
    def process(folder, params):
        node = params['node']
        if hasattr(node, 'categories'):
            categories = node.categories
        else:
            raise ValueError("No categories member on node %s" % (node))

        #: defining the output folder - customisable
        relative_folder = output_folder = 'archives'
        if 'output_folder' in params and params['output_folder'] is not None \
                and len(params['output_folder']) > 0:
            relative_folder = output_folder = params['output_folder']
        output_folder = os.path.join(settings.TMP_DIR, folder.name, output_folder)
        if not os.path.isdir(output_folder):
            os.makedirs(output_folder)

        #: fetching default archive template
        template = None
        if 'template' in params:
            template = os.path.join(settings.LAYOUT_DIR, params['template'])
        else:
            raise ValueError("No template reference in CategoriesArchiveGenerator's settings")

        for category in categories:
            archive_resource = "%s.html" % urllib.quote_plus(category["name"])
            category["archive_url"] = "/%s/%s" % (folder.name, "%s/%s" % (relative_folder, archive_resource))
            
        node.categories = categories

        for category in categories:
            name = urllib.quote_plus(category["name"])
            posts = category["posts"]
            archive_resource = "%s.html" % (name)
            settings.CONTEXT.update({'category':category["name"], 
                                                 'posts': posts,
                                                 'categories': categories})
            output = render_to_string(template, settings.CONTEXT)
            with codecs.open(os.path.join(output_folder, \
                                 archive_resource), \
                                 "w", "utf-8") as file:
                file.write(output)
        
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
            nodeFromPathFragment = site.find_node(site.folder.parent.child_folder(path))
            if not nodeFromPathFragment:
                continue
            for post in node.walk_pages():
                setattr(post, varName, nodeFromPathFragment)

class ExcerptSetter(object):
    import re
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
