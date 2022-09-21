#  Copyright (c) 2022.

from setuptools import setup, find_packages

README = open('README.md', 'r').read()

setup(
    name='aqui_brain_dump',
    version='1.0.2',
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
        'markupsafe==2.0.1',
        'Jinja2==2.11.3',
        'Markdown==3.3.4',
        'markdown-checklist==0.4.3',
        'pyembed-markdown==1.1.0',
        'python-frontmatter==1.0.0',
        'beautifulsoup4==4.9.3',
    ]
)
