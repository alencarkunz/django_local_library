import datetime

from django.contrib.auth.decorators import permission_required
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
# para CRUD
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from catalog.models import Book, Author, BookInstance, Genre
from catalog.forms import RenewBookForm


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    
    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    # The 'all()' is implied by default.
    num_authors = Author.objects.count()

    # exact > SEM  %% - like ''
    # contains > COM %% - like '%%'
    # exact e contains SÃO case sensitive
    # iexact e icontains NÃO SÃO case sensitive

    #gêneros e livros - case insensitive
    inum_genre = Genre.objects.filter(name__iexact='poesia').count()
    inum_books = Book.objects.filter(title__icontains='a').count()
    
    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'head_title' : 'Local Library',
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'inum_genre' : inum_genre,
        'inum_books' : inum_books,
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)


# Book
class BookListView(generic.ListView):
    model = Book
    paginate_by = 10 #10

    def get_queryset(self):
        #return Book.objects.filter(title__icontains='war')[:5] # Get 5 books containing the title war
        #return Book.objects.all()[:5] # Get 5 books 
        return Book.objects.all() #tem paginação

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(BookListView, self).get_context_data(**kwargs)
        # Create any data and add it to the context
        context['some_data'] = 'This is just some data'
        return context

class BookDetailView(generic.DetailView):
    model = Book

class BookCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'catalog.add_book'
    model = Book
    fields = '__all__'
    initial = {'language': '1'} #Português
    
class BookUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'catalog.change_book'
    model = Book
    fields = '__all__'
    #fields = ['title','author','summary']
    success_url = reverse_lazy('books')

class BookDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'catalog.change_book'
    model = Book
    success_url = reverse_lazy('books')


class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')

class BorrowsBooksByUserListView(PermissionRequiredMixin,generic.ListView): # PermissionRequiredMixin usando quando é uma classe e também permission_required
    permission_required = 'catalog.can_mark_returned'

    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed.html'
    paginate_by = 10
    
    def get_queryset(self):
        # exclude(borrower__isnull=True) = is not null
        return BookInstance.objects.exclude(borrower__isnull=True).filter(status__exact='o').order_by('due_back') 


@permission_required('catalog.can_mark_returned') #usando quando é uma função em vez de classe
def renew_book_librarian(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-borrowed') )

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)

# Author
class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10

    def get_queryset(self):
        #return Author.objects.all()[:5] # Get 5 books porque tem paginação
        return Author.objects.all()

    def get_context_data(self, **kwargs):
        context = super(AuthorListView, self).get_context_data(**kwargs)
        # Create any data and add it to the context
        context['some_data'] = 'This is just some data'
        return context

class AuthorDetailView(PermissionRequiredMixin, generic.DetailView):
    permission_required = 'catalog.view_author' 
    model = Author

class AuthorCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'catalog.add_author' # add_author padrão sistema
    model = Author
    fields = '__all__'
    initial = {'date_of_death': '05/01/2018'}
    #Você pode mudar o sufixo para algo diferente de _form usando o campo template_name_suffix em sua view
    #template_name_suffix = '_other_suffix' 

class AuthorUpdate(PermissionRequiredMixin, UpdateView): #PermissionRequiredMixin,
    permission_required = 'catalog.change_author' # change_author padrão sistema
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    success_url = reverse_lazy('authors')

class AuthorDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'catalog.delete_author' # change_author padrão sistema 
    model = Author
    success_url = reverse_lazy('authors')