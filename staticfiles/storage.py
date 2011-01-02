import warning

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ImproperlyConfigured

from staticfiles import utils
from staticfiles.settings import URL as STATIC_URL, ROOT as STATIC_ROOT, PREPEND_LABEL_APPS

class StaticFilesStorage(FileSystemStorage):
    """
    Standard file system storage for site media files.
    
    The defaults for ``location`` and ``base_url`` are
    ``STATIC_ROOT`` and ``STATIC_URL``.
    """
    def __init__(self, location=None, base_url=None, *args, **kwargs):
        if location is None:
            location = STATIC_ROOT
        if base_url is None:
            base_url = STATIC_URL
        if not location:
            raise ImproperlyConfigured("You're using the staticfiles app "
                "without having set the STATIC_ROOT setting. Set it to "
                "the absolute path of the directory that holds static media.")
        # check for None since we might use a root URL (``/``)
        if base_url is None:
            raise ImproperlyConfigured("You're using the staticfiles app "
                "without having set the STATIC_URL setting. Set it to "
                "URL that handles the files served from STATIC_ROOT.")
        if settings.DEBUG:
            utils.check_settings()
        super(StaticFilesStorage, self).__init__(location, base_url,
                                                 *args, **kwargs)

class StaticFileStorage(StaticFilesStorage):

    def __init__(self, *args, **kwargs):
        warning.warn(
            "The storage backend 'staticfiles.storage.StaticFileStorage' "
            "was renamed to 'staticfiles.storage.StaticFilesStorage'.",
            PendingDeprecationWarning)
        super(StaticFileStorage, self).__init__(*args, **kwargs)


class AppStaticStorage(FileSystemStorage):
    """
    A file system storage backend that takes an app module and works
    for the ``static`` directory of it.
    """
    source_dir = 'static'

    def __init__(self, app, *args, **kwargs):
        """
        Returns a static file storage if available in the given app.
        """
        # app is actually the models module of the app. Remove the '.models'.
        bits = app.__name__.split('.')[:-1]
        self.app_name = bits[-1]
        self.app_module = '.'.join(bits)
        # The models module (app) may be a package in which case
        # dirname(app.__file__) would be wrong. Import the actual app
        # as opposed to the models module.
        app = import_module(self.app_module)
        location = self.get_location(os.path.dirname(app.__file__))
        super(AppStaticStorage, self).__init__(location, *args, **kwargs)

    def get_location(self, app_root):
        """
        Given the app root, return the location of the static files of an app,
        by default 'static'. We special case the admin app here since it has
        its static files in 'media'.
        """
        if self.app_module == 'django.contrib.admin':
            return os.path.join(app_root, 'media')
        return os.path.join(app_root, self.source_dir)

    def get_prefix(self):
        """
        Return the path name that should be prepended to files for this app.
        """
        if self.app_module in PREPEND_LABEL_APPS:
            return app_name
        return None

    def get_files(self, ignore_patterns=[]):
        """
        Return a list containing the relative source paths for all files that
        should be copied for an app.
        """
        files = []
        prefix = self.get_prefix()
        for path in utils.get_files(self, ignore_patterns):
            if prefix:
                path = '/'.join([prefix, path])
            files.append(path)
        return files
