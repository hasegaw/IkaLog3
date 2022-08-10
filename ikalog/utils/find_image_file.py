import os
import logging

from ikalog.utils.ikautils import IkaUtils
from ikalog.utils.localization import Localization


logger = logging.getLogger()

def find_image_file(img_file=None, languages=None):
    if languages is None:
        languages = Localization.get_game_languages()

    if languages is not None:
        if not isinstance(languages, list):
            languages = [lang]

        for lang in languages:
            f = IkaUtils.get_path('masks', lang, img_file)
            if os.path.exists(f):
                return f

    f = IkaUtils.get_path('masks', img_file)
    if os.path.exists(f):
        return f

    f = IkaUtils.get_path(img_file)
    if os.path.exists(f):
        return f

    f = IkaUtils.get_path('masks', 'ja', img_file)
    if os.path.exists(f):
        logger.info(f'mask {img_file}: using ja version')
        return f

    raise FileNotFoundError('Could not find image file %s (lang %s)' % (img_file, lang))

