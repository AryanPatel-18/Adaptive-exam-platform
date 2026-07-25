from django.contrib import admin
from .models import (
    ProcessingJob,
    Topic,
    TopicFile,
    Question,
    QuestionOption,
    QuestionTopic,
)

admin.site.register(ProcessingJob)
admin.site.register(Topic)
admin.site.register(TopicFile)
admin.site.register(Question)
admin.site.register(QuestionOption)
admin.site.register(QuestionTopic)
