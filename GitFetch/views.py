from django.shortcuts import render
from .services import GitFServices
# Create your views here.
def repo_list(request):
    repositories = GitFServices.get_all_repos()
    context={
        'repositories':repositories
    }
    return render(request,'gitfetch/repo_list.html',context)

def repo_detail(request,repo_id):
    repo = GitFServices.get_repo_id(repo_id)
    commits = GitFServices.get_sorted_commits(repo)
    context  ={
        'repo': repo,
        'commits': commits
    }
    return render(request, 'gitfetch/repo_detail.html', context)
