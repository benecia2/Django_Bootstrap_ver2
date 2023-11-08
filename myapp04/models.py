from django.db import models
from datetime import datetime
from django.contrib.auth.models import User

# Create your models here.

class Board(models.Model):
    writer = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(null=False, max_length=200)
    content = models.TextField(null=False)
    hit = models.IntegerField(default=0)
    post_date = models.DateTimeField(default=datetime.now, blank=True)
    filename = models.CharField(null=True, blank=True, default='', max_length=50)
    filesize = models.IntegerField(default=0)
    down = models.IntegerField(default=-0)

    # 조회수
    def hit_up(self):
        self.hit += 1
    
    # 다운로드 횟수
    def down_up(self):
        # self.down += 1
        self.down = int(self.down)+1


# 댓글
class Comment(models.Model):
    board = models.ForeignKey(Board,on_delete=models.CASCADE)
    writer = models.CharField(null=False, max_length=50)
    content = models.TextField(null=False)
    post_date = models.DateTimeField(default=datetime.now, blank=True)


class Movie(models.Model):
    title = models.CharField(null=False, max_length=500)
    point = models.FloatField(default=0.0)
    reserve = models.FloatField(null=False, default=0.0)


class Forecast(models.Model):
    city = models.CharField(null=False, max_length=200)
    tmef = models.TextField(null=True)
    wf = models.TextField(null=True)
    tmn = models.IntegerField(default=0)
    tmx = models.IntegerField(default=0)