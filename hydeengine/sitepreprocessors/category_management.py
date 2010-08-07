from django.conf import settings
from django.template.loader import render_to_string
from codecs import open as copen
from os import path, makedirs
import operator
import urllib

"""
Preprocessor managing categories. Takes care of mainly two tasks:
    - `CategoriesManager` injects the category listing into a custom `node`
    - `CategoriesArchiveGenerator` creates an archive listing by categories;
       needs the category listing on the node set in `params`, thus
       `CategoriesManager` needs to be set as a SITE_PRE_PROCESSORS before.
"""

class Category:
    """
    Plain object
    """
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

    By default it generates also listing pages displaying every posts belonging
    to each category. You can turn it off by setting `archiving` param to `False`

       `params` : must contain the `template` key which will be used to render
                  the archive page
                  may contain the `output_folder` key to specify the destination
                  folder of the generated listing pages (by default: 'archives')
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

        #archiving section
        archiving = 'archiving' in params.keys() and params['archiving'] is False or True

        if archiving:
            categories = l
            #: defining the output folder - customisable
            if hasattr(settings,"CATEGORY_ARCHIVES_DIR"):
                relative_folder = output_folder = settings.CATEGORY_ARCHIVES_DIR
            else:
                relative_folder = output_folder = 'archives'
            if 'output_folder' in params and params['output_folder'] is not None \
                    and len(params['output_folder']) > 0:
                relative_folder = output_folder = params['output_folder']
            output_folder = path.join(settings.TMP_DIR, folder.name, output_folder)
            if not path.isdir(output_folder):
                makedirs(output_folder)

            #: fetching default archive template
            template = None
            if 'template' in params:
                template = path.join(settings.LAYOUT_DIR, params['template'])
            else:
                raise ValueError("No template reference in CategoriesManager's settings")

            for category in categories:
                archive_resource = "%s.html" % urllib.quote_plus(category["name"])
                category["archive_url"] = "/%s/%s" % (relative_folder,
                                                         archive_resource)

            for category in categories:
                name = urllib.quote_plus(category["name"])
                posts = category["posts"]
                archive_resource = "%s.html" % (name)
                settings.CONTEXT.update({'category':category["name"], 
                                         'posts': posts,
                                         'categories': categories})
                output = render_to_string(template, settings.CONTEXT)
                with copen(path.join(output_folder, \
                                     archive_resource), \
                                     "w", "utf-8") as file:
                    file.write(output)
