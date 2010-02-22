#!/usr/bin/env python

import MySQLdb
import html2text
import codecs
import os.path
import time

class WpImporter:
    def __init__(self, host, user, pwd, dbname):
        query = "select post_title, post_name, post_date, post_content, post_excerpt from wp_posts where post_status = 'publish' and post_type = 'post'"
        connection = None
        cursor = None
        try:
            connection = MySQLdb.connect(host, user, pwd, dbname, charset="utf8")
            cursor = connection.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            for r in results:
                self.export(r)
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()

    def export(self, post):
        title, slug, post_date, content, excerpt = post
        md = html2text.html2text(content)
        output = "{% extends '_post.html' %}\n"
        output = output + "{%hyde\ntitle: \""+title.replace("\"","\\\"")+"\"\ncreated: "+str(post_date.date())+"%}\n"
        output = output + "{% block article %}\n{% article %}\n"+md+"\n{% endarticle %}\n{% endblock %}"
        
        try:
            path = "posts/%s.html" % (slug)
            file = codecs.open(path, "w", 'utf-8')
            file.write(output)
            file.flush()
        finally:
            file.close()
        os.utime(path, (time.mktime(post_date.timetuple()),time.mktime(post_date.timetuple())))
