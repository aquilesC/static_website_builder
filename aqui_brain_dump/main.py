from jinja2 import Template
import markdown
import os


dir = os.path.abspath(os.path.join('..', 'content'))
out_dir = os.path.abspath(os.path.join('..', 'output'))
template_dir = os.path.abspath(os.path.join('..', 'templates'))

if not os.path.isdir(out_dir):
    os.makedirs(out_dir)

with open(os.path.join(template_dir, 'base.html'), 'r') as f:
    template = Template(f.read())

f_walk = os.walk(dir)
for dirs in f_walk:
    cur_dir = dirs[0]
    print(cur_dir)
    for file in dirs[2]:
        print(file)
        with open(os.path.join(cur_dir, file), 'r') as f:
            filename = ''.join(file.split('.')[:-1])
            html = markdown.markdown(f.read(), extensions=['wikilinks', ])
            with open(os.path.join(out_dir, filename+'.html'), 'w') as out_file:
                out_file.write(template.render(content=html))