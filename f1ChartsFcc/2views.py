from django.http import HttpResponse
from django.shortcuts import render

def home(request):
    labels = ['Monaco', 'Silverstone', 'Spa', 'Monza', 'Suzuka']
    data = [120000, 150000, 100000, 130000, 110000]
    return render(request, 'homepage.html', {
        'labels': labels,
        'data': data,
    })