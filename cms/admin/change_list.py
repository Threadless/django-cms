from django.contrib.admin.views.main import ChangeList, ALL_VAR, IS_POPUP_VAR,\
    ORDER_TYPE_VAR, ORDER_VAR, SEARCH_VAR
from cms.models import Title, PagePermission, Page
from cms import settings
from cms.utils import get_language_from_request, find_children
from django.contrib.sites.models import Site

SITE_VAR = "sites__id__exact"
COPY_VAR = "copy"

class CMSChangeList(ChangeList):
    real_queryset = False
    
    def __init__(self,  *args, **kwargs):
        super(CMSChangeList, self).__init__(*args, **kwargs)
        request = args[0]
        try:
            self.query_set = self.get_query_set(request)
        except:
            raise
        self.get_results(request)
        
        if SITE_VAR in self.params:
            try:   
                self._current_site = Site.objects.get(pk=self.params[SITE_VAR])
            except:
                self._current_site = Site.objects.get_current()
        else:
            self._current_site = Site.objects.get_current()
        
    def get_query_set(self, request=None):
        if COPY_VAR in self.params:
            del self.params[COPY_VAR] 
        qs = super(CMSChangeList, self).get_query_set()
        if request:
            permissions = Page.permissions.get_change_list_id_list(request.user)
            if permissions != Page.permissions.GRANT_ALL:
                qs = qs.filter(pk__in=permissions)
                self.root_query_set = self.root_query_set.filter(pk__in=permissions)
            self.real_queryset = True
        qs = qs.order_by('tree_id', 'parent', 'lft')
        return qs
    
    def is_filtered(self):
        lookup_params = self.params.copy() # a dictionary of the query string
        for i in (ALL_VAR, ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR, IS_POPUP_VAR, SITE_VAR):
            if i in lookup_params:
                del lookup_params[i]
        if not lookup_params.items() and not self.query:
            return False
        return True
    
    def get_results(self, request):
        if self.real_queryset:
            super(CMSChangeList, self).get_results(request)
            if not self.is_filtered():
                self.full_result_count = self.result_count = self.root_query_set.count()
            else:
                self.full_result_count = self.root_query_set.count()
    
    def set_items(self, request):
        lang = get_language_from_request(request)
        pages = self.get_query_set(request).order_by('tree_id', 'parent', 'lft').select_related()
        
        perm_edit_ids = Page.permissions.get_change_id_list(request.user)
        perm_publish_ids = Page.permissions.get_publish_id_list(request.user)
        perm_softroot_ids = Page.permissions.get_softroot_id_list(request.user)
        perm_change_list_ids = Page.permissions.get_change_list_id_list(request.user)
        
        if perm_edit_ids and perm_edit_ids != Page.permissions.GRANT_ALL:
            #pages = pages.filter(pk__in=perm_edit_ids)
            pages = pages.filter(pk__in=perm_change_list_ids)   
        
        if settings.CMS_MODERATOR:
            # get oll ids of public models, so we can cahce them
            # TODO: add some filtering here, so the set is the same like page set...
            public_page_id_set = Page.PublicModel.objects.all().value_list('id', flat=True)
        
        ids = []
        root_pages = []
        pages = list(pages)
        all_pages = pages[:]
        for page in pages:
            children = []

            # note: We are using change_list permission here, because we must
            # display also pages which user must not edit, but he haves a 
            # permission for adding a child under this page. Otherwise he would
            # not be able to add anything under page which he can't change. 
            if not page.parent_id or (perm_change_list_ids != Page.permissions.GRANT_ALL and not int(page.parent_id) in perm_change_list_ids):
                page.root_node = True
            else:
                page.root_node = False
            ids.append(page.pk)
            
            if settings.CMS_PERMISSION:
                # caching the permissions
                page.permission_edit_cache = perm_edit_ids == Page.permissions.GRANT_ALL or page.pk in perm_edit_ids
                page.permission_publish_cache = perm_publish_ids == Page.permissions.GRANT_ALL or page.pk in perm_publish_ids
                page.permission_softroot_cache = perm_publish_ids == Page.permissions.GRANT_ALL or page.pk in perm_softroot_ids
                page.permission_user_cache = request.user
            
            if settings.CMS_MODERATOR:
                # set public instance existence state
                page.public_published_cache = page.public_id in public_page_id_set
                
                
            if page.root_node or self.is_filtered():
                page.last = True
                if len(children):
                    children[-1].last = False
                root_pages.append(page)
                page.ancestors_ascending = []
                if not self.is_filtered():
                    find_children(page, pages, 1000, 1000, [], -1, soft_roots=False, request=request, no_extended=True, to_levels=1000)
                else:
                    page.childrens = []
        titles = Title.objects.filter(page__in=ids)
        for page in all_pages:# add the title and slugs and some meta data
            page.languages_cache = []
            for title in titles:
                if title.page_id == page.pk:
                    if title.language == lang:
                        page.title_cache = title
                    if not title.language in page.languages_cache:
                        page.languages_cache.append(title.language)
        
        self.root_pages = root_pages
        
    def get_items(self):
        return self.root_pages
    
    def sites(self):
        return Site.objects.all()
    
    def current_site(self):
        return self._current_site
    
