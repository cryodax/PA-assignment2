# Create your views here.
from .models import Book, Author, BookInstance
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import LoanBookForm
import datetime


def index(request):
    """View function for home page of site."""
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    # The 'all()' is implied by default.
    num_authors = Author.objects.count()

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits,
    }
    # Render the HTML template index.html with the data in the context variable
    return render(request, 'catalog/index.html', context=context)

class BookListView(LoginRequiredMixin, generic.ListView):
    model = Book

class BookDetailView(LoginRequiredMixin, generic.DetailView):
    model = Book

class AuthorListView(LoginRequiredMixin, generic.ListView):
    model = Author

class AuthorDetailView(LoginRequiredMixin, generic.DetailView):
    model = Author

class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name = 'catalog/my_books.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter\
        (borrower=self.request.user).filter(status__exact='o').order_by('due_back')

class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class BookCreate(SuperuserRequiredMixin, CreateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'book_image']
    success_url = reverse_lazy('book_list')


class BookUpdate(SuperuserRequiredMixin, UpdateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'book_image']
    success_url = reverse_lazy('book_list')


class BookDelete(SuperuserRequiredMixin, DeleteView):
    model = Book
    template_name = 'catalog/book_delete.html'
    success_url = reverse_lazy('book_list')

class AuthorCreate(CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death', 'author_image']

    def form_valid(self, form):
        post = form.save(commit=False)
        post.save()
        return HttpResponseRedirect(reverse('author_list'))


class AuthorUpdate(UpdateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death', 'author_image']

    def form_valid(self, form):
        post = form.save(commit=False)
        post.save()
        return HttpResponseRedirect(reverse('author_list'))


def author_delete(request, pk):
    author = get_object_or_404(Author, pk=pk)
    try:
        author.delete()
        messages.success(request, (author.first_name + ' ' + author.last_name +" has been deleted"))
    except:
        messages.success(request, (author.first_name + ' ' + author.last_name + ' cannot be deleted. Books exist for this author'))
        return redirect('author_list')


class AvailBooksListView(SuperuserRequiredMixin, generic.ListView):
    """Generic class-based view listing all books on loan. """
    model = BookInstance
    template_name = 'catalog/bookinstance_list_available.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='a').order_by('book__title')


@user_passes_test(lambda user: user.is_superuser)
def loan_book_librarian(request, pk):
    """Loan an available book instance to a library member."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == 'POST':
        form = LoanBookForm(request.POST, instance=book_instance)
        if form.is_valid():
            book_instance = form.save()
            book_instance.due_back = datetime.date.today() + datetime.timedelta(weeks=4)
            book_instance.status = 'o'
            book_instance.save()
            return HttpResponseRedirect(reverse('all_available'))
    else:
        form = LoanBookForm(
            instance=book_instance,
            initial={'book_title': book_instance.book.title},
        )

    return render(request, 'catalog/loan_book_librarian.html', {'form': form})

