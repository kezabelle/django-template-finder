import fnmatch
import logging
import os
import re

from django.conf import settings
from django.utils.importlib import import_module
from django.utils.text import capfirst


__all__ = ('find_all_templates', 'template_choices')


LOGGER = logging.getLogger('templatefinder')


def find_all_templates(pattern='*.html'):
    """
    Finds all Django templates matching given glob in all TEMPLATE_LOADERS

    :param str pattern: `glob <http://docs.python.org/2/library/glob.html>`_
                        to match

    .. important:: At the moment egg loader is not supported.
    """
    templates = []

    # See: https://docs.djangoproject.com/en/dev/ref/templates/api/#django.template.loaders.cached.Loader
    template_loaders = list(settings.TEMPLATE_LOADERS)
    if 'django.template.loaders.cached.Loader' in template_loaders:
        cached_loader_index = template_loaders.index('django.template.loaders.cached.Loader')
        extra_loaders = template_loaders[cached_loader_index + 1]
        # both the cached loader and the next element (list of regular loaders)
        del template_loaders[cached_loader_index]
        del template_loaders[cached_loader_index]
        for loader in extra_loaders:
            template_loaders.insert(cached_loader_index, loader)

    for loader_name in template_loaders:
        module, klass = loader_name.rsplit('.', 1)
        if loader_name in (
            'django.template.loaders.app_directories.Loader',
            'django.template.loaders.filesystem.Loader',
        ):
            loader = getattr(import_module(module), klass)()
            for dir in loader.get_template_sources(''):
                for root, dirnames, filenames in os.walk(dir):
                    for basename in filenames:
                        filename = os.path.join(root, basename)
                        rel_filename = filename[len(dir)+1:]
                        if fnmatch.fnmatch(filename, pattern) or \
                           fnmatch.fnmatch(basename, pattern) or \
                           fnmatch.fnmatch(rel_filename, pattern):
                            templates.append(rel_filename)
        else:
            LOGGER.debug('%s is not supported' % loader_name)
    return sorted(set(templates))


to_space_re = re.compile(r'[^a-zA-Z0-9\-]+')


def template_choices(templates, display_names=None):
    """
    Given an iterable of `templates`, calculate human-friendly display names
    for each of them, optionally using the `display_names` provided, or a
    global dictionary (`TEMPLATEFINDER_DISPLAY_NAMES`) stored in the Django
    project's settings.

    .. note:: As the resulting iterable is a lazy generator, if it needs to be
              consumed more than once, it should be turned into a `set`, `tuple`
              or `list`.

    :param list templates: an iterable of template paths, as returned by
                           `find_all_templates`
    :param display_names: If given, should be a dictionary where each key
                          represents a template path in `templates`, and each
                          value is the display text.
    :type display_names: dictionary or None
    :return: an iterable of two-tuples representing value (0) & display text (1)
    :rtype: generator expression
    """
    # allow for global template names, as well as usage-local ones.
    if display_names is None:
        display_names = getattr(settings, 'TEMPLATEFINDER_DISPLAY_NAMES', {})

    def fix_display_title(template_path):
        if template_path in display_names:
            return display_names[template_path]
        # take the last part from the template path; works even if there is no /
        lastpart = template_path.rpartition('/')[-1]
        # take everything to the left of the rightmost . (the file extension)
        lastpart_minus_suffix = lastpart.rpartition('.')[0]
        # convert most non-alphanumeric characters into spaces, with the
        # exception of hyphens.
        lastpart_spaces = to_space_re.sub(' ', lastpart_minus_suffix)
        return capfirst(lastpart_spaces)

    return ((template, fix_display_title(template)) for template in templates)
