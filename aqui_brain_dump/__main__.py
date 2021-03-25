import os
import sys
import time
from distutils.dir_util import copy_tree
import logging
from pathlib import Path
from shutil import copyfile

from aqui_brain_dump import base_url, content_path, output_path, static_path, static_url
from aqui_brain_dump.note import Note


logger = logging.getLogger(__name__)


def main():
    logger.info('Starting to compile the notes')
    if len(sys.argv) > 1:
        print(sys.argv)
        base_url = sys.argv[1]

    out_static_dir = output_path / static_url
    copy_tree(str(static_path.absolute()), str(out_static_dir.absolute()))

    f_walk = os.walk(content_path)
    for dirs in f_walk:
        logger.info(f'Entering to {dirs[0]}')
        cur_dir = dirs[0]
        sub_dir = os.path.abspath(cur_dir)
        if sub_dir == '.':
            sub_dir = ''

        if sub_dir.startswith('.'):
            continue

        sub_dir = Path(sub_dir).absolute()
        out_subdir = output_path / sub_dir.relative_to(content_path)
        out_subdir.mkdir(exist_ok=True, parents=True)
        for file in dirs[2]:
            if not file.endswith('.md'):
                logger.debug(f'Copying {file} to {output_path / sub_dir.relative_to(content_path) / file}')
                copyfile(os.path.join(cur_dir, file), output_path / sub_dir.relative_to(content_path) / file)
                continue
            filepath = content_path / sub_dir / file
            logger.debug(f'Creating note for {filepath}')
            Note.create_from_path(filepath)

    logger.info('Waiting for note parser executor to finish')
    while len([f for f in Note.futures_executor if f.running()]):
        time.sleep(.01)

    logger.info('Creating Tags')
    for tag, backlinks in Note.tags_dict.items():
        t = tag.strip('#')
        tag_page = Note.create_from_url(f'/tags/{t}')
        tag_page.backlinks = backlinks

    logger.info('Building backlinks')
    Note.build_backlinks()
    logger.info('Waiting for backlinks executor to finish')

    while len([f for f in Note.futures_executor if f.running()]):
        time.sleep(.01)
    Note.note_executor.shutdown(wait=True)

    logger.info('Rendering notes')
    for rel_path, note in Note.notes.items():
        logger.debug(f'Rendering {note}')
        note.render()

    logger.info('Finished building notes')


if __name__ == '__main__':
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    fh = logging.FileHandler('logger.log', mode='w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    log.addHandler(ch)
    log.addHandler(fh)

    main()