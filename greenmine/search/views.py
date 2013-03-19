# -*- coding: utf-8 -*-
from django.core.paginator import Paginator, InvalidPage
from django.conf import settings
from django.http import Http404
from haystack.query import EmptySearchQuerySet

from greenmine.core.decorators import login_required
from greenmine.core.generic import GenericView
from greenmine.scrum.models import Project
from .forms import SearchForm


SEARCH_RESULTS_PER_PAGE = getattr(settings, 'SEARCH_RESULTS_PER_PAGE', 20)


class SearchView(GenericView):
    template_path = 'search-results.html'

    @login_required
    def get(self, request):
        query = ''
        results = EmptySearchQuerySet()

        if request.user.is_staff:
            projects = Project.objects.all()
        else:
            projects = request.user.projects.all() | \
                request.user.projects_participant.all()

        projects = projects.order_by('name').distinct()

        if request.GET.get('q'):
            form = SearchForm(request.GET)

            if form.is_valid():
                query = form.cleaned_data['q']
                results = form.search().filter(project__in=projects)
        else:
            form = SearchForm()

        paginator = Paginator(results, SEARCH_RESULTS_PER_PAGE)

        try:
            page = paginator.page(int(request.GET.get('page', 1)))
        except InvalidPage:
            raise Http404(_(u'No such page of results!'))

        context = {
            'form': form,
            'page': page,
            'paginator': paginator,
            'query': query,
        }

        return self.render_to_response(self.template_path, context)

