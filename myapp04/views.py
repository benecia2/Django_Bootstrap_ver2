from django.shortcuts import render, redirect
from myapp04.models import Board, Comment, Movie, Forecast, User
from django.http.response import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .form import UserForm
import math
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
import pandas as pd


import json
from myapp04 import dataProcess
from django.db.models.aggregates import Count, Avg

# Create your views here.

# write_form(추가폼)
@login_required(login_url='/login/')
def write_form(request):
    return render(request, 'board/insert.html')

# 업로드 파일위치
UPLOAD_DIR = "D:/DJANGOWORK/upload/"

# signup : 회원가입
def signup(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request,user)
            return redirect('/')
        else:
            print("signup POST un_valid")
    else:
        form = UserForm()
        
    return render(request, 'common/signup.html',{'form':form})

# insert : 추가하기
@csrf_exempt
def insert(request):
    fname = ''
    fsize = 0
    if 'file' in request.FILES :
        file = request.FILES['file']
        fsize = file.size
        fname = file.name
        fp = open('%s%s' %(UPLOAD_DIR, fname), 'wb')
        for chunk in file.chunks():
            fp.write(chunk)
        fp.close()

    board = Board(writer = request.user,
                    title = request.POST['title'],
                    content = request.POST['content'],
                    filename = fname,
                    filesize = fsize
                    )
    board.save()
    return redirect("/list/")

# list : 전체보기
def list(request):
    page = request.GET.get('page',1)
    word = request.GET.get('word','')

    boardCount = Board.objects.filter(
                                    Q(title__contains = word)|
                                    Q(content__contains = word)).count()
    
    boardList = Board.objects.filter(
                                    Q(title__contains = word)|
                                    Q(content__contains = word)).order_by('-id')

    # 페이징 처리
    pageSize = 5

    paginator = Paginator(boardList,pageSize)
    page_obj = paginator.get_page(page)
    print('page_obj:',page_obj)

    context = {
        'boardCount':boardCount,
        'page_list' :page_obj,
        'word':word
    }

    return render(request, 'board/list.html',context)


# detail 상세보기 : /detail/1" ==> detail/<int:board_id>
def detail(request, board_id):
    # print('board_id : ',board_id)
    board = Board.objects.get(id=board_id)
    # 조회수 1증가
    board.hit_up()
    board.save()
    # comment list
    commentList = Comment.objects.filter(board_id = board_id).order_by('-id')
    commentCnt = Comment.objects.filter(board_id=board_id).count
    print('commentList sql : ', commentList.query)
    return render(request, 'board/detail.html',{'board':board,  'commentList': commentList})


# comment_insert : 댓글 추가하기
@csrf_exempt
def comment_insert(request):
    id = request.POST['id']
    cboard = Comment(board_id = id, writer = '홍길동', content = request.POST['content'])

    cboard.save()

    # return redirect("detail_id?id="+id)
    return redirect("/detail/"+id)

# delete : 삭제
def delete(request,board_id):
    Board.objects.get(id=board_id).delete()
    return redirect("/list/")

# update_form : 수정 폼
def update_form(request, board_id):
    board = Board.objects.get(id=board_id)
    context = {'board':board}
    return render(request, 'board/update.html', context)

# update : 수정하기
@csrf_exempt
def update(request):
    id = request.POST['id']
    board = Board.objects.get(id = id)
    fname = board.filename
    fsize = board.filesize
    


    # file 수정
    if 'file' in request.FILES :
        file = request.FILES['file']
        fsize = file.size
        fname = file.name
        fp = open('%s%s' %(UPLOAD_DIR, fname), 'wb')
        for chunk in file.chunks():
            fp.write(chunk)
        fp.close()

    board_update = Board(id,
                writer = request.user,
                title = request.POST['title'],
                content = request.POST['content'],
                filename = fname,
                filesize = fsize
                )
    board_update.save()
    return redirect("/list")

# download_count
def download_count(request):
    id = request.GET['id']
    print('id : ',id)
    board = Board.objects.get(id = id)
    board.down_up()   # 다운로드 수 증가
    board.save()
    count = board.down    # 다운로드 수
    print('count : ', count)
    return JsonResponse({'id' : id, 'count': count})

# download
def download(request):
    id = request.GET['id']
    board = Board.objects.get(id = id)
    path = UPLOAD_DIR + board.filename
    # filename = urllib.parse.quote(board.filename)
    filename = board.filename

    with open(path, 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/octet-stream')
        response['Content-Disposition']="attachment;filename*=UTF-8''{0}".format(filename)

        return response
    
# wordcloud2
def wordcloud2(request):
    a_path = 'D:\\DJANGOWORK\\myDjango03\\data\\'
    data = json.loads(open(a_path+'4차 산업혁명.json', 'r', encoding='utf-8').read())

    dataProcess.make_wordCloud(data)
    return render(request, 'bigdata/word.html', {"img_data":'pytag_word.png'})


# map
def map(request):
    dataProcess.map()
    return render(request, 'bigdata/map.html')


# weather
def weather(request):
    last_date =Forecast.objects.values('tmef').order_by('-tmef')[:1]
    print('last_date.query :',last_date.query)
    weather = {}
    dataProcess.weather_crawing(last_date,weather)
    for i in weather:
        for j in weather[i]:
            dto = Forecast(city = i, tmef = j[0], wf = j[1], tmn=j[2], tmx=j[3])
            dto.save()

# 부산 정보만 출력
    result = Forecast.objects.filter(city='부산')

    result1 = Forecast.objects.filter(city='부산').values('wf').annotate(dcount = Count('wf')).values("dcount", "wf")
    # print('result1',result1.query)
    df = pd.DataFrame(result1)
    print('df',df)
    image_dic = dataProcess.weather_chart(result,df.wf, df.dcount)

    print('image_dic : ',image_dic)
    return render(request, 'bigdata/chart.html',
                {'img_data':image_dic})



# movie ==> 테이블에(Movie)에 insert
def movie(request):
    data = []
    dataProcess.movie_crawing(data)
    # data 들어있는 순서 : title, point, reserve
    for r in data:
        movie = Movie(title = r[0], point = r[1],reserve = r[2])
        movie.save()
    return redirect('/')


# movie_chart (daum_chart)
def movie_chart(request):
    data = []
    data = dataProcess.movie_crawing(data)
    # print(data)
    df = pd.DataFrame(data, columns=['제목','평점','예매율'])
    # print(df)
    group_title =df.groupby('제목')
    # print(group_title)

    # 제목별 그룹화 해서 평점의 평균
    group_mean = df.groupby('제목')['평점'].mean().sort_values(ascending=False).head(10)
    # print(group_mean)
    df1 = pd.DataFrame(group_mean, columns=['평점'])
    dataProcess.movie_daum_chart(df1.index, df1.평점)


    # dataProcess.movie_daum_chart()
    return render(request, 'bigdata/movie_daum.html',
                {'img_data':'movie_daum_fig.png'})


