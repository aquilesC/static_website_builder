from distutils.dir_util import copy_tree
from jinja2 import Template
import markdown
import os


dir = os.path.abspath(os.path.join('..', 'content'))
out_dir = os.path.abspath(os.path.join('..', 'output'))
static_dir = os.path.abspath(os.path.join('..', 'static'))
template_dir = os.path.abspath(os.path.join('..', 'templates'))

if not os.path.isdir(out_dir):
    os.makedirs(out_dir)

out_static_dir = os.path.join(out_dir, 'static')
if not os.path.isdir(out_static_dir):
    os.makedirs(out_static_dir)
copy_tree(static_dir, out_static_dir)

with open(os.path.join(template_dir, 'base.html'), 'r') as f:
    template = Template(f.read())


f_walk = os.walk(dir)
for dirs in f_walk:
    cur_dir = dirs[0]
    for file in dirs[2]:
        with open(os.path.join(cur_dir, file), 'r') as f:
            filename = ''.join(file.split('.')[:-1])
            html = markdown.markdown(f.read(), extensions=['wikilinks', ])
            with open(os.path.join(out_dir, filename+'.html'), 'w') as out_file:
                context = {
                    'content': html,
                    'static': 'static',
                }
                out_file.write(template.render(context))