import json
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from .models import Repository,Commit

class GitFServices:
    @staticmethod
    def get_all_repos():
        return Repository.objects.all()
    
    @staticmethod
    def get_repo_id(repo_id):
        return get_object_or_404(Repository,pk=repo_id)

    @staticmethod
    def get_sorted_commits(repo):
        return repo.commits.all().order_by('-timestamp')
    
    @staticmethod
    def process_webhook(json_File):
        try:
            payload = json.loads(json_File)
        except(json.JSONDecodeError,TypeError):
            return False
        repo_data = payload.get('repository', {})
        repo_name = repo_data.get('name')
        repo_desc = repo_data.get('description') or ''
        if not repo_name:
            return False
        
        repo,created= Repository.objects.get_or_create(
            name = repo_name,
            defaults={'description':repo_desc},
        )
        commit_list = payload.get('commits',[])

        for commit_data in commit_list:
            hash_string = commit_data.get('id')
            author_dict = commit_data.get('author', {})
            author_name = author_dict.get('name', 'Unknown Author')
            commit_msg = commit_data.get('message')
            time_string = commit_data.get('timestamp')
            modified_files = commit_data.get('modified', [])
            added_files = commit_data.get('added', [])
            all_files = modified_files + added_files
            joined_files = ", ".join(all_files)


            if not all([hash_string, author_name, commit_msg, time_string]):
                continue
            parsed_time = parse_datetime(time_string)

            if not parsed_time:
                continue

            if Commit.objects.filter(commit_hash = hash_string).exists():
                continue
            
            Commit.objects.create(
                repository = repo,
                commit_hash = hash_string,
                author = author_name,
                message = commit_msg,
                timestamp = parsed_time,
                files_changed = joined_files,
            )
        return True