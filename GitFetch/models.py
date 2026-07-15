from django.db import models

# Create your models here.
class Repository (models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name_plural = "Repositories"
    def __str__(self):
        return self.name

class Commit(models.Model):
    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
        related_name="commits",
    )
    commit_hash = models.CharField(max_length=40)
    author = models.CharField(max_length=100)
    message = models.CharField()
    timestamp = models.DateTimeField()
    files_changed = models.TextField(blank=True)

    def __str__(self):
        return f"{self.repository.name} - {self.commit_hash[:7]}"

