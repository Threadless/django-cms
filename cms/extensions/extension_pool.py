from cms.exceptions import SubClassNeededError
from cms.models import Title

from .models import PageExtension, TitleExtension


class ExtensionPool(object):
    def __init__(self):
        self.page_extensions = set()
        self.title_extensions = set()
        self.signaling_activated = False

    def register(self, extension):
        """
        Registers the given extension.
        """

        if issubclass(extension, PageExtension):
            self.page_extensions.add(extension)
        elif issubclass(extension, TitleExtension):
            self.title_extensions.add(extension)
        else:
            raise SubClassNeededError(
                'Extension has to subclass either %r or %r. %r does not!' % (PageExtension, TitleExtension, extension)
            )
        self._activate_signaling()

    def unregister(self, extension):
        try:
            if issubclass(extension, PageExtension):
                self.page_extensions.remove(extension)
            elif issubclass(extension, TitleExtension):
                self.title_extensions.remove(extension)
        except KeyError:
            pass

    def _activate_signaling(self):
        """
        Activates the post_publish signal receiver if not already done.
        """

        if not self.signaling_activated:
            from cms.signals import post_publish
            post_publish.connect(self._receiver)
            self.signaling_activated = True

    def _receiver(self, sender, **kwargs):
        """
        Receiver for the post_publish signal. Gets the published page from kwargs.
        """

        # instance from kwargs is the draft page
        draft_page = kwargs.get('instance')
        # get the new public page from the draft page
        public_page = draft_page.publisher_public

        if self.page_extensions:
            self._copy_page_extensions(draft_page, public_page)
            self._remove_orphaned_page_extensions()
        if self.title_extensions:
            self._copy_title_extensions(draft_page, public_page)
            self._remove_orphaned_title_extensions()

    def _copy_page_extensions(self, draft_page, public_page):
        for extension in self.page_extensions:
            for instance in extension.objects.filter(extended_object=draft_page):
                instance.copy_to_public(public_page)

    def _copy_title_extensions(self, draft_page, public_page):
        for draft_title in draft_page.title_set.all():
            public_title = Title.objects.get(language=draft_title.language, page=public_page)
            for extension in self.title_extensions:
                for instance in extension.objects.filter(extended_object=draft_title):
                    instance.copy_to_public(public_title)

    def _remove_orphaned_page_extensions(self):
        for extension in self.page_extensions:
            extension.objects.filter(
                extended_object__publisher_is_draft=False,
                draft_extension=None
            ).delete()

    def _remove_orphaned_title_extensions(self):
        for extension in self.page_extensions:
            extension.objects.filter(
                extended_object__page__publisher_is_draft=False,
                draft_extension=None
            ).delete()


extension_pool = ExtensionPool()

