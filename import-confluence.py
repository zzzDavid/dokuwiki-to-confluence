import sys
import ssl
import os
from os.path import dirname, isdir, join
import re
import mimetypes
from xmlrpc.client import ServerProxy, Fault, Binary
from getpass import getpass
from atlassian import Confluence

# doku wiki parser
from doku import doku_to_confluence

# settings
from setting import doku_data_path, space, parent_page

# Prepare SSL Context
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
# Disable SSL certificate checking
context.verify_mode = ssl.CERT_NONE
context.check_hostname = False

# Connects to confluence server with username and password
site_URL = "https://justforfun25.atlassian.net"
user, pw = "nikita.u.lazarev@gmail.com", "Q5O5NE8MxgDKRrrdJNut5E68"
confluence = Confluence(url=site_URL, username=user, password=pw, cloud=True)
space = "Fun"

# server = ServerProxy(site_URL + "/rpc/xmlrpc", context=context)

username = "nikita.u.lazarev@gmail.com"
if len(sys.argv) > 1 and sys.argv[1] == '-p':
    pwd = getpass("Enter password: ")
else:
	pwd = "qwertyqwerty12"

# token = server.confluence2.login(username, pwd)

class Tree:
    def __init__(s):
        s.previous_depth = 0
        s.page_to_id = {}

    def add_page(s, project_dir, filename, result):
        absolute_filename = join(project_dir, filename)
        s.page_to_id[absolute_filename] = result['id']

    def get_parent(s, project_dir, absolute_filename):
        if project_dir == top_page:
            return parent_page
        else:
            return s.page_to_id[dirname(absolute_filename)]

def save_attachments(space, curpage, attachment):
    for filename in attachment:
#        try:
#            with open(join(doku_data_path, 'media', filename), 'rb') as f:
#                data = f.read(); # slurp all the data
#        except:
#            continue
        attach = {};
        attach['fileName'] = os.path.basename(filename);
        contentType = mimetypes.guess_type(filename)[0]
        if contentType:
            attach['contentType'] = contentType;
        else:
            attach['contentType'] = 'application/octet-stream';
        print (filename + " p=" + curpage['id'])
        try:
            # server.confluence2.addAttachment(token, curpage['id'], attach, Binary(data));
            confluence.attach_file(filename=filename, name=None, content_type = attach['contentType'], page_id=curpage['id'], space=space)
        except:
            # I have no idea which exception this thing throws, so all of them.
            print ("ERROR: Can not upload file '{0}' for the page '{1}' in space {2}".format(join(filename , attachment), curpage['title'], space))

def save(project_dir, filename, pagename, is_directory, tree):
    # Retrives text from a file and converts it
    if is_directory:
        content = ""
        attachment = []
    else:
        output = doku_to_confluence(join(project_dir, filename))
        content = output[0]
        attachment = output[1]

    debug_file = join ('confluence', filename.split('/')[-1])
    with open (debug_file, 'w') as f:
        f.write(content)
    # Create empty page with content
    # content = server.confluence2.convertWikiToStorageFormat(token, content)
    content = confluence.convert_wiki_to_storage(content)
    parent_id = tree.get_parent (project_dir, join(project_dir, filename))
    newpage = { 'content' : content,
                'parentId' : parent_id,
                'space' : space,
                'title' : pagename}
    # server.confluence2.storePage(token, newpage)
    confluence.update_or_create_page(
        parent_id=parent_id,
        title=pagename,
        body=content,
        representation='storage'
    )
    # Push attachments to the page
    # result = server.confluence2.getPage(token,space,pagename)
    result = confluence.get_page_by_title(space, pagename)
    save_attachments(space, result, attachment)
    return result

def add_page (project_dir, filename, is_directory = False):
    pagename = filename.strip()
    if filename[-4:] == '.txt':
        pagename = filename[:-4]
        pagename = pagename.replace('_',' ').strip()
    try:
        # result = server.confluence2.getPage(token, space, pagename)
        result = confluence.get_page_by_title(space, pagename)
    except Fault:
        print ("Saving page %s" % pagename)
        result = save(project_dir , filename, pagename, is_directory, tree)
    else:
        print ("Page %s exists" % pagename)
    tree.add_page (project_dir, filename, result)

tree = Tree()
top_page = join(doku_data_path, 'pages')
for project_dir, subdirs, files in os.walk(top_page):
    for directory in subdirs:
        add_page(project_dir, directory, True)
    for filename in files:
        add_page(project_dir, filename, False)

# server.confluence2.logout(token)
