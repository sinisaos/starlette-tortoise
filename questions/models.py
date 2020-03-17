from tortoise.models import Model
from tortoise import fields


class Question(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255)
    slug = fields.CharField(max_length=255)
    content = fields.TextField()
    created = fields.DatetimeField(auto_now_add=True)
    view = fields.IntField(default=0)
    question_like = fields.IntField(default=0)
    accepted_answer = fields.BooleanField(default=False)
    tags = fields.ManyToManyField(
        'models.Tag', related_name='tags', through='question_tag')
    user = fields.ForeignKeyField(
        'models.User', related_name='user', on_delete=fields.CASCADE)

    def __str__(self):
        return self.title


class Answer(Model):
    id = fields.IntField(pk=True)
    content = fields.TextField()
    created = fields.DatetimeField(auto_now_add=True)
    answer_like = fields.IntField(default=0)
    is_accepted_answer = fields.BooleanField(default=False)
    ans_user = fields.ForeignKeyField(
        'models.User', related_name='ans_user', on_delete=fields.CASCADE)
    question = fields.ForeignKeyField(
        'models.Question', related_name='question', on_delete=fields.CASCADE)


class Tag(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)

    def __str__(self):
        return self.name
