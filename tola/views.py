from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from tola.forms import ProfileUpdateForm, NewUserRegistrationForm, NewTolaUserRegistrationForm, BookmarkForm
from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from workflow.models import ProjectAgreement, ProjectComplete, Program, SiteProfile, Sector,Country, TolaUser,TolaSites, TolaBookmarks, FormGuidance
from indicators.models import CollectedData, Indicator

from django.shortcuts import get_object_or_404
from django.db.models import Sum, Q, Count
from tola.util import getCountry
from django.contrib.auth.models import Group
from indicators.queries import ProgramWithMetrics

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

@login_required(login_url='/accounts/login/')
def index(request, selected_country=None):
    """
    Home page
    """

    # Find the active country
    user = request.user.tola_user
    user_countries = getCountry(request.user) # all countries whose programs are available to the user

    if selected_country: # from URL
        active_country = Country.objects.filter(id=selected_country)[0]
        user.update_active_country(active_country)
    else:
        try:
            # default to first country in user's accessible countries
            active_country = user.active_country if user.active_country else user_countries[0]
        except IndexError:
            # ... or failing that, to their "home" country
            active_country = user.country
            # ... failing all of this, the homepage will be blank. Sorry!

    programs_with_metrics = ProgramWithMetrics.home_page.with_annotations().filter(
        country=active_country,
        funding_status="Funded"
    )
    getSiteProfile = SiteProfile.objects.all()\
        .prefetch_related('country','district','province')\
        .filter(country=active_country)\
        .filter(status=1)
    getSiteProfileIndicator = SiteProfile.objects.all()\
        .prefetch_related('country','district','province')\
        .filter(country=active_country)\
        .filter(status=1)

    return render(request, 'home.html', {
        'user_countries': user_countries,
        'active_country': active_country,
        'programs': programs_with_metrics,
        'no_programs': programs_with_metrics.count(),
        'getSiteProfile': getSiteProfile,
        'getSiteProfileIndicator': getSiteProfileIndicator,
    })


def register(request):
    """
    Register a new User profile using built in Django Users Model
    """
    privacy = TolaSites.objects.get(id=1)
    if request.method == 'POST':
        uf = NewUserRegistrationForm(request.POST)
        tf = NewTolaUserRegistrationForm(request.POST)

        if uf.is_valid() * tf.is_valid():
            user = uf.save()
            user.groups.add(Group.objects.get(name='ViewOnly'))

            tolauser = tf.save(commit=False)
            tolauser.user = user
            tolauser.save()
            messages.error(request, 'Thank you, You have been registered as a new user.', fail_silently=False)
            return HttpResponseRedirect("/")
    else:
        uf = NewUserRegistrationForm()
        tf = NewTolaUserRegistrationForm()

    return render(request, "registration/register.html", {
        'userform': uf,'tolaform': tf, 'helper': NewTolaUserRegistrationForm.helper,'privacy':privacy
    })


def profile(request):
    """
    Update a User profile using built in Django Users Model if the user is logged in
    otherwise redirect them to registration version
    """
    if request.user.is_authenticated():
        obj = get_object_or_404(TolaUser, user=request.user)
        form = ProfileUpdateForm(request.POST or None, instance=obj, user=request.user)

        if request.method == 'POST':
            if form.is_valid():
                form.save()
                messages.error(request, 'Your profile has been updated.', fail_silently=False,
                               extra_tags='success')
                # immediately redirect to user sees language change
                return HttpResponseRedirect(reverse_lazy('profile'))

        return render(request, "registration/profile.html", {
            'form': form, 'helper': ProfileUpdateForm.helper
        })
    else:
        return HttpResponseRedirect(reverse_lazy('register'))


class BookmarkList(ListView):
    """
    Bookmark Report filtered by project
    """
    model = TolaBookmarks
    template_name = 'registration/bookmark_list.html'

    def get(self, request, *args, **kwargs):
        getUser = TolaUser.objects.all().filter(user=request.user)
        getBookmarks = TolaBookmarks.objects.all().filter(user=getUser)

        return render(request, self.template_name, {'getBookmarks':getBookmarks})


class BookmarkCreate(CreateView):
    """
    Using Bookmark Form for new bookmark per user
    """
    model = TolaBookmarks
    template_name = 'registration/bookmark_form.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            self.guidance = FormGuidance.objects.get(form="Bookmarks")
        except FormGuidance.DoesNotExist:
            self.guidance = None
        return super(BookmarkCreate, self).dispatch(request, *args, **kwargs)

    # add the request to the kwargs
    def get_form_kwargs(self):
        kwargs = super(BookmarkCreate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):

        initial = {
            'user': self.request.user,
        }

        return initial

    def form_invalid(self, form):

        messages.error(self.request, 'Invalid Form', fail_silently=False)

        return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Success, Bookmark Created!')
        latest = TolaBookmarks.objects.latest('id')
        redirect_url = '/bookmark_update/' + str(latest.id)
        return HttpResponseRedirect(redirect_url)

    form_class = BookmarkForm


class BookmarkUpdate(UpdateView):
    """
    Bookmark Form Update an existing site profile
    """
    model = TolaBookmarks
    template_name = 'registration/bookmark_form.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            self.guidance = FormGuidance.objects.get(form="Bookmarks")
        except FormGuidance.DoesNotExist:
            self.guidance = None
        return super(BookmarkUpdate, self).dispatch(request, *args, **kwargs)

    def get_initial(self):

        initial = {
            'user': self.request.user,
        }

        return initial

    def form_invalid(self, form):

        messages.error(self.request, 'Invalid Form', fail_silently=False)

        return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Success, Bookmark Updated!')
        latest = TolaBookmarks.objects.latest('id')
        redirect_url = '/bookmark_update/' + str(latest.id)
        return HttpResponseRedirect(redirect_url)

    form_class = BookmarkForm


class BookmarkDelete(DeleteView):
    """
    Bookmark Form Delete an existing bookmark
    """
    model = TolaBookmarks
    template_name = 'registration/bookmark_confirm_delete.html'
    success_url = "/bookmark_list"

    def dispatch(self, request, *args, **kwargs):
        return super(BookmarkDelete, self).dispatch(request, *args, **kwargs)

    def form_invalid(self, form):

        messages.error(self.request, 'Invalid Form', fail_silently=False)

        return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form):

        form.save()

        messages.success(self.request, 'Success, Bookmark Deleted!')
        return self.render_to_response(self.get_context_data(form=form))

    form_class = BookmarkForm


def logout_view(request):
    """
    Logout a user
    """
    logout(request)
    # Redirect to a success page.
    return HttpResponseRedirect("/")

