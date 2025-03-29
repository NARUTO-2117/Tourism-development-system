from django.shortcuts import render
from django.http import HttpResponse

 # Create your views here.

def index(request):
    return render(request, "TourismSystem/index.html")
def attractions(request):
    return render(request, "TourismSystem/attractions.html")
def log(request):
    return render(request, "TourismSystem/log.html")
def login(request):
    return render(request, "TourismSystem/login.html")
def mine(request):
    return render(request, "TourismSystem/mine.html")