from django.http import Http404
from django.http import HttpResponse, HttpResponseRedirect 
from django.shortcuts import get_object_or_404,render
from .models import Choice,Question
from django.urls import reverse
from django.db.models import F
from django.template import loader
from django.views import generic
import datetime
from django.utils import timezone
# Create your views here.

class IndexView(generic.ListView):
    template_name  = "polls/index.html"
    context_object_name  = "latest_question_list"

    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[
        :5
    ]

class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"
    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        # request.POST['choice'] grabs the 'value' attribute from the checked radio input
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form with an error state context variable.
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        # Use F() expressions to prevent database race conditions at the SQL execution layer
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        
        # Safe POST redirect to guarantee idempotency if a user reloads their client browser
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))
