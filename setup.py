#  Copyright (c) 2024.

from setuptools import setup, find_packages

README = open('README.md', 'r').read()

setup(
    name='aqui_brain_dump',
    version='1.0.6',
    packages=find_packages(),
    data_files=[('', ['aqui_brain_dump/sitemap.xml', 'aqui_brain_dump/feed.rss'])],
    include_package_data=True,
    # package_dir={'': 'aqui_brain_dump'},
    url='https://github.com/aquilesC/static_website_builder',
    license='BSD',
    author='Aquiles Carattino',
    author_email='aqui.carattino@gmail.com',
    description='Convert a bunch of markdown files to a beautiful website',
    long_description=README,
    long_description_content_type='text/markdown',
    entry_points={
        'console_scripts': [
            'brain_dump=aqui_brain_dump.__main__:main'
        ]
    },
    install_requires=[
        'beautifulsoup4==4.11.1',
        'Jinja2==3.1.4',
        'Markdown==3.7',
        'markdown-checklist==0.4.4',
        'MarkupSafe==2.1.1',
        'md4mathjax==0.1.3',
        'pyembed==1.3.3',
        'pyembed-markdown==1.1.0',
        'python-frontmatter==1.1.0',
        'PyYAML==6.0.2',
        'text-unidecode==1.3',
        'setuptools==75.1.0',
    ]
)
