from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View

class IndexView(View):
    template_name = 'mainapp/home_page.html'

    def get(self, request):
        return render(request, self.template_name)

class AboutView(View):
    template_name = 'mainapp/about.html'

    def get(self, request):
        return render(request, self.template_name)